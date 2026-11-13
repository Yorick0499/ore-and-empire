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
    'characters_worldrelease':['id','world_id','key','released_at','snapshot'],
    'characters_eventschedule':['id','world_id','stamp'],
    'characters_regionaleventuse':['id','profile_id','event_id','request_key','created_at','snapshot'],
    'characters_worldevent':['id','world_id','key','name','description','kind','starts_at','ends_at','enabled','ore_percent','experience_percent','premium_bonus','region','activity','targets','art_key','release_key','rule_version'],
    'characters_factionsuccession':['id','race_id','details','created_at'],
    'characters_factionmembership':['id','profile_id','succession_id','faction','guild_id','historical_camp','historical_rank'],
    'characters_factionchoice':['id','membership_id','destination','original_rank','source_guild_id','target_guild_id','ore','experience','created_at'],
    'characters_factionrankprogress':['id','membership_id','tier'],
    'characters_campquest':['id','profile_id','rank_key','accepted_at','progress','promoted_at'],
    'characters_sleeperrace':['id','colony_id','khorinis_id','winner_id','state','paused','lease_owner','lease_expires_at','backup_path','backup_digest','proof','won_at','joined_at'],
    'characters_sleepersiege':['id','race_id','guild_id','maximum_health','health','attack','protection','completed_at'],
    'characters_sleeperstrike':['id','siege_id','profile_id','account_id','request_key','damage','log','created_at'],
    'characters_sleeperreward':['id','race_id','account_id','profile_id','created_at'],
    'characters_barrierevent':['id','race_id','kind','details','created_at'],
    'characters_bossattempt':['id','profile_id','boss_key','created_at','won','experience_reward','ore_reward','combat_log'],
    'characters_realmconvergence':['id','colony_id','khorinis_id','phase','paused','operator_id','lease_owner','lease_expires_at','attempts','plan','backup_path','backup_digest','snapshot'],
    'characters_convergenceevent':['id','operation_id','kind','attempt','details'],
    'characters_equipmentwork':['id','profile_id','request_key','item_id_snapshot','action','snapshot'],
    'characters_frontierprogress':['id','profile_id','unlocked','wins','last_attempt_at'],
    'characters_regionalfrontierprogress':['id','profile_id','track','unlocked','wins'],
    'characters_frontierrecord':['track','id','profile_id','request_key','depth','season','won','points','snapshot'],
    "characters_campaigncompletion":["id","profile_id","battle_id","snapshot"],
    "characters_editionconclusion":["id","world_id","operator_id","snapshot"],
    "characters_journalnotice": ["id","profile_id","key","title","destination","read_at"],
    'characters_marketevent':['id','profile_id','item_id','blueprint_id','action','price','quantity','reason'],
    'characters_craftrecipe':['id','key','name','discipline','skill','level','fee','ingredients','output_id','quantity','enabled'],
    'characters_craftrecord':['id','profile_id','recipe_id','request_key','snapshot'],
    'characters_personalchallenge':['id','profile_id','cadence','period','camp','kind','required','progress','ore','experience','premium','reputation','claimed_at'],
    'characters_campreputation':['id','profile_id','camp','value'],
    'characters_playerachievement':['id','profile_id','key','progress','completed_at','claimed_at'],
    'characters_storepurchase':['id','profile_id','product_id','request_key','price','effect','kind_snapshot'],
    'characters_adventuretemplate':['id','key','universe','name','level','duration_seconds','energy_cost','ore_reward','experience_reward','premium_reward','enabled'],
    'characters_world':['union_key','is_open','bot_personality_cycles','bot_simulated_purchases','id','name','edition','universe','rules_version','status','is_current','bot_count'],
    'characters_campraid':['cycle','rule_version','id','guild_id','day','name','maximum_health','health','attack','protection','minimum_level','completed_at'],
    'characters_campraidstrike':['id','raid_id','profile_id','request_key','damage','health_cost','mana_cost','casts','log'],
    'characters_campraidreward':['id','raid_id','profile_id','ore','experience','premium'],
    'characters_campguild':['id','world_id','camp','experience','level','treasury','training_level','supply_level','defense_level'],
    'characters_campproject':['id','guild_id','day','title','objectives','progress','experience_reward','treasury_reward','completed_at'],
    'characters_campcontribution':['id','guild_id','profile_id','project_id','source','kind','amount'],
    'characters_campsupplyuse':['id','profile_id','day','request_key','energy','health'],
    'characters_playerprofile': ['legacy_water_path','alliance_rank','visiting_world_id','action_end_time','current_energy','current_health','energy_updated_at','health_updated_at','mana_updated_at','origin_world_id','slot','name','name_key','is_draft','bot_personality','bot_session_shift','id','user_id','world_id','ore_balance','premium_balance','experience','skill_points','level','camp','guild','strength','dexterity','mana','life','magic_skill','onehand_skill','twohand_skill','bow_skill','crossbow_skill','smithing_skill','alchemy_skill','current_mana','equipment_mana','prepared_magic_id'],
    'characters_owneditem': ['id','owner_id','blueprint_id','is_market_listed','market_price','is_equipped','equipped_slot','quantity','listed_at','upgrade_level','origin','is_protected','rarity'],
    'characters_storyrun': ['id','profile_id','quest_id','status','progress','snapshot','choices','claimed_at'],
    'characters_adventurerun': ['started_at','ends_at','id','profile_id','template_id','claimed_at','ore_reward','experience_reward','premium_reward','event_names','briefing'],
    'characters_economicentry': ['id','profile_id','resource','amount','balance_after','category','reference'],
    'characters_premiumentry': ['id','profile_id','amount','balance_after','reference'],
    'characters_markettrade': ['rarity','upgrade_level','id','seller_id','buyer_id','price','blueprint_id','quantity'],
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
            if table=='characters_owneditem' and 'rarity' in available and 'rarity' not in columns and 'upgrade_level' in columns:
                rarities=dict(db.execute('SELECT id,rarity FROM characters_owneditem'))
                level_index=columns.index('upgrade_level'); id_index=columns.index('id')
                rows=[tuple(value+2*rarities[row[id_index]] if index==level_index else value for index,value in enumerate(row)) for row in rows]
            if table=='characters_storyrun' and 'snapshot' in columns:
                # Text-only narrative migrations may relabel a quest, never change its contract.
                snapshot_index=columns.index('snapshot');normalized=[]
                for row in rows:
                    values=list(row);snapshot=json.loads(values[snapshot_index])
                    for field in ('title','description','narrative_version'):snapshot.pop(field,None)
                    for goal in snapshot.get('objectives',[]):
                        goal.pop('label',None)
                        if 'options' in goal:goal['options']=sorted(goal['options'])
                    values[snapshot_index]=json.dumps(snapshot,sort_keys=True,ensure_ascii=False)
                    normalized.append(values)
                rows=normalized
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
    return sorted((p for p in root.glob('world-*') if re.fullmatch(r'world-\d{8}T\d{6}-[a-f0-9]{8}',p.name) and not p.is_symlink() and (p/'manifest.json').is_file() and ((p/'world.sqlite3').is_file() or (p/'world.pgdump').is_file())),key=lambda p:((p/'manifest.json').stat().st_mtime_ns,p.name),reverse=True)


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
        from ore_empire.database import sqlite_environment
        env=sqlite_environment(target)
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
