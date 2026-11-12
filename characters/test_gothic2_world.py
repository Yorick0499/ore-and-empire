from datetime import timedelta
from io import StringIO
from unittest.mock import patch
from django.core.management import call_command
from django.test import TestCase,SimpleTestCase
from django.utils import timezone
from .test_faction_succession import fixture,person,succeed
from .gothic2_world import DATA,BOSS_ROWS,campaign
from .models import StoryQuest,ItemBluePrint,OwnedItem
from . import game_logic as game

class NkWorldCatalogTests(SimpleTestCase):
    def test_all_85_source_models_have_explicit_roles_and_67_have_habitats(self):
        from .locations import LOCATIONS
        from .bestiary import BESTIARY
        self.assertEqual(len(DATA),85);self.assertEqual(sum(r['role']=='hunt' for r in DATA),67)
        for r in DATA:
            self.assertIn(r['role'],{'hunt','boss','summon','special','quest_variant'})
            if r['role']=='hunt':self.assertIn(r['key'],BESTIARY);self.assertTrue(any(r['key'] in loc.monsters for loc in LOCATIONS))
            else:self.assertNotIn(r['key'],BESTIARY)
    def test_all_new_bosses_have_actual_elemental_phases_and_conservative_forecasts(self):
        from .bosses import encounter_round
        for key,*_ in BOSS_ROWS:
            monster=game.BOSSES[key].monster
            for ratio in (1,.6,.25):
                for turn in range(1,7):
                    stage,armor,strength,kind,log=encounter_round(monster,int(monster['life']*ratio),turn)
                    self.assertLessEqual(armor,monster['forecast_protection']);self.assertLessEqual(strength,monster['forecast_strength'])
                    self.assertIn(kind,{'weapon','fire','magic'})
                    if turn==3:self.assertTrue(log)

