"""Small isolated HTTP process. No Django, ORM, inherited credentials or tools."""
import json,sys,urllib.request

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):raise ValueError("Model endpoint redirects are forbidden")

def main():
    config=json.loads(sys.stdin.buffer.read(16385))
    payload={'model':config['model'],'messages':[{'role':'system','content':'Choose one allowed action index for a Gothic browser game resident. Keep resources useful; follow the numeric schema. No tools, code or extra fields.'},{'role':'user','content':json.dumps(config['prompt'],ensure_ascii=False,separators=(',',':'))}],'format':{'type':'object','properties':{'choice':{'type':'integer','enum':list(range(len(config['prompt']['choices'])))}},'required':['choice'],'additionalProperties':False},'stream':False,'keep_alive':'5m','options':{'temperature':0,'num_predict':config['max_output'],'num_ctx':4096,'num_thread':2,'num_gpu':0}}
    request=urllib.request.Request(config['endpoint'],data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    with opener.open(request,timeout=config['timeout']) as response:raw=response.read(4097)
    if len(raw)>4096:raise ValueError('Oversized model response')
    result=json.loads(raw);content=json.loads(result['message']['content'])
    if set(content)!={'choice'}:raise ValueError('Unexpected output fields')
    print(json.dumps({'choice':content['choice'],'prompt_tokens':result.get('prompt_eval_count',0),'generated_tokens':result.get('eval_count',0)}))

if __name__=='__main__':
    try:main()
    except Exception:sys.exit(2)
