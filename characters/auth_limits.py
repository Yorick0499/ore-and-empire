"""Shared database-backed login limits. Never store raw IPs, logins or passwords."""
import hashlib,hmac,ipaddress
from datetime import timedelta
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from .models import AuthRateBucket

def client_address(request):
    try:remote=ipaddress.ip_address(request.META.get('REMOTE_ADDR',''))
    except ValueError:return 'unknown'
    networks=[ipaddress.ip_network(c) for c in settings.TRUSTED_PROXY_CIDRS]
    trusted=lambda ip:any(ip in network for network in networks)
    if not trusted(remote):return str(remote)
    try:chain=[ipaddress.ip_address(v.strip()) for v in request.META.get('HTTP_X_FORWARDED_FOR','').split(',') if v.strip()]+[remote]
    except ValueError:return str(remote)
    while len(chain)>1 and trusted(chain[-1]):chain.pop()
    return str(chain[-1])

def bucket_key(scope,value):return hmac.new(settings.SECRET_KEY.encode(),(scope+':'+value).encode(),hashlib.sha256).hexdigest()

@transaction.atomic
def consume(scope,value,limit,window):
    now=timezone.now();key=bucket_key(scope,value)
    row,_=AuthRateBucket.objects.get_or_create(key=key)
    row=AuthRateBucket.objects.select_for_update().get(pk=row.pk)
    end=row.window_started+timedelta(seconds=window)
    if now>=end:row.window_started=now;row.attempts=0;end=now+timedelta(seconds=window)
    if row.attempts>=limit:return max(1,int((end-now).total_seconds())+1)
    row.attempts+=1;row.save(update_fields=['window_started','attempts'])
    return 0

class AuthRateLimitMiddleware(MiddlewareMixin):
    def process_view(self,request,view_func,view_args,view_kwargs):
        if request.method!='POST' or not request.resolver_match:return None
        name=request.resolver_match.view_name
        if name not in {'login','admin:login','register'}:return None
        rules=settings.AUTH_RATE_LIMITS;address=client_address(request)
        scopes=[('ip',address,rules['ip'])]
        if name=='register':scopes.append(('register',address,rules['register']))
        else:scopes.append(('login',address+':'+request.POST.get('username','')[:150].casefold(),rules['login']))
        for scope,value,limit in scopes:
            wait=consume(scope,value,limit,rules['window'])
            if wait:
                response=HttpResponse('Zbyt wiele prób. Spróbuj ponownie później.',status=429,content_type='text/plain; charset=utf-8');response['Retry-After']=str(wait);return response
        if name!='register':request._auth_limit_key=bucket_key('login',scopes[-1][1])
    def process_response(self,request,response):
        if getattr(request,'_auth_limit_key',None) and 300<=response.status_code<400 and getattr(request,'user',None) and request.user.is_authenticated:
            AuthRateBucket.objects.filter(key=request._auth_limit_key).delete()
        return response
