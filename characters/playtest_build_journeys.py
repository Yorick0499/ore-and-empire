"""Opt-in earned build/faction matrix. Global Barrier victory is external here.

Actual verified community activation has its separate simulate_journey rehearsal.
No character levels, wallets, items, memberships or milestones are granted.
"""
import sys
from datetime import timedelta
from io import StringIO
from uuid import uuid4
from django.core.management import call_command
from django.test import TestCase
from . import game_logic as game
from .models import ItemBluePrint,World,StoryQuest
from .barrier import region,source_games,travel
from .equipment import allowed
from .camp_progression import BY_RANK,available_rank,accept_camp_quest,promote_in_camp
from .faction_advancement import RANKS,current_tier
from .locations import LOCATIONS,BY_KEY
from .playtest_pacing import CampaignPacingTests
from .playtest_gothic2 import EarnedNkCampaign
from .release_probe import record_scenario

CASES={
 'old-warrior':('GOTHIC_I','OLD_CAMP','warrior',('DIGGER','SHADOW','GUARD','BARON'),'BANDITS'),
 'new-archer':('GOTHIC_I','NEW_CAMP','archer',('MOLE','ROGUE','MERC','ELITE_MERC'),'MERCENARIES'),
 'old-fire':('GOTHIC_I','OLD_CAMP','fire',('DIGGER','SHADOW','FIRE_MAGE','ARCH_FIRE'),'FIRE_ORDER'),
 'new-water':('GOTHIC_I','NEW_CAMP','water',('MOLE','ROGUE','WATER_MAGE','ARCH_WATER'),'WATER_CIRCLE'),
 'city-warrior':('GOTHIC_II','CITY_WATCH','warrior',('K2_CITIZEN','K2_MILITIA','K2_PALADIN','K2_COMMANDER'),'CITY_WATCH'),
 'monastery-fire':('GOTHIC_II','FIRE_ORDER','fire',('K2_NOVICE','K2_ADEPT','K2_MAGE','K2_ARCHMAGE'),'FIRE_ORDER'),
 'onar-archer':('GOTHIC_II','ONAR_MERCS','archer',('K2_LABORER','K2_RECRUIT','K2_MERC','K2_CAPTAIN'),'MERCENARIES'),
 'swamp-guru':('GOTHIC_I','SWAMP_CAMP','water',('PICKER','NOVICE','GURU','ARCH_GURU'),'WATER_CIRCLE'),
 'swamp-templar':('GOTHIC_I','SWAMP_CAMP','warrior',('PICKER','NOVICE','SWAMP_GUARD','TEMPLAR'),'CITY_WATCH'),
}

