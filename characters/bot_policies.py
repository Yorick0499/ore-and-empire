"""Opt-in local model experiment. Rules remain the default and execution authority."""
import hashlib,json,math,os,re,subprocess,sys,time
from dataclasses import asdict,fields
from datetime import timedelta
from urllib.parse import urlsplit
from django.conf import settings
from django.utils import timezone
from .bots import Observation,BaselinePolicyV18

# Frozen protocol: future Observation fields do not alter version-one prompts/replay.
POLICY_FIELDS = ('energy','ore','busy','reward_ready','offer_id','inventory_id','blueprint_id','equip_id','armed','role','skill_points','strength','health','max_health','premium','turn','camp','camp_target','rank_target','rank_action','needs_ore','training','training_needed','quest_mine','quest_hunt','boss_key','hunt_key','hunt_location','adventure_id','adventure_ready','template_id','product_id','product_urgent','upgrade_action','upgrade_id','upgrade_cost','upgrade_gain','ore_reserve','disposal_id','story_action','story_target','story_recover','consume_id','experience','magic_action','magic_target','mana','magic_ready','magic_focused','camp_action','camp_target_id','camp_upgrade_level','raid_action','raid_target','personal_action','personal_target','craft_action','craft_target','market_action','market_target','market_price','forge_action','forge_target','forge_level','patrol_depth','ammo_id','ammo_blocked')

