"""Private SQLite snapshots and restore drills. Never replaces the live database."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from uuid import uuid4

STABLE = {
    'characters_playerprofile': ['id','user_id','ore_balance','premium_balance','experience','skill_points','level','camp','guild'],
    'characters_owneditem': ['id','owner_id','blueprint_id','is_market_listed','market_price'],
    'characters_storyrun': ['id','profile_id','quest_id','status','progress','reward_snapshot','claimed_at'],
    'characters_adventurerun': ['id','profile_id','template_id','claimed_at'],
    'characters_economicentry': ['id','profile_id','resource','amount','balance_after','category','reference'],
    'characters_premiumentry': ['id','profile_id','amount','balance_after','reference'],
    'characters_markettrade': ['id','seller_id','buyer_id','price','blueprint_id'],
    'auth_user': ['id','username','password','is_superuser','is_active','is_staff'],
}


def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()


def inspect_database(path, specification=None):
    with sqlite3.connect(f'{Path(path).resolve().as_uri()}?mode=ro',uri=True) as db:
        if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok': raise ValueError('SQLite integrity check failed')
        if db.execute('PRAGMA foreign_key_check').fetchone(): raise ValueError('Foreign key check failed')
        tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        facts={}
        for table,fields in (specification or STABLE).items():
            if table not in tables:
                if specification: raise ValueError('Missing restore table: '+table)
                continue
            available={r[1] for r in db.execute(f'PRAGMA table_info({table})')}
            columns=[f for f in fields if f in available]
            if specification and columns!=fields: raise ValueError('Missing restore columns')
            rows=db.execute('SELECT '+','.join(columns)+' FROM '+table+' ORDER BY id').fetchall()
            facts[table]={'columns':columns,'count':len(rows),'digest':hashlib.sha256(json.dumps(rows,ensure_ascii=False,default=str).encode()).hexdigest()}
        return facts


def create_backup(source, root, keep=7):
    source=Path(source).resolve();root=Path(root).resolve()
    if not 1<=keep<=365: raise ValueError('keep must be 1..365')
    if not source.is_file(): raise ValueError('SQLite database does not exist')
    root.mkdir(parents=True,exist_ok=True,mode=0o700);root.chmod(0o700)
    staging=Path(tempfile.mkdtemp(prefix='.partial-',dir=root))
    try:
        target=staging/'world.sqlite3'
        with sqlite3.connect(f'{source.as_uri()}?mode=ro',uri=True) as src,sqlite3.connect(target) as dst: src.backup(dst)
        target.chmod(0o600)
        with sqlite3.connect(target) as db:
            migrations=db.execute('SELECT app,name FROM django_migrations ORDER BY app,name').fetchall()
            packs=db.execute('SELECT game,version,sha256 FROM characters_contentpack ORDER BY game,version').fetchall() if db.execute("SELECT 1 FROM sqlite_master WHERE name='characters_contentpack'").fetchone() else []
        repo=Path(__file__).resolve().parent.parent
        revision=subprocess.run(['git','rev-parse','HEAD'],cwd=repo,capture_output=True,text=True,check=False).stdout.strip()
        manifest={'schema':1,'created_at':datetime.now(timezone.utc).isoformat(),'engine':'sqlite','code_revision':revision,'database_sha256':sha(target),'migrations':migrations,'content_packs':packs,'facts':inspect_database(target)}
        (staging/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');(staging/'manifest.json').chmod(0o600)
        destination=root/('world-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid4().hex[:8]);staging.rename(destination)
        # Only complete, tool-owned backups participate in retention. No arbitrary directory deletion.
        complete=backups(root)
        for old in complete[keep:]: shutil.rmtree(old)
        return destination
    except BaseException:
        if staging.exists(): shutil.rmtree(staging)
        raise


def backups(root):
    import re
    root=Path(root)
    return sorted((p for p in root.glob('world-*') if re.fullmatch(r'world-\d{8}T\d{6}-[a-f0-9]{8}',p.name) and not p.is_symlink() and (p/'manifest.json').is_file() and (p/'world.sqlite3').is_file()),key=lambda p:(p.stat().st_mtime_ns,p.name),reverse=True)


def restore_drill(backup, target, live):
    backup=Path(backup).resolve(); target=Path(target).resolve();live=Path(live).resolve()
    if target==live or target.exists(): raise ValueError('Restore requires a new, separate database path')
    manifest=json.loads((backup/'manifest.json').read_text())
    if manifest.get('schema')!=1 or manifest.get('engine')!='sqlite': raise ValueError('Unsupported backup format')
    source=backup/'world.sqlite3'
    if sha(source)!=manifest['database_sha256']: raise ValueError('Backup checksum mismatch')
    # Never interpret column names from an untrusted manifest as SQL.
    spec={table:fact['columns'] for table,fact in manifest['facts'].items()}
    if any(table not in STABLE or any(field not in STABLE[table] for field in fields) for table,fields in spec.items()): raise ValueError('Invalid validation specification')
    if inspect_database(source,spec)!=manifest['facts']: raise ValueError('Backup facts mismatch')
    target.parent.mkdir(parents=True,exist_ok=True)
    try:
        with open(target,'xb') as dst,open(source,'rb') as src: os.chmod(target,0o600);shutil.copyfileobj(src,dst)
        repo=Path(__file__).resolve().parent.parent
        env={**os.environ,'ORE_DATABASE_PATH':str(target)}
        process=subprocess.run([sys.executable,str(repo/'manage.py'),'migrate','--noinput'],cwd=repo,env=env,capture_output=True,text=True)
        if process.returncode: raise ValueError('Restore migration failed; original backup remains untouched')
        if inspect_database(target,spec)!=manifest['facts']: raise ValueError('Restored progression/ledger differs from snapshot')
        proof={'schema':1,'verified_at':datetime.now(timezone.utc).isoformat(),'database_sha256':sha(target),'migration_applied':True,'tables':len(spec)}
        temporary=backup/'.verification.tmp';temporary.write_text(json.dumps(proof,indent=2)+'\n');temporary.chmod(0o600);temporary.replace(backup/'verification.json')
        return proof
    except BaseException:
        target.unlink(missing_ok=True)
        raise


def backup_status(root):
    entries=backups(root)
    if not entries:return None
    latest=entries[0];manifest=json.loads((latest/'manifest.json').read_text())
    proof=json.loads((latest/'verification.json').read_text()) if (latest/'verification.json').exists() else None
    return {'name':latest.name,'created_at':manifest['created_at'],'revision':manifest['code_revision'][:12],'verified_at':proof['verified_at'] if proof else None,'count':len(entries)}
