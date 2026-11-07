"""Explicit database selection; an isolated SQLite subprocess never inherits PG."""
import os
from urllib.parse import urlsplit,unquote,parse_qs
from django.core.exceptions import ImproperlyConfigured


def database_config(env,base):
    url=env.get('DATABASE_URL','')
    engine=env.get('ORE_DATABASE_ENGINE','sqlite')
    if url:
        parsed=urlsplit(url)
        if parsed.scheme not in {'postgres','postgresql'}:raise ImproperlyConfigured('DATABASE_URL must select PostgreSQL')
        query=parse_qs(parsed.query)
        if set(query)-{'sslmode'}:raise ImproperlyConfigured('Unsupported database URL option')
        config={'ENGINE':'django.db.backends.postgresql','NAME':unquote(parsed.path.lstrip('/')),'USER':unquote(parsed.username or ''),'PASSWORD':unquote(parsed.password or ''),'HOST':parsed.hostname or env.get('PGHOST',''),'PORT':parsed.port or 5432}
        sslmode=query.get('sslmode',[None])[0]
        if sslmode:config['OPTIONS']={'sslmode':sslmode}
    elif engine=='postgresql':
        config={'ENGINE':'django.db.backends.postgresql','NAME':env.get('PGDATABASE','ore_world'),'USER':env.get('PGUSER','ore_user'),'PASSWORD':env.get('PGPASSWORD',''),'HOST':env.get('PGHOST','127.0.0.1'),'PORT':env.get('PGPORT','5432')}
        if env.get('PGSSLMODE'):config['OPTIONS']={'sslmode':env['PGSSLMODE']}
    elif engine=='sqlite':
        return {'ENGINE':'django.db.backends.sqlite3','NAME':env.get('ORE_DATABASE_PATH',base/'db.sqlite3'),'OPTIONS':{'timeout':20}}
    else:raise ImproperlyConfigured('Unsupported ORE_DATABASE_ENGINE')
    if not config['NAME']:raise ImproperlyConfigured('PostgreSQL database name is required')
    config['CONN_MAX_AGE']=60
    config['CONN_HEALTH_CHECKS']=True
    config.setdefault('OPTIONS',{}).update(connect_timeout=5,options='-c lock_timeout=5000 -c statement_timeout=30000')
    return config


def sqlite_environment(path):
    env={**os.environ,'ORE_DATABASE_ENGINE':'sqlite','ORE_DATABASE_PATH':str(path)}
    env.pop('DATABASE_URL',None)
    return env
