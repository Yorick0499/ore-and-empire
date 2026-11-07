import os
bind=os.environ.get('ORE_BIND','127.0.0.1:8010')
workers=int(os.environ.get('ORE_WEB_WORKERS','2'))
threads=2
worker_class='gthread'
timeout=30
graceful_timeout=30
keepalive=5
accesslog='-'
errorlog='-'
forwarded_allow_ips=os.environ.get('ORE_FORWARDED_ALLOW_IPS','127.0.0.1,::1')

control_socket_disable=True
