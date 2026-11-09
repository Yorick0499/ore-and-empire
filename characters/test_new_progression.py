from datetime import timedelta
from io import StringIO
from unittest.mock import patch
from uuid import uuid4
from html.parser import HTMLParser
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase,Client
from django.utils import timezone
from .models import PlayerProfile,StoryQuest,StoryRun,CampQuest,CampGuild,CampSupplyUse,EnergyRefill,EconomicEntry
from . import game_logic as game
from .camp_progression import accept_camp_quest,promote_in_camp,BY_RANK
from .camp_privileges import privileges,claim_resupply
from .character_selection import create_character

# Controlled story state for boundary tests; real campaign tests still play every objective.
def claim(profile,key):
    q=StoryQuest.objects.get(key=key)
    fields=('key','version','title','description','chapter','level','camp','universe','prerequisites','any_prerequisites','required_choices','objectives','rewards','energy_cost')
    return StoryRun.objects.create(profile=profile,quest=q,status='claimed',snapshot={f:getattr(q,f) for f in fields},claimed_at=timezone.now())

class ProgressionGateTests(TestCase):
    def setUp(self):
        from .world_management import seed_clean_world
        seed_clean_world();self.p=User.objects.create_user('mieszkaniec').playerprofile
    def test_membership_requires_claimed_prologue_not_level_or_started_run(self):
        self.p.level=30;self.p.save();self.assertFalse(game.choose_camp(self.p,'OLD_CAMP'))
        run=claim(self.p,'prologue-path');run.status='active';run.save()
        self.assertFalse(game.choose_camp(self.p,'OLD_CAMP'))
        run.status='claimed';run.save();self.assertTrue(game.choose_camp(self.p,'OLD_CAMP'))
        self.assertFalse(game.choose_camp(self.p,'NEW_CAMP'))
    def test_promotion_requires_own_story_even_with_completed_rank_objectives(self):
        self.p.camp='OLD_CAMP';self.p.guild='DIGGER';self.p.level=3;self.p.strength=15;self.p.ore_balance=100;self.p.save()
        claim(self.p,'prologue-path');claim(self.p,'new-trust-2')
        self.assertFalse(accept_camp_quest(self.p,'SHADOW'))
        run=claim(self.p,'old-trust-2');self.assertTrue(accept_camp_quest(self.p,'SHADOW'))
        quest=CampQuest.objects.get(profile=self.p);quest.progress={o.event:o.count for o in BY_RANK['SHADOW'].objectives};quest.save()
        run.status='active';run.save();self.assertFalse(promote_in_camp(self.p,'SHADOW'))
        self.p.refresh_from_db();self.assertEqual(self.p.ore_balance,100)
        run.status='claimed';run.save();self.assertTrue(promote_in_camp(self.p,'SHADOW'))
        self.assertFalse(promote_in_camp(self.p,'SHADOW'))
    def test_rank_perks_and_upgrade_authority_grow(self):
        from .camp_guilds import upgrade_camp
        self.p.camp='OLD_CAMP';self.p.guild='DIGGER';self.p.save()
        guild=CampGuild.objects.get(world=self.p.world,camp=self.p.camp);guild.level=4;guild.treasury=1000;guild.save()
        self.assertFalse(upgrade_camp(self.p,'training',0))
        self.p.guild='SHADOW';self.p.save();self.assertTrue(upgrade_camp(self.p,'training',0))
        self.assertFalse(upgrade_camp(self.p,'training',1))
        self.p.guild='GUARD';self.p.save();self.assertTrue(upgrade_camp(self.p,'training',1))
        self.assertEqual(privileges(self.p)['supply'],2)
        self.p.guild='BARON';self.p.save();self.assertTrue(upgrade_camp(self.p,'training',2))
        self.assertEqual(privileges(self.p)['training'],2)
        self.p.refresh_from_db();self.assertEqual(self.p.camp_perks['training_level'],5)
    def test_daily_support_is_paid_capped_and_idempotent(self):
        now=timezone.now();self.p.camp='OLD_CAMP';self.p.guild='GUARD';self.p.ore_balance=100;self.p.life=100;self.p.current_health=10;self.p.current_energy=0;self.p.energy_updated_at=self.p.health_updated_at=now;self.p.save()
        with patch('django.utils.timezone.now',return_value=now):
            key=uuid4();first=claim_resupply(self.p,key);self.assertTrue(first)
            self.assertEqual(claim_resupply(self.p,key).pk,first.pk)
            self.assertFalse(claim_resupply(self.p,uuid4()))
        self.p.refresh_from_db();self.assertEqual((self.p.ore_balance,self.p.current_energy,self.p.current_health),(90,20,40))
        self.assertEqual(EnergyRefill.objects.filter(profile=self.p).count(),1)
        self.assertEqual(CampSupplyUse.objects.filter(profile=self.p).count(),1)
    def test_full_resources_and_exhausted_energy_cap_do_not_charge(self):
        self.p.camp='OLD_CAMP';self.p.guild='GUARD';self.p.save()
        self.assertFalse(claim_resupply(self.p,uuid4()))
        now=timezone.now();self.p.current_energy=0;self.p.energy_updated_at=now;self.p.save()
        for n in range(5):EnergyRefill.objects.create(profile=self.p,reference='fixture:'+str(n))
        with patch('django.utils.timezone.now',return_value=now):self.assertFalse(claim_resupply(self.p,uuid4()))
        self.p.refresh_from_db();self.assertEqual(self.p.ore_balance,50)

