"""Deterministic budget stress model; not a replay of combat/market bot policies."""
from functools import lru_cache
from .adventures import ADVENTURES

DAY=86400
CHECKPOINTS=(10,30,90)


def rates():
    return [{'key':key,'seconds':seconds,'energy':energy,'ore':ore,'pd_per_second':round(xp/seconds,4),'pd_per_energy':round(xp/energy,4),'shards_per_hour':round(shards*3600/seconds,4),'shards_per_energy':round(shards/energy,4),'event_shards_per_energy':round((shards+1)/energy,4)} for key,name,text,level,seconds,energy,ore,xp,shards in ADVENTURES]


@lru_cache(maxsize=16)
def actor_budget(policy,event=False,human=False,capped=True):
    t=0;energy=100;updated=0;ore=50.0;shards=xp=level=0
    pending=None;refill_day=-1;refills=0;refill_total=0;runs=0;mines=0;training_points=0
    npc_spent=0;gear=set();result={};index=0
    def snapshot(day):
        return {'days':day,'ore':round(ore,2),'shards':shards,'experience':xp,'level':level,'adventures':runs,'mining_claims':mines,'refills':refill_total,'npc_ore_sink':npc_spent}
    while index<len(CHECKPOINTS):
        boundary=CHECKPOINTS[index]*DAY
        if t>=boundary:
            result[CHECKPOINTS[index]]=snapshot(CHECKPOINTS[index]);index+=1
            if index==len(CHECKPOINTS):break
            continue
        points=(t-updated)//60
        if energy>=100:updated=t
        elif points:
            energy=min(100,energy+points);updated+=points*60
            if energy==100:updated=t
        day=t//DAY
        if day!=refill_day:refill_day=day;refills=0
        if human:
            time=t%DAY
            if not (8*3600<=time<8*3600+1800 or 20*3600<=time<20*3600+1800):
                next_start=day*DAY+(8*3600 if time<8*3600 else 20*3600 if time<20*3600 else DAY+8*3600)
                t=min(next_start,boundary);continue
        if pending:
            end,reward_ore,reward_xp,reward_shards,is_mine=pending
            if t<end:t=min(end,boundary);continue
            ore+=reward_ore;xp+=reward_xp;shards+=reward_shards;mines+=is_mine;runs+=not is_mine;pending=None
            while xp>=250*(level+1)*(level+2):level+=1;training_points+=10
            t=min(t+5,boundary);continue
        # Fixed milestone sinks approximate equipment/training demand, not combat.
        if training_points and ore>=10:
            training_points-=1;ore-=10;npc_spent+=10;t=min(t+5,boundary);continue
        bought=False
        for milestone,price in ((3,80),(8,240),(15,500)):
            if level>=milestone and milestone not in gear and ore>=price:
                ore-=price;npc_spent+=price;gear.add(milestone);t=min(t+5,boundary);bought=True;break
        if bought:continue
        if policy=='miner':cost,duration,reward_ore,reward_xp,reward_shards=10,15,17.5*(1.25 if event else 1),0,0
        else:
            eligible=[a for a in ADVENTURES if a[3]<=level]
            a=ADVENTURES[0] if policy=='courier' else max(eligible,key=lambda a:a[7])
            cost,duration=a[5],a[4]
            reward_ore=a[6]*(1.25 if event else 1);reward_xp=int(a[7]*(1.1 if event else 1));reward_shards=a[8]+int(event)
        if energy<cost:
            if shards>=3 and (not capped or refills<5):
                shards-=3;energy=min(100,energy+25);updated=t;refills+=1;refill_total+=1;t=min(t+5,boundary)
            else:t=min(t+60,boundary)
            continue
        energy-=cost;pending=(t+duration,reward_ore,reward_xp,reward_shards,policy=='miner');t=min(t+5,boundary)
    return result


def simulation_report():
    cases=[]
    for population,bot_share in ((6,1.0),(20,0.5),(50,0.2)):
        bots=round(population*bot_share);miners=bots//3;questers=bots-miners;humans=population-bots
        for event in (False,True):
            budgets=[(questers,actor_budget('highest',event)),(miners,actor_budget('miner',event)),(humans,actor_budget('courier',event,True))]
            for day in CHECKPOINTS:
                totals={key:round(sum(n*budget[day][key] for n,budget in budgets),2) for key in ('ore','shards','experience','adventures','mining_claims','refills','npc_ore_sink')}
                cases.append({'days':day,'population':population,'bots':bots,'humans':humans,'event_stress':event,'totals':totals})
    return {'schema':1,'model':'repeatable-budget-v1','assumptions':{'bot_activity':'24h, 2/3 highest-XP eligible adventures and 1/3 mining','human_activity':'courier, two 30-minute sessions/day','events':'none or continuous +25% ore/+10% XP/+1 shard stress envelope, not calendar forecast','ore_per_mine':'deterministic mean 17.5; live game draws integer 10..25','energy':'100 cap; 1/min; refill25 for3 shards, at most5 per UTC day','sinks':'10 ore per earned learning point; one NPC milestone purchase at levels3/8/15','excluded':'combat, one-time campaign, loot liquidation, crafting, LLM policies and endogenous market prices; no claim of a full world simulation'},'quest_rates':rates(),'cases':cases,'courier_event_refill_comparison_90d':{'capped':actor_budget('courier',True)[90],'uncapped':actor_budget('courier',True,False,False)[90]},'market':'Transfers do not mint currency. Use the live ledger/trade history for turnover and prices.'}