def candidates(obs):
    baseline=BaselinePolicyV18().choose(obs);result=[baseline]
    # Critical progression, rewards, recovery, combat preparation and trades remain rule-controlled.
    if baseline[0] not in {'mine','hunt','adventure'} or obs.busy or obs.story_action or obs.story_recover or obs.boss_key or obs.needs_ore:return result
    if obs.energy>=10:result.append(('mine',None))
    if obs.armed and obs.hunt_key and obs.energy>=15 and obs.health>=max(10,obs.max_health//2):result.append(('hunt',None))
    if obs.template_id and obs.energy>=15:result.append(('adventure',obs.template_id))
    return list(dict.fromkeys(result))

def prompt(obs,choices):return {'version':1,'state':{key:getattr(obs,key) for key in POLICY_FIELDS},'choices':[{'action':a,'target':t} for a,t in choices]}
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

class Budget:
    def __init__(self,calls,tokens,milliseconds,guard=None,clock=time.monotonic):
        self.maximum=(calls,tokens,milliseconds);self.guard=guard;self.clock=clock;self.started=clock();self.used=[0,0,0];self.blocked_until=0
    def reserve(self,tokens,milliseconds):
        if self.guard:
            from .models import BotPolicyBudget
            with self.guard.work():
                row,_=BotPolicyBudget.objects.get_or_create(world_id=self.guard.world_id)
                now=timezone.now()
                if now-row.window_started>=timedelta(hours=1):row.window_started=now;row.calls=0;row.tokens_reserved=0;row.milliseconds_reserved=0;row.blocked_until=None
                values=(row.calls+1,row.tokens_reserved+tokens,row.milliseconds_reserved+milliseconds)
                if (row.blocked_until and row.blocked_until>now) or any(a>b for a,b in zip(values,self.maximum)):return False
                row.calls,row.tokens_reserved,row.milliseconds_reserved=values;row.save();return True
        now=self.clock()
        if now-self.started>=3600:self.started=now;self.used=[0,0,0];self.blocked_until=0
        values=[self.used[0]+1,self.used[1]+tokens,self.used[2]+milliseconds]
        if now<self.blocked_until or any(a>b for a,b in zip(values,self.maximum)):return False
        self.used=values;return True
    def cooldown(self):
        if self.guard:
            from .models import BotPolicyBudget
            with self.guard.work():BotPolicyBudget.objects.filter(world_id=self.guard.world_id).update(blocked_until=timezone.now()+timedelta(seconds=60))
        else:self.blocked_until=self.clock()+60

class OllamaPolicy:
    version='ollama-1'
    def __init__(self,model,endpoint='http://127.0.0.1:11434/api/chat',timeout=2,max_calls=20,max_tokens=50000,max_seconds=60,max_output=48,guard=None):
        parsed=urlsplit(endpoint)
        if parsed.scheme not in {'http','https'} or parsed.hostname not in {'127.0.0.1','localhost','::1'} or parsed.path!='/api/chat' or parsed.username or parsed.password or parsed.query or parsed.fragment:raise ValueError('Only an explicitly local Ollama chat endpoint is supported')
        if not re.fullmatch(r'[A-Za-z0-9_.:/-]{1,100}',model) or 'cloud' in model.casefold():raise ValueError('An explicit local model is required; cloud tags are disabled')
        if not .1<=timeout<=10 or not 0<=max_calls<=1000 or not 0<=max_tokens<=5000000 or not 0<=max_seconds<=600 or not 8<=max_output<=128:raise ValueError('Invalid local policy budget')
        self.model=model;self.endpoint=endpoint;self.timeout=timeout;self.max_output=max_output;self.budget=Budget(max_calls,max_tokens,math.ceil(max_seconds*1000),guard);self.last_details={}
    def choose(self,obs):
        choices=candidates(obs);payload=prompt(obs,choices)
        info={'version':1,'model':self.model,'candidates':[[a,t] for a,t in choices],'choice':0,'prompt_sha256':digest(payload),'status':'forced-rules','latency_ms':0,'prompt_tokens':0,'generated_tokens':0}
        self.last_details=info
        if len(choices)<2:return choices[0]
        reservation=4096+self.max_output
        if not self.budget.reserve(reservation,math.ceil(self.timeout*1000)):info['status']='budget-or-cooldown';return choices[0]
        config={'model':self.model,'endpoint':self.endpoint,'timeout':self.timeout,'max_output':self.max_output,'prompt':payload}
        raw=json.dumps(config,ensure_ascii=False).encode()
        if len(raw)>8192:info['status']='oversized-observation';return choices[0]
        started=time.monotonic()
        try:
            # A separate, credential-free process gives a hard overall deadline, including DNS/headers.
            env={k:os.environ[k] for k in ('PATH','LANG','SSL_CERT_FILE','SSL_CERT_DIR') if k in os.environ}
            proc=subprocess.run([sys.executable,'-m','characters.local_model_transport'],input=raw,capture_output=True,timeout=self.timeout,cwd=settings.BASE_DIR,env=env)
            if proc.returncode or len(proc.stdout)>4096:raise ValueError('Transport failed')
            result=json.loads(proc.stdout);index=result['choice']
            if type(index)is not int or not 0<=index<len(choices):raise ValueError('Action outside allowlist')
            if type(result['prompt_tokens'])is not int or not 0<=result['prompt_tokens']<=4096 or type(result['generated_tokens'])is not int or not 0<=result['generated_tokens']<=self.max_output:raise ValueError('Invalid token counts')
            info.update(choice=index,status='accepted',prompt_tokens=result['prompt_tokens'],generated_tokens=result['generated_tokens'])
        except (OSError,ValueError,TypeError,KeyError,subprocess.TimeoutExpired):
            info['status']='fallback';self.budget.cooldown()
        finally:info['latency_ms']=round((time.monotonic()-started)*1000,2)
        return choices[info['choice']]

def configured_policy(guard):
    kind=os.environ.get('ORE_BOT_POLICY','rules')
    if kind=='rules':return None
    if kind!='ollama':raise ValueError('Unknown ORE_BOT_POLICY')
    return OllamaPolicy(model=os.environ.get('ORE_LLM_MODEL',''),endpoint=os.environ.get('ORE_LLM_ENDPOINT','http://127.0.0.1:11434/api/chat'),timeout=float(os.environ.get('ORE_LLM_TIMEOUT','2')),max_calls=int(os.environ.get('ORE_LLM_MAX_CALLS','20')),max_tokens=int(os.environ.get('ORE_LLM_MAX_TOKENS','50000')),max_seconds=float(os.environ.get('ORE_LLM_MAX_SECONDS','60')),guard=guard)

def replay(decision):
    try:
        obs=Observation(**{k:v for k,v in decision.observation.items() if k in {f.name for f in fields(Observation)}})
        saved=decision.policy_snapshot;choices=candidates(obs);index=saved['choice']
        if saved.get('version')!=1 or saved['candidates']!=[[a,t] for a,t in choices] or type(index)is not int or not 0<=index<len(choices) or saved['prompt_sha256']!=digest(prompt(obs,choices)):raise ValueError('Invalid replay proof')
        action,target=choices[index]
        return {'supported':True,'action':action,'target':target,'matches':(action,target)==(decision.action,decision.target_id),'model_requeried':False}
    except (KeyError,TypeError,ValueError):return {'supported':False,'reason':'Invalid local-policy snapshot'}