class CharacterFlowTests(TestCase):
    def setUp(self):self.user=User.objects.create_user('konto',password='Test-Only-Character-2026');self.p=self.user.playerprofile
    def test_registration_requires_creation_and_adopts_single_draft(self):
        response=self.client.post('/konto/rejestracja/',{'username':'nowy','password1':'Test-Only-Registration-2026','password2':'Test-Only-Registration-2026'})
        self.assertRedirects(response,'/postacie/')
        user=User.objects.get(username='nowy');p=user.playerprofile
        self.assertTrue(p.is_draft);self.assertFalse(game.start_mining(p,15))
        self.assertRedirects(self.client.get('/'),'/postacie/')
        self.assertEqual(self.client.post('/postacie/',{'action':'create','name':'Wędrowiec','world':p.world_id}).status_code,302)
        p.refresh_from_db();self.assertFalse(p.is_draft);self.assertEqual(p.name,'Wędrowiec')
        self.assertEqual(user.characters.count(),1)
        self.assertEqual(sum(EconomicEntry.objects.filter(profile=p,category='opening',resource='ore').values_list('amount',flat=True)),50)
    def test_five_slots_are_independent_and_switch_without_relogin(self):
        self.client.force_login(self.user)
        chars=[self.p]+[create_character(self.user,'Postać '+str(n),self.p.world_id) for n in range(2,6)]
        with self.assertRaises(ValidationError):create_character(self.user,'Szósta',self.p.world_id)
        self.assertEqual(list(self.user.characters.order_by('slot').values_list('slot',flat=True)),[1,2,3,4,5])
        chars[1].ore_balance=123;chars[1].save()
        self.assertEqual(self.client.post('/postacie/',{'profile':chars[1].pk}).status_code,302)
        page=self.client.get('/');self.assertEqual(page.context['profile'].pk,chars[1].pk)
        self.assertContains(page,'Postać 2');self.assertEqual(self.client.session['_auth_user_id'],str(self.user.pk))
        self.assertEqual(self.client.post('/postacie/',{'profile':self.p.pk}).status_code,302)
        self.assertEqual(self.client.get('/').context['profile'].ore_balance,50)
    def test_foreign_character_and_archived_world_cannot_be_selected(self):
        other=User.objects.create_user('obcy').playerprofile
        self.client.force_login(self.user)
        self.assertEqual(self.client.post('/postacie/',{'profile':other.pk}).status_code,404)
        from .models import World
        archived=World.objects.create(name='Archiwum',status='archived')
        with self.assertRaises(ValidationError):create_character(self.user,'Przemytnik',archived.pk)
    def test_names_are_normalized_and_unique_per_world(self):
        create_character(self.user,'Łowca',self.p.world_id)
        other=User.objects.create_user('inne-konto')
        with self.assertRaises(ValidationError):create_character(other,'łowca',self.p.world_id)
        with self.assertRaises(ValidationError):create_character(self.user,'<script>',self.p.world_id)
    def test_switch_rotates_csrf_so_old_tabs_cannot_act_on_new_character(self):
        c=Client(enforce_csrf_checks=True);c.force_login(self.user)
        other=create_character(self.user,'Druga',self.p.world_id)
        c.get('/postacie/');old=c.cookies['csrftoken'].value
        response=c.post('/postacie/',{'profile':other.pk,'csrfmiddlewaretoken':old})
        self.assertEqual(response.status_code,302);self.assertNotEqual(c.cookies['csrftoken'].value,old)
        self.assertEqual(c.post('/kopalnia/',{'action':'mine','csrfmiddlewaretoken':old}).status_code,403)
        self.assertEqual(c.post('/kopalnia/',{'action':'mine','csrfmiddlewaretoken':c.cookies['csrftoken'].value}).status_code,302)
        self.p.refresh_from_db();other.refresh_from_db();self.assertIsNone(self.p.action_end_time);self.assertIsNotNone(other.action_end_time)

class ItemshopLayoutTests(TestCase):
    def test_every_product_has_exactly_one_image_and_title(self):
        from .world_management import seed_clean_world
        seed_clean_world();user=User.objects.create_user('sklep');self.client.force_login(user)
        class Cards(HTMLParser):
            def __init__(self):super().__init__();self.cards=[];self.current=None
            def handle_starttag(self,tag,attrs):
                attrs=dict(attrs)
                if tag=='article' and 'store-card' in attrs.get('class',''):self.current={'images':0,'titles':0}
                if self.current is not None:
                    if tag=='img':self.current['images']+=1
                    if tag=='h3':self.current['titles']+=1
            def handle_endtag(self,tag):
                if tag=='article' and self.current is not None:self.cards.append(self.current);self.current=None
        parser=Cards();parser.feed(self.client.get('/sklep-odlamkow/').content.decode())
        self.assertEqual(len(parser.cards),17)
        self.assertTrue(all(card=={'images':1,'titles':1} for card in parser.cards),parser.cards)
