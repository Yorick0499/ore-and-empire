"""Fail-closed settings for a separate, explicitly configured installation."""
from urllib.parse import urlsplit
from django.core.exceptions import ImproperlyConfigured

def production_settings(env,database):
    key=env.get('SECRET_KEY','')
    hosts=[h.strip() for h in env.get('ALLOWED_HOSTS','').split(',') if h.strip()]
    origins=[v.strip() for v in env.get('CSRF_TRUSTED_ORIGINS','').split(',') if v.strip()]
    if env.get('DEBUG','False')!='False' or len(key)<50 or len(set(key))<5:raise ImproperlyConfigured('Production requires DEBUG=False and a private strong SECRET_KEY')
    if not hosts or any('*' in h or '/' in h for h in hosts):raise ImproperlyConfigured('Production requires explicit ALLOWED_HOSTS')
    if not origins or any(urlsplit(v).scheme!='https' or urlsplit(v).hostname not in [h.strip('[]') for h in hosts] or urlsplit(v).username or urlsplit(v).path not in {'','/'} or urlsplit(v).query or urlsplit(v).fragment for v in origins):raise ImproperlyConfigured('Production requires explicit matching HTTPS CSRF_TRUSTED_ORIGINS')
    if database['ENGINE']!='django.db.backends.postgresql':raise ImproperlyConfigured('Production requires PostgreSQL')
    return dict(ALLOWED_HOSTS=hosts,CSRF_TRUSTED_ORIGINS=origins,DEBUG=False,SESSION_COOKIE_SECURE=True,CSRF_COOKIE_SECURE=True,SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax',CSRF_COOKIE_SAMESITE='Lax',SECURE_SSL_REDIRECT=True,SECURE_REDIRECT_EXEMPT=[r'^health/live/$',r'^health/ready/$'],SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO','https'),SECURE_HSTS_SECONDS=int(env.get('ORE_HSTS_SECONDS','3600')),SECURE_HSTS_INCLUDE_SUBDOMAINS=True,SECURE_HSTS_PRELOAD=True,X_FRAME_OPTIONS='DENY',SECURE_CONTENT_TYPE_NOSNIFF=True,SECURE_REFERRER_POLICY='same-origin')