class NkWorldServices(TestCase):
    def setUp(self):
        self.c,self.i,self.race=fixture();call_command('seed_khorinis',stdout=StringIO())
    def test_world_seed_preserves_operator_changes_and_has_distinct_boss_trophies(self):
        from .models import LootTable
        q=StoryQuest.objects.get(key='nk-undead');q.title='Tytuł operatora';q.save()
        before=(StoryQuest.objects.count(),ItemBluePrint.objects.count())
        call_command('seed_gothic2_world',stdout=StringIO());q.refresh_from_db();self.assertEqual(q.title,'Tytuł operatora');self.assertEqual(before,(StoryQuest.objects.count(),ItemBluePrint.objects.count()))
        tables=[LootTable.objects.get(key=row[0]).entries for row in BOSS_ROWS]
        self.assertEqual(len({str(t) for t in tables}),8)
    def test_late_regions_require_global_join_portal_and_real_sailing_claim(self):
        from .locations import BY_KEY
        p=person(self.i,'NONE','NONE');p.level=50;p.life=1000;p.current_health=1000;p.save()
        self.assertFalse(BY_KEY['g2nk_irdorath'].accessible(p));self.assertFalse(game.execute_boss(p,'g2nk_dragon_undead'))
        self.assertFalse(game.execute_boss(p,'g2nk_raven'))
        from .models import World
        World.objects.filter(pk__in=[self.c.pk,self.i.pk]).update(union_key=None)
        self.assertFalse(BY_KEY['g2nk_forest'].accessible(p))
        self.assertFalse(__import__('characters.story_quests',fromlist=['accept_story']).accept_story(p,StoryQuest.objects.get(key='nk-scouts').pk))
    def test_two_mage_schools_and_archer_can_pay_for_gear_and_defeat_late_boss(self):
        from .magic import learn_circle,purchase_magic,prepare_magic,NK_SPELLS,offers
        from .equipment import allowed
        for camp,rank,school in [('OLD_CAMP','ARCH_FIRE','fire'),('NEW_CAMP','ARCH_WATER','water'),('OLD_CAMP','BARON','archer')]:
            p=person(self.c,camp,rank);p.level=45;p.life=580;p.current_health=580;p.mana=300;p.current_mana=300;p.strength=10;p.dexterity=200 if school=='archer' else 10;p.bow_skill=60 if school=='archer' else 0;p.skill_points=150;p.ore_balance=30000;p.save()
        succeed(self.race)
        from .testing_story import claimed_milestone
        # Initial veterans are explicit fixtures; purchases, learning and fights are real services.
        from .models import PlayerProfile
        for p in PlayerProfile.objects.filter(world=self.c).exclude(camp='NONE'):
            school='archer' if p.guild=='BARON' else 'fire' if p.guild=='ARCH_FIRE' else 'water'
            claimed_milestone(p,'nk-sailing')
            from .barrier import travel
            self.assertTrue(travel(p,self.i.pk))
            armor=next(b for b in ItemBluePrint.objects.filter(merchant=True,kind='armor',min_level__lte=p.level).order_by('-weapon_prot','base_value') if allowed(p,b))
            self.assertTrue(game.buy_item_from_npc(p,armor));self.assertTrue(game.equip_item(p,p.inventory.get(blueprint=armor)))
            if school=='archer':
                for _ in range(4):self.assertTrue(game.train_attribute(p,'bow_skill',10))
                bow=next(b for b in ItemBluePrint.objects.filter(source_game='GOTHIC_II',merchant=True,kind='weapon',weapon_type='bow',required_dexterity__lte=p.dexterity,required_strength__lte=p.strength).order_by('-damage') if allowed(p,b))
                self.assertTrue(game.buy_item_from_npc(p,bow));self.assertTrue(game.equip_item(p,p.inventory.get(blueprint=bow)))
                ammo=ItemBluePrint.objects.get(catalog_key='g2nk-itrw_arrow');self.assertTrue(game.buy_item_from_npc(p,ammo,100))
            else:
                for _ in range(6):self.assertTrue(learn_circle(p))
                spell=next(s for s in NK_SPELLS if s.school==school);bp=ItemBluePrint.objects.get(catalog_key=f'oe-nk-{spell.key}-rune')
                item=purchase_magic(p,bp.pk);self.assertTrue(item);self.assertTrue(prepare_magic(p,item.pk))
            result=game.execute_boss(p,'g2nk_dragon_undead');self.assertTrue(result);self.assertTrue(result.won,(school,result.combat_log))
            if school!='archer':self.assertTrue(any('koszt 18 many' in line for line in p.battles.first().combat_log))
    def test_mastered_archery_forecast_matches_guaranteed_combat_damage(self):
        from .equipment import physical_survival_health
        p=person(self.c,'OLD_CAMP','BARON');p.level=45;p.dexterity=200;p.life=600;p.current_health=600;p.bow_skill=100;p.save()
        bp=ItemBluePrint.objects.create(name='Forecast bow',kind='weapon',weapon_type='bow',damage=160,damage_type='arrow')
        OwnedItem.objects.create(owner=p,blueprint=bp,is_equipped=True,equipped_slot='weapon')
        monster=game.BOSSES['g2nk_dragon_undead'].monster
        result=game.simulate_combat(p,'g2nk_dragon_undead',monster=monster)
        self.assertEqual(physical_survival_health(p,monster),600-result.remaining_health+10)
    def test_foreign_rank_boss_cannot_preempt_a_local_story_hunt(self):
        from .models import FactionRankProgress,CampQuest
        from .testing_story import claimed_milestone
        from .story_quests import accept_story,activate_story
        from .barrier import travel
        from .bots import tick_bot
        p=person(self.c,'OLD_CAMP','BARON',bot=True);p.level=45;p.strength=500;p.life=2000;p.current_health=2000;p.weapon_prot=150;p.fire_prot=150;p.save();succeed(self.race)
        p.refresh_from_db();FactionRankProgress.objects.create(membership=p.faction_membership,tier=4)
        CampQuest.objects.create(profile=p,rank_key='ADV_BANDITS_5')
        claimed_milestone(p,'jark-portal');self.assertTrue(travel(p,self.i.pk))
        quest=StoryQuest.objects.create(key='local-route-probe',title='Local hunt',universe='JOINED',objectives=[{'id':'hunt','kind':'hunt','target':'jark_lurker','label':'Hunt'}])
        self.assertTrue(accept_story(p,quest.pk));self.assertTrue(activate_story(p,p.story_runs.get(quest=quest).pk))
        captured=[]
        class Capture:
            def choose(self,o):captured.append(o);return 'wait',None
        tick_bot(p,policy=Capture(),force_active=True)
        self.assertIsNone(captured[0].boss_key);self.assertEqual(captured[0].hunt_key,'jark_lurker')
    def test_armed_bot_buys_and_delivers_materials_with_full_equipment_inventory(self):
        from .models import CampQuest,FactionRankProgress
        from .story_quests import accept_story,activate_story,claim_story
        from .testing_story import claimed_milestone
        from .bots import tick_bot
        p=person(self.c,'OLD_CAMP','BARON',bot=True);p.level=45;p.strength=200;p.life=600;p.current_health=600;p.ore_balance=2000;p.save();succeed(self.race)
        p.refresh_from_db();FactionRankProgress.objects.create(membership=p.faction_membership,tier=7)
        for index,kind in enumerate(('weapon','armor','amulet','ring','ring','rune')):
            bp=ItemBluePrint.objects.create(name='Retained equipment '+kind,kind=kind,damage=40 if kind=='weapon' else 0,weapon_prot=40 if kind=='armor' else 0,mana_bonus=10 if kind=='amulet' else 0,strength_bonus=5 if kind=='ring' else 0,merchant=False)
            OwnedItem.objects.create(owner=p,blueprint=bp,is_equipped=kind!='rune',equipped_slot='ring2' if index==4 else '')
        self.assertEqual(p.inventory.count(),6);claimed_milestone(p,'nk-scouts')
        q=StoryQuest.objects.get(key='nk-supplies');self.assertTrue(accept_story(p,q.pk));run=p.story_runs.get(quest=q);self.assertTrue(activate_story(p,run.pk))
        now=timezone.now()
        with patch('django.utils.timezone.now',side_effect=lambda:now):
            for _ in range(3):
                self.assertTrue(game.start_mining(p,15));now+=timedelta(minutes=16);self.assertTrue(game.claim_ore_reward(p))
            before=p.ore_balance;actions=[]
            for _ in range(20):
                now+=timedelta(minutes=1);action,ok=tick_bot(p,force_active=True);actions.append(action)
                run.refresh_from_db()
                if run.status=='claimed':break
            self.assertEqual(run.status,'claimed',actions);self.assertIn('stock',actions)
            self.assertFalse(p.inventory.filter(blueprint__catalog_key='oe-nk-salvage').exists())
            p.refresh_from_db();self.assertEqual(p.ore_balance,before-36+q.rewards['ore'])
            self.assertFalse(claim_story(p,run.pk))