class EarnedBuild:
    def __init__(self,kind):self.kind=kind
    def train(self,test,p,steps,attribute,amount):
        while amount>0:
            n=min(10,amount,p.skill_points)
            test.assertGreater(n,0,(attribute,amount,p.level))
            steps['funds'](p.training_cost*n)
            test.assertTrue(steps['do']('build_train_'+attribute,lambda:game.train_attribute(p,attribute,n)))
            amount-=n
    def prepare(self,test,p,steps,target=None):
        from .magic import learn_circle,circle_cap,BY_CODE,purchase_magic,prepare_magic
        magic=self.kind in {'fire','water'}
        # Reserve earned points for promotion training objectives rather than
        # spending every point before accepting the quest.
        if magic:
            while p.magic_skill<circle_cap(p) and p.level>=2*(p.magic_skill+1) and p.skill_points>=5*(p.magic_skill+1)+10:
                steps['funds'](50*(p.magic_skill+1));test.assertTrue(steps['do']('build_circle',lambda:learn_circle(p)))
        reserve=10+5*(p.magic_skill+1) if magic and p.magic_skill<circle_cap(p) else 10
        minimum=50 if self.kind=='archer' else 25 if magic else 10
        if p.strength<minimum and p.skill_points>reserve:self.train(test,p,steps,'strength',min(minimum-p.strength,p.skill_points-reserve))
        attr='mana' if magic else 'dexterity' if self.kind=='archer' else 'strength'
        if not magic:
            skill='bow_skill' if self.kind=='archer' else 'onehand_skill'
            if getattr(p,skill)<min(60,p.level*2) and p.skill_points>10:self.train(test,p,steps,skill,min(min(60,p.level*2)-getattr(p,skill),p.skill_points-10))
        if p.skill_points>reserve:self.train(test,p,steps,attr,p.skill_points-reserve)
        kind='bow' if self.kind=='archer' else 'onehand'
        choices=ItemBluePrint.objects.filter(source_game__in=source_games(p),merchant=True,kind='weapon',weapon_type=kind,required_strength__lte=p.strength,required_dexterity__lte=p.dexterity,base_value__lte=max(100,p.level*80)).order_by('-damage','base_value','pk')
        bp=next((b for b in choices if allowed(p,b)),None)
        if bp:
            equipped=p.inventory.filter(is_equipped=True,equipped_slot='weapon').first()
            if not equipped or equipped.effective_stats['damage']<bp.damage:
                owned=p.inventory.filter(blueprint=bp,is_market_listed=False).first()
                if not owned:steps['funds'](bp.base_value);test.assertTrue(steps['do']('build_buy_weapon',lambda:game.buy_item_from_npc(p,bp)));owned=p.inventory.get(blueprint=bp)
                test.assertTrue(steps['do']('build_equip_weapon',lambda:game.equip_item(p,owned)))
        # Buy ordinary protective jewelry; no free fixture armor/health.
        def value(item):
            return item.weapon_prot*3+item.fire_prot+item.magic_prot+item.life_bonus/5+item.mana_bonus/5
        for slot,kind in [('ring1','ring'),('ring2','ring'),('amulet','amulet'),('belt','belt')]:
            rows=ItemBluePrint.objects.filter(source_game__in=source_games(p),merchant=True,kind=kind,base_value__lte=max(100,p.level*80),required_strength__lte=p.strength,required_dexterity__lte=p.dexterity)
            bp=max((b for b in rows if allowed(p,b)),key=lambda b:(value(b),-b.base_value),default=None)
            worn=p.inventory.filter(is_equipped=True,equipped_slot=slot).select_related('blueprint').first()
            if bp and value(bp)>0 and (not worn or value(bp)>value(worn.blueprint)):
                owned=p.inventory.filter(blueprint=bp,is_equipped=False,is_market_listed=False).first()
                if not owned:
                    steps['funds'](bp.base_value);test.assertTrue(steps['do']('build_buy_protection',lambda:game.buy_item_from_npc(p,bp)))
                    owned=p.inventory.filter(blueprint=bp,is_equipped=False).first()
                test.assertTrue(steps['do']('build_equip_protection',lambda:game.equip_item(p,owned,slot)))
        if self.kind=='archer':
            ammo=ItemBluePrint.objects.filter(source_game__in=source_games(p),merchant=True,kind='ammo',original_stats__ammo_type='arrow').order_by('base_value','pk').first()
            if ammo and sum(p.inventory.filter(blueprint=ammo,is_market_listed=False).values_list('quantity',flat=True))<10:
                steps['funds'](ammo.base_value*30);test.assertTrue(steps['do']('build_ammo',lambda:game.buy_item_from_npc(p,ammo,30)))
        if magic and p.magic_skill:
            from .magic import rune_allowed
            from .bestiary import BESTIARY
            monster=game.BOSSES[target].monster if target in game.BOSSES else BESTIARY.get(target,{})
            candidates=[]
            for b in ItemBluePrint.objects.filter(source_game__in=source_games(p),catalog_key__in=BY_CODE):
                spell,scroll=BY_CODE[b.catalog_key]
                if allowed(p,b) and (scroll or rune_allowed(p,spell)):
                    damage=max(1,spell.damage-monster.get(spell.damage_type+'_prot',0))
                    # Prefer sustainable runes; a bought opposite-element scroll
                    # is a deliberate option when own-school damage is resisted.
                    score=damage if not scroll else damage//10
                    candidates.append((score,not scroll,-b.base_value,b))
            if candidates:
                own=max((score for score,rune,_,_ in candidates if rune),default=0)
                if target and own<=15:
                    candidates=[((max(1,BY_CODE[b.catalog_key][0].damage-monster.get(BY_CODE[b.catalog_key][0].damage_type+'_prot',0)) if not rune else score),rune,price,b) for score,rune,price,b in candidates]
                b=max(candidates,key=lambda x:x[:3])[3];spell,scroll=BY_CODE[b.catalog_key]
                count=min(40,max(1,(monster.get('life',200)+max(1,spell.damage-monster.get(spell.damage_type+'_prot',0))-1)//max(1,spell.damage-monster.get(spell.damage_type+'_prot',0))+2)) if scroll else 1
                if target and not scroll:
                    needed=((monster.get('life',0)+max(1,spell.damage-monster.get(spell.damage_type+'_prot',0))-1)//max(1,spell.damage-monster.get(spell.damage_type+'_prot',0))+2)*spell.cost
                    for _ in range(100):
                        if p.max_mana>=needed:break
                        if p.skill_points<=reserve:
                            steps['grind_level']();p.refresh_from_db()
                            if p.magic_skill<circle_cap(p) and p.skill_points>=5*(p.magic_skill+1)+10:
                                return self.prepare(test,p,steps,target)
                        if p.skill_points>reserve:self.train(test,p,steps,'mana',min(needed-p.max_mana,p.skill_points-reserve))
                    test.assertGreaterEqual(p.max_mana,needed,(target,spell.key))

                stock=p.inventory.filter(blueprint=b,is_market_listed=False)
                owned=stock.first();quantity=sum(stock.values_list('quantity',flat=True)) if scroll else (owned.quantity if owned else 0)
                if quantity<count:
                    amount=count-quantity;steps['funds'](b.base_value*amount);test.assertTrue(steps['do']('build_buy_magic',lambda:purchase_magic(p,b.pk)))
                    # purchase_magic buys one; repeated buys use the same service.
                    for _ in range(amount-1):test.assertTrue(steps['do']('build_buy_magic',lambda:purchase_magic(p,b.pk)))
                    owned=p.inventory.filter(blueprint=b,is_market_listed=False).first()
                test.assertTrue(steps['do']('build_prepare_magic',lambda:prepare_magic(p,owned.pk)))

class EarnedBuildJourneys(TestCase):
    play=CampaignPacingTests.play
    expedition=EarnedNkCampaign.expedition
    def run_case(self,key):
        self.case=key;self.universe,self.camp,self.build,self.path,self.destination=CASES[key];self.checkpoints=[]
        self.play(self.universe,None,support=True,income_first=True,camp=self.camp,build_strategy=EarnedBuild(self.build),on_checkpoint=self.native_ranks,after_campaign=self.finish,actor_name='b-'+key)
    def native_ranks(self,p,steps):
        for key in self.path:
            rank=BY_RANK[key]
            if p.camp_quests.filter(rank_key=key,promoted_at__isnull=False).exists():continue
            if p.level<rank.level or not available_rank(p,rank):break
            self.earn_rank(p,rank,steps)
    def earn_rank(self,p,rank,steps):
        do,prepare,advance=steps['do'],steps['prepare'],steps['advance']
        while p.level<rank.level:steps['grind_level']();p.refresh_from_db()
        self.assertTrue(do('matrix_rank_accept',lambda:accept_camp_quest(p,rank.key)),(self.case,rank.key,p.guild))
        for goal in rank.objectives:
            kind,_,target=goal.event.partition(':')
            quest=p.camp_quests.get(rank_key=rank.key,promoted_at__isnull=True)
            for _ in range(max(0,goal.count-quest.progress.get(goal.event,0))):
                if kind=='train':
                    if not p.skill_points:steps['grind_level']()
                    steps['funds'](p.training_cost);self.assertTrue(do('matrix_train_goal',lambda:game.train_attribute(p,target)))
                elif kind=='mine':
                    self.assertTrue(do('matrix_mine',lambda:game.start_mining(p,15)));advance(max(0,int((p.action_end_time-steps['now']()).total_seconds())),'timer');self.assertTrue(do('matrix_mine_claim',lambda:game.claim_ore_reward(p)))
                else:
                    prepare(target)
                    if kind=='hunt':
                        location=next(l for l in LOCATIONS if target in l.monsters);self.route(p,location);self.assertTrue(location.accessible(p))
                        self.assertTrue(do('matrix_hunt',lambda:game.execute_hunt(p,target,location.key)));self.assertTrue(p.battles.first().won,(self.case,rank.key,target))
                    elif kind=='boss':
                        loc=BY_KEY[target];self.route(p,loc)
                        last=p.boss_attempts.filter(boss_key=target).first()
                        if last:
                            remaining=(last.created_at+timedelta(minutes=game.BOSSES[target].cooldown_minutes)-steps['now']()).total_seconds()
                            if remaining>0:advance(int(remaining)+1,'timer')
                        result=do('matrix_boss',lambda:game.execute_boss(p,target));self.assertTrue(result.won,(self.case,rank.key,target,result.combat_log))
                    else:self.fail(kind)
        attribute=rank.attribute
        while getattr(p,attribute)<rank.attribute_value:
            if not p.skill_points:steps['grind_level']();p.refresh_from_db()
            steps['funds'](p.training_cost)
            train='dexterity' if attribute=='martial' and self.build=='archer' else 'strength' if attribute=='martial' else attribute
            self.assertTrue(do('matrix_rank_attribute',lambda:game.train_attribute(p,train)))
        steps['funds'](rank.cost);self.assertTrue(do('matrix_rank_promote',lambda:promote_in_camp(p,rank.key)))
        print(self.case,rank.key,p.level,file=sys.stderr,flush=True)
        self.checkpoints.append({'rank':rank.name,'ordinal':rank.tier+1,'level':p.level,'world_hours':round((steps['now']()-steps['start']).total_seconds()/3600,2),'ore':p.ore_balance})
    def route(self,p,loc):
        if region(p).universe!=loc.universe:self.assertTrue(travel(p,(World.objects.get(is_current=True) if loc.universe=='GOTHIC_I' else World.objects.get(universe='GOTHIC_II',is_open=True)).pk))
    def join_worlds(self,p,steps):
        # This matrix observes the external community event. No personal state
        # is granted; the fully earned activation is checked by simulate_journey.
        self.native_ranks(p,steps)
        for key in self.path:
            if not p.camp_quests.filter(rank_key=key,promoted_at__isnull=False).exists():self.earn_rank(p,BY_RANK[key],steps)
        c,i=EarnedNkCampaign.join_worlds(self,p,steps)
        p.refresh_from_db()
        from .faction_choice import choose
        from .factions import membership
        if membership(p).faction=='PENDING':self.assertTrue(choose(p,self.destination))
        self.assertEqual(membership(p).faction,self.destination)
        return c,i
    def finish(self,p,steps):
        self.expedition(p,steps)
        # Advanced quests take the player back to the Valley and then to dragons.
        for rank in RANKS:
            if rank.camp!=self.destination:continue
            self.assertTrue(travel(p,World.objects.get(is_current=True).pk))
            self.earn_rank(p,rank,steps)
        self.assertEqual(current_tier(p),7)
        from .frontier import patrol
        from .regional_endgame import TRACKS
        for track in TRACKS:
            self.assertTrue(travel(p,(World.objects.get(is_current=True) if track=='valley' else World.objects.get(universe='GOTHIC_II',is_open=True)).pk))
            steps['prepare']();steps['advance'](301,'timer');row=steps['do']('matrix_regional',lambda:patrol(p,1,uuid4(),track));self.assertTrue(row.won,(self.case,track,row.snapshot))
        self.assertEqual(p.battles.filter(won=False).count(),0)
        casts=p.battles.filter(combat_details__casts__gt=0).count()
        if self.build in {'fire','water'}:self.assertGreater(casts,20)
        if self.build=='archer':self.assertEqual(p.inventory.get(is_equipped=True,equipped_slot='weapon').blueprint.weapon_type,'bow')
        record_scenario('earned-build-faction-journey',{'case':self.case,'build':self.build,'start_universe':self.universe,'native_camp':self.camp,'faction':self.destination,'rank_ordinal':8,'level':p.level,'strength':p.strength,'dexterity':p.dexterity,'mana':p.mana,'magic_circle':p.magic_skill,'magical_battles':casts,'ore':p.ore_balance,'world_days':round((steps['now']()-steps['start']).total_seconds()/86400,2),'checkpoints':self.checkpoints,'earned_personal_progression':True,'external_global_barrier_event':True,'limits':['Ordinary earned character; global community victory is an external fixture.','Knowledgeable strategy and virtual recovery, no competing player market or PvP.','First regional depths, not all400 or a long-lived economy.']})

for _key in CASES:
    def _test(self,key=_key):self.run_case(key)
    setattr(EarnedBuildJourneys,'test_'+_key.replace('-','_'),_test)
