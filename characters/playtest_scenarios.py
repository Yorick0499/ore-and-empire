"""Opt-in ordinary-player simulation; deliberately outside automatic test discovery."""
from collections import Counter
from datetime import timedelta
from io import StringIO
import random
from unittest.mock import patch
from uuid import uuid4
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase, Client
from django.utils import timezone
from . import game_logic as game
from .models import PlayerProfile, ItemBluePrint, AdventureTemplate, BotDecision
from .world_management import seed_clean_world
from .combat_preparation import hunt_preparation
from .locations import LOCATIONS
from .bestiary import BESTIARY
from .release_probe import record_scenario


class OrdinaryBuildSession(TestCase):
    def test_three_earned_builds_in_shared_world(self):
        self.run_session(income_first=False)

    def test_income_first_builds_can_finance_their_gear_and_magic(self):
        self.run_session(income_first=True)

    def run_session(self, *, income_first):
        seed_clean_world()
        state=random.getstate();self.addCleanup(random.setstate,state);random.seed(71)
        call_command('run_bots',create=3,create_only=True,stdout=StringIO())
        from .bots import tick_bot
        from .camp_progression import BY_RANK,quest_complete
        from .magic import circle_cap
        actors=[]
        for name,camp in [('warrior','OLD_CAMP'),('archer','NEW_CAMP'),('mage','SWAMP_CAMP')]:
            user=User.objects.create_user('probe-'+name)
            p=user.playerprofile;self.assertTrue(game.choose_camp(p,camp))
            client=Client();client.force_login(user)
            actors.append((name,p,client,Counter()))
        bots=list(PlayerProfile.objects.filter(is_bot=True));now=timezone.now();bot_actions=Counter()
        for step in range(600):
            with patch('django.utils.timezone.now',return_value=now+timedelta(minutes=15*step)):
                for bot in bots:
                    action,success=tick_bot(bot, force_active=True);self.assertTrue(success,(step,action));bot_actions[action]+=1
                for name,p,client,actions in actors:
                    p.refresh_from_db();game.refresh_player(p)
                    if p.level>=6 and actions[{'mage':'magic_hunt','archer':'ranged_hunt','warrior':'melee_hunt'}[name]]>=10:continue
                    def post(route,**data):
                        response=client.post(route,data)
                        self.assertEqual(response.status_code,302,(name,route,response.status_code))
                        p.refresh_from_db()
                    run=p.adventures.filter(claimed_at__isnull=True).first()
                    if run:
                        if run.ends_at<=timezone.now():post('/zadania/',action='claim',run=run.pk);actions['adventure_claim']+=1
                        else:actions['wait']+=1
                        continue
                    if p.action_end_time:
                        if p.action_end_time<=timezone.now():post('/kopalnia/',action='claim');actions['mine_claim']+=1
                        continue
                    # Camp requirements are earned after accepting the actual promotion quest.
                    rank_key=('PICKER' if p.guild=='NONE' else 'NOVICE' if p.guild=='PICKER' else '') if name=='mage' else ''
                    target=None
                    if rank_key:
                        rank=BY_RANK[rank_key];cq=p.camp_quests.filter(rank_key=rank_key,promoted_at__isnull=True).first()
                        if not cq:post('/oboz/',action='accept',rank=rank_key);actions['rank_accept']+=1;continue
                        if quest_complete(cq,rank) and p.level>=rank.level and getattr(p,rank.attribute)>=rank.attribute_value and p.ore_balance>=rank.cost:
                            post('/oboz/',action='promote',rank=rank_key);actions['rank_promote']+=1;continue
                        target=next((g.event.split(':',1)[1] for g in rank.objectives if g.event.startswith('hunt:') and cq.progress.get(g.event,0)<g.count),None)
                    # Spend earned PN, reserving five for the mage's first circle.
                    reserve=5 if name=='mage' and not p.magic_skill else 0
                    attribute='strength' if name=='warrior' else 'dexterity' if name=='archer' else 'mana'
                    mastery='onehand_skill' if name=='warrior' else 'bow_skill'
                    if p.skill_points>reserve and p.ore_balance>=p.training_cost:
                        skill=mastery if name!='mage' and getattr(p,mastery)<min(20,p.level*3) else attribute
                        post('/trening/',attribute=skill,count=1);actions['train_'+skill]+=1;continue
                    if name=='mage' and not p.magic_skill and circle_cap(p) and p.level>=2 and p.skill_points>=5 and p.ore_balance>=50:
                        post('/magia/',action='learn');actions['learn_circle']+=1;continue
                    if name=='mage' and p.magic_skill and not p.prepared_magic_id:
                        rune=ItemBluePrint.objects.get(catalog_key='g1-itarrunewindfist')
                        owned=p.inventory.filter(blueprint=rune).first()
                        if owned:post('/magia/',action='prepare',item=owned.pk);actions['prepare_rune']+=1;continue
                        if p.ore_balance>=rune.base_value:post('/magia/',action='buy',blueprint=rune.pk);actions['buy_rune']+=1;continue
                    weapon_type='bow' if name=='archer' else 'onehand'
                    equipped=p.inventory.filter(is_equipped=True,equipped_slot='weapon').select_related('blueprint').first()
                    # Buy only improvements, leaving the mage's rune savings intact.
                    best=ItemBluePrint.objects.filter(merchant=True,kind='weapon',weapon_type=weapon_type,required_strength__lte=p.strength,required_dexterity__lte=p.dexterity,min_level__lte=p.level,min_camp_tier__lte=p.camp_tier,required_camp__in=['',p.camp],base_value__lte=p.ore_balance).order_by('-damage','base_value').first()
                    if best and (not equipped or best.damage>equipped.effective_stats['damage']) and (name!='mage' or not equipped):
                        owned=p.inventory.filter(blueprint=best,is_equipped=False,is_market_listed=False).first()
                        if owned:self.assertTrue(game.equip_item(p,owned));actions['equip']+=1
                        else:
                            post('/sklep/',action='buy',buy_item_id=best.pk);actions['buy_weapon']+=1
                            owned=p.inventory.filter(blueprint=best,is_equipped=False,is_market_listed=False).first()
                            self.assertIsNotNone(owned)
                            self.assertTrue(game.equip_item(p,owned));actions['equip']+=1
                        continue
                    if name=='archer':
                        ammo=p.inventory.filter(blueprint__kind='ammo',blueprint__original_stats__ammo_type='arrow',is_market_listed=False).first()
                        if not ammo or ammo.quantity<2:
                            bp=ItemBluePrint.objects.filter(merchant=True,kind='ammo',original_stats__ammo_type='arrow').order_by('base_value').first()
                            if bp and p.ore_balance>=bp.base_value*10:
                                post('/sklep/',action='buy',buy_item_id=bp.pk,quantity=10);actions['buy_ammo_pack']+=1;continue
                    # Real loot funds the next weapon; equipped/protected/prepared items stay.
                    spare=p.inventory.filter(is_equipped=False,is_market_listed=False,is_protected=False,blueprint__tradeable=True,blueprint__kind='weapon').first()
                    if spare:
                        self.assertTrue(game.sell_item_from_npc(p,spare));actions['sell_loot']+=1;continue
                    habitats={key:loc.key for loc in reversed(LOCATIONS) if loc.accessible(p) for key in loc.monsters}
                    preview=hunt_preparation(p,{key:BESTIARY[key] for key in habitats})
                    choices=[key for key in habitats if preview['forecasts'][key]['needed']<=p.current_health]
                    # Alternate repeatable contracts and hunts to fund all three builds.
                    need_funds=p.ore_balance<50 or (name=='mage' and not p.prepared_magic_id)
                    if not target and (step%4==0 or need_funds or preview['blocks'] or not choices):
                        quest=AdventureTemplate.objects.filter(enabled=True,level__lte=p.level,energy_cost__lte=p.current_energy).order_by('-ore_reward' if income_first and need_funds else '-experience_reward').first()
                        if quest:post('/zadania/',action='start',template=quest.pk);actions['adventure_start']+=1;continue
                    key=target if target in choices else max(choices,key=lambda k:BESTIARY[k]['exp_reward']) if choices else None
                    if key and not preview['blocks']:
                        before=p.battles.count()
                        post('/polowanie/?location='+habitats[key],monster_key=key,request_key=uuid4())
                        self.assertEqual(p.battles.count(),before+1)
                        battle=p.battles.first();self.assertTrue(battle.won,(name,key,battle.combat_log))
                        if p.prepared_magic_id:self.assertIn('Uderzenie wiatru',str(battle.combat_log))
                        actions['magic_hunt' if p.prepared_magic_id else 'ranged_hunt' if name=='archer' else 'melee_hunt']+=1
                    else:actions['wait']+=1
            if all(p.level>=6 and actions[{'mage':'magic_hunt','archer':'ranged_hunt','warrior':'melee_hunt'}[name]]>=10 for name,p,_,actions in actors):break
        facts=[]
        for name,p,_,actions in actors:
            p.refresh_from_db();self.assertGreaterEqual(p.level,6,(name,dict(actions),p.__dict__))
            self.assertFalse(p.user.is_staff)
            if name=='mage':self.assertGreaterEqual(actions['magic_hunt'],10);self.assertEqual(p.guild,'NOVICE')
            else:
                self.assertGreater(getattr(p,'onehand_skill' if name=='warrior' else 'bow_skill'),0)
                self.assertGreaterEqual(actions['melee_hunt' if name=='warrior' else 'ranged_hunt'],10)
            facts.append({'build':name,'level':p.level,'xp':p.experience,'ore':p.ore_balance,'strength':p.strength,'dexterity':p.dexterity,'mana':p.mana,'mastery':p.onehand_skill if name=='warrior' else p.bow_skill if name=='archer' else p.magic_skill,'actions':dict(actions),'defeats':p.battles.filter(won=False).count()})
        self.assertFalse(BotDecision.objects.filter(success=False).exists())
        record_scenario('trzy-buildy-z-finansowaniem' if income_first else 'trzy-zwykle-buildy-od-zera',{'strategy':'zlecenia na rudę przy brakach' if income_first else 'zlecenia na PD','seed':71,'ticks':step+1,'simulated_hours':step/4,'minutes_per_tick':15,'characters':facts,'bot_actions':dict(bot_actions),'bots':3,'admin_grants':False,'limits':'Formularze treningu, zakupów, polowań, wypraw i awansu; serwisy regeneracji, wyposażenia i sprzedaży. Zegar przyspieszony, bez nadawania zasobów. To nie jest pomiar czasu aktywnego klikania ani retencji.'})
