from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import TestCase
from .models import OwnedItem,ItemBluePrint,MarketTrade
from .equipment import add_item
from . import game_logic as game
from .market_intelligence import MarketState,retention,sale_candidate,score
from .market_policy import list_bot_surplus,bot_market_plan
from .weapon_finance import finance,plan

class IntelligentMarketTests(TestCase):
    def setUp(self):
        self.s=User.objects.create_user('sprzedawca').playerprofile;self.s.is_bot=True;self.s.ore_balance=500;self.s.save()
        self.b=User.objects.create_user('nabywca').playerprofile;self.b.ore_balance=500;self.b.save()
        self.bp=ItemBluePrint.objects.create(name='Przydatny miecz',damage=20,base_value=100,merchant=False,required_strength=10)
        self.item=add_item(self.s,self.bp)
        self.best=add_item(self.s,ItemBluePrint.objects.create(name='Własny miecz',damage=40,base_value=200,merchant=False))
        game.equip_item(self.s,self.best)
    def test_ranked_portal_buyers_have_constant_market_query_count(self):
        from django.db import connection,transaction
        from django.test.utils import CaptureQueriesContext
        from .test_faction_succession import fixture,succeed,person
        from .factions import enroll
        from .models import FactionRankProgress,StoryQuest,StoryRun
        from .realms import world_scope
        c,i,race=fixture()
        portal=StoryQuest.objects.create(key="jark-portal",title="Query fixture",universe="JOINED")
        self.bp.catalog_key="oe-jark-query-fixture";self.bp.save()
        for actor in [self.s,self.b]:actor.camp='OLD_CAMP';actor.guild='BARON';actor.save()
        succeed(race)
        for actor in [self.s,self.b]:
            actor.refresh_from_db();FactionRankProgress.objects.create(membership=actor.faction_membership,tier=4)
            StoryRun.objects.create(profile=actor,quest=portal,status="claimed",snapshot={"key":"jark-portal"})
        def queries():
            with world_scope(c),CaptureQueriesContext(connection) as captured:
                MarketState(c.pk).quote(self.s,self.item)
            return len(captured)
        small=queries()
        for n in range(20):
            actor=person(c,'OLD_CAMP','BARON')
            with transaction.atomic():enroll(actor)
            FactionRankProgress.objects.create(membership=actor.faction_membership,tier=7)
            StoryRun.objects.create(profile=actor,quest=portal,status="claimed",snapshot={"key":"jark-portal"})
        large=queries();self.assertEqual(small,large);self.assertLessEqual(large,10)

    def test_junk_and_no_eligible_buyer_do_not_create_artificial_demand(self):
        junk=add_item(self.s,ItemBluePrint.objects.create(name='Drewniany kij',damage=1,base_value=5))
        self.assertEqual(MarketState(self.s.world_id).quote(self.s,junk).price,0)
        self.b.strength=1;self.b.save()
        self.assertEqual(MarketState(self.s.world_id).quote(self.s,self.item).price,0)
    def test_supply_reduces_price_and_limits_listing(self):
        initial=MarketState(self.s.world_id).quote(self.s,self.item).price
        for n in range(5):
            other=User.objects.create_user('zapas-'+str(n)).playerprofile
            OwnedItem.objects.create(owner=other,blueprint=self.bp,is_market_listed=True,market_price=100)
        state=MarketState(self.s.world_id)
        self.assertLess(state.quote(self.s,self.item).price,initial)
        self.assertIsNone(sale_candidate(self.s,list(self.s.inventory.select_related('blueprint')),market=state))
    def test_equivalent_npc_substitute_caps_price(self):
        ItemBluePrint.objects.create(name='Zamiennik',damage=21,base_value=70)
        q=MarketState(self.s.world_id).quote(self.s,self.item)
        self.assertLessEqual(q.price,round(70*.95));self.assertGreater(q.price,50)
    def test_best_future_and_protected_gear_are_retained(self):
        future=add_item(self.s,ItemBluePrint.objects.create(name='Na później',damage=60,required_strength=20,merchant=False))
        keep=retention(self.s,list(self.s.inventory.select_related('blueprint')))
        self.assertTrue({future.pk,self.best.pk}<=keep)
        self.assertFalse(list_bot_surplus(self.s,self.best))
        self.assertTrue(list_bot_surplus(self.s,self.item))
        duplicate=add_item(self.s,self.bp);self.assertFalse(list_bot_surplus(self.s,duplicate))
    def test_human_buys_bot_surplus_once_and_bot_keeps_playing(self):
        from .bots import tick_bot
        self.assertTrue(list_bot_surplus(self.s,self.item))
        self.item.refresh_from_db();price=self.item.market_price
        self.assertTrue(game.buy_item_on_market(self.b,self.item,price))
        self.assertFalse(game.buy_item_on_market(self.b,self.item,price))
        self.b.refresh_from_db();self.s.refresh_from_db();self.item.refresh_from_db()
        self.assertEqual(self.item.owner_id,self.b.pk)
        self.assertEqual(self.b.ore_balance,500-price)
        self.assertEqual(self.s.ore_balance,500+price)
        self.assertEqual(MarketTrade.objects.count(),1)
        self.assertTrue(tick_bot(self.s,force_active=True)[1])
        self.best.refresh_from_db()
        self.assertEqual(self.best.owner_id,self.s.pk)
        self.assertTrue(self.best.is_equipped)

    def test_legacy_best_listing_is_rescued(self):
        game.unequip_item(self.s,self.best);game.list_item_on_market(self.s,self.best,200)
        self.assertEqual(bot_market_plan(self.s)[:2],('market_cancel',self.best.pk))
    def test_variant_snapshots_and_repeated_buyer_do_not_poison_history(self):
        rare=add_item(self.s,self.bp,rarity=4)
        price=MarketState(self.s.world_id).quote(self.s,rare).price
        MarketTrade.objects.create(seller=self.s,buyer=self.b,blueprint=self.bp,price=99999,quantity=1)
        self.assertEqual(MarketState(self.s.world_id).quote(self.s,rare).price,price)
        for _ in range(25):MarketTrade.objects.create(seller=self.s,buyer=self.b,blueprint=self.bp,price=130,quantity=1,rarity=0,upgrade_level=0)
        self.assertEqual(MarketState(self.s.world_id).quote(self.s,self.item).sales,1)
        game.list_item_on_market(self.s,rare,150);self.assertTrue(game.buy_item_on_market(self.b,rare,150))
        t=MarketTrade.objects.first();self.assertEqual((t.rarity,t.upgrade_level),(4,0))
    def test_build_score_does_not_switch_strength_warrior_to_bad_bow(self):
        self.s.strength=100;self.s.dexterity=10
        bow=ItemBluePrint.objects.create(name='Łuk',damage=50,weapon_type='bow')
        self.assertLess(score(self.s,bow),score(self.s,self.best))
    def test_financing_replacement_is_atomic_and_preserves_rare_gear(self):
        self.s.ore_balance=30;self.s.save()
        better=ItemBluePrint.objects.create(name='Dostępny zamiennik',damage=80,base_value=100)
        self.assertEqual(plan(self.s,list(self.s.inventory.select_related('blueprint')),[better]),better)
        with patch('characters.game_logic.buy_item_from_npc',return_value=False):
            self.assertFalse(finance(self.s,self.best.pk,better.pk,100))
        self.best.refresh_from_db();self.s.refresh_from_db()
        self.assertTrue(self.best.is_equipped);self.assertEqual(self.s.ore_balance,30)
        self.assertFalse(finance(self.s,self.best.pk,better.pk,101))
        self.assertTrue(finance(self.s,self.best.pk,better.pk,100))
        self.assertEqual(self.s.inventory.get(is_equipped=True).blueprint_id,better.pk)

    def test_own_equivalent_listing_is_not_a_reason_to_buy_the_same_weapon_again(self):
        game.list_item_on_market(self.b,add_item(self.b,self.bp),100)
        self.assertTrue(game.list_item_on_market(self.s,self.item,5))
        market = MarketState(self.s.world_id)
        self.assertEqual(market.need(self.b,self.item),0)
        self.assertFalse(market.can_buy(self.b,self.item))
    def test_inactive_seller_does_not_break_bot_planning(self):
        self.b.user.is_active=False;self.b.user.save()
        game.list_item_on_market(self.b,add_item(self.b,self.bp),10)
        from .bots import tick_bot
        self.assertTrue(tick_bot(self.s,force_active=True)[1])
    def test_rare_weapon_is_not_liquidated_to_finance_an_npc_upgrade(self):
        game.unequip_item(self.s,self.best)
        rare=add_item(self.s,self.best.blueprint,rarity=3);game.equip_item(self.s,rare)
        self.s.ore_balance=30;self.s.save()
        b=ItemBluePrint.objects.create(name='Zamiennik rzadkiej',damage=150,base_value=100)
        self.assertIsNone(plan(self.s,list(self.s.inventory.select_related('blueprint')),[b]))

    def test_account_alts_do_not_multiply_history_and_drafts_add_no_demand(self):
        from .character_selection import create_character
        alt=create_character(self.b.user,'Drugi nabywca',self.b.world_id)
        for buyer in (self.b,alt):MarketTrade.objects.create(seller=self.s,buyer=buyer,blueprint=self.bp,price=100,quantity=1,rarity=0,upgrade_level=0)
        self.assertEqual(MarketState(self.s.world_id).quote(self.s,self.item).sales,1)
        self.b.is_draft=True;self.b.save();alt.is_draft=True;alt.save()
        self.assertEqual(MarketState(self.s.world_id).quote(self.s,self.item).price,0)

    def test_small_accessory_bonus_has_value_when_a_ring_slot_is_empty(self):
        ring = ItemBluePrint.objects.create(name='Pierścień z drobnym bonusem', kind='ring',
                                            strength_bonus=1, merchant=False, base_value=12)
        offered = add_item(self.s, ring)
        self.assertEqual(MarketState(self.s.world_id).need(self.b, offered), 1)
        add_item(self.b, ring)
        self.assertEqual(MarketState(self.s.world_id).need(self.b, offered), 1)
        add_item(self.b, ring)
        self.assertEqual(MarketState(self.s.world_id).need(self.b, offered), 0)

    def test_khorinis_bot_sells_one_spare_restorative_to_player_through_market(self):
        from django.urls import reverse
        from .models import World

        world = World.objects.create(name='Targ w Khorinis', universe='GOTHIC_II',
                                     edition=2, is_open=True, configured=True)
        self.item.delete()
        colony = self.b.world
        for profile in (self.s, self.b):
            profile.world = world
            profile.save(update_fields=['world'])
        potion = ItemBluePrint.objects.create(name='Wywar z Khorinis', kind='consumable',
                                               source_game='GOTHIC_II', stackable=True,
                                               heal_amount=20, merchant=False, base_value=8)
        stack = add_item(self.s, potion, 4, origin='loot')
        self.assertEqual(MarketState(world.pk).need(self.b, stack), 1)
        self.assertFalse(list_bot_surplus(self.s, stack, reserved={potion.pk}))
        self.assertTrue(list_bot_surplus(self.s, stack))
        offer = self.s.inventory.get(blueprint=potion, is_market_listed=True)
        self.assertEqual(offer.quantity, 1)
        price = offer.market_price
        stack.refresh_from_db()
        self.assertEqual(stack.quantity, 3)
        self.client.force_login(self.b.user)
        market = reverse('market_page')
        self.assertContains(self.client.get(market), potion.name)
        payload = {'action': 'buy', 'buy_item_id': offer.pk, 'expected_price': price}
        outsider = User.objects.create_user('outsider-market').playerprofile
        outsider.world = colony
        outsider.ore_balance = 500
        outsider.save(update_fields=['world', 'ore_balance'])
        self.assertFalse(game.buy_item_on_market(outsider, offer, price))
        self.assertEqual(self.client.post(market, payload).status_code, 302)
        self.assertEqual(self.client.post(market, payload).status_code, 302)
        offer.refresh_from_db()
        self.s.refresh_from_db()
        self.b.refresh_from_db()
        self.assertEqual((offer.owner_id, self.s.ore_balance, self.b.ore_balance),
                         (self.b.pk, 500 + price, 500 - price))
        self.assertEqual(MarketTrade.objects.filter(blueprint=potion).count(), 1)
        self.assertEqual(MarketState(world.pk).need(self.b, stack), 0)

    def test_player_restorative_offer_respects_mana_and_health_when_matching_npc(self):
        tonic = ItemBluePrint.objects.create(name='Wywar na zdrowie i manę', kind='consumable',
                                             merchant=False, base_value=30, heal_amount=10,
                                             original_stats={'browser_restore': {'mana': 15}})
        ItemBluePrint.objects.create(name='Prosty wywar', kind='consumable',
                                     merchant=True, base_value=4, heal_amount=10)
        complete = ItemBluePrint.objects.create(name='Wywar mistrza', kind='consumable',
                                                merchant=True, base_value=24, heal_amount=10,
                                                original_stats={'browser_restore': {'mana': 20}})
        self.b.magic_skill = 5
        self.b.is_bot = True
        self.b.save(update_fields=['magic_skill', 'is_bot'])
        self.s.is_bot = False
        self.s.save(update_fields=['is_bot'])
        self.client.force_login(self.s.user)
        from django.urls import reverse
        offered = add_item(self.s, tonic, origin='loot')
        self.assertEqual(self.client.post(reverse('market_page'), {
            'action': 'list', 'sell_item_id': offered.pk, 'item_price': 18,
        }).status_code, 302)
        offered.refresh_from_db()
        self.assertEqual(MarketState(self.s.world_id).ceiling(self.b, offered), complete.base_value)
        self.assertEqual(bot_market_plan(self.b), ('market_buy', offered.pk, 18))
        self.assertTrue(game.buy_item_on_market(self.b, offered, 18))
        self.assertEqual(bot_market_plan(self.b), ('', None, 0))

    def test_player_bargain_is_judged_against_buyers_npc_alternative(self):
        costly = ItemBluePrint.objects.create(name='Pierścień z łupu', kind='ring',
                                              strength_bonus=3, merchant=False, base_value=100)
        ItemBluePrint.objects.create(name='Zamiennik kupca', kind='ring', strength_bonus=3,
                                     merchant=True, base_value=12)
        offered = add_item(self.s, costly)
        self.assertEqual(MarketState(self.s.world_id).quote(self.s, offered).price, 0)
        self.assertTrue(game.list_item_on_market(self.s, offered, 15))
        self.assertEqual(bot_market_plan(self.b), ('', None, 0))
        from .market_policy import reprice_listing
        self.assertTrue(reprice_listing(self.s, offered, 9, 15))
        self.assertEqual(bot_market_plan(self.b), ('market_buy', offered.pk, 9))

    def test_healthy_alchemist_can_buy_ingredients_for_one_spare_potion(self):
        from .crafting import craft_item
        from .models import CraftRecipe
        from uuid import uuid4

        material = ItemBluePrint.objects.create(name='Zioła zapasowe', kind='material', stackable=True,
                                                merchant=False, base_value=4)
        tonic = ItemBluePrint.objects.create(name='Wywar wędrowca', kind='consumable', heal_amount=30)
        recipe = CraftRecipe.objects.create(
            key='tonic-for-the-road', name='Wywar wędrowca', discipline='alchemy', level=0, skill=1,
            fee=5, ingredients=[{'blueprint': material.pk, 'count': 1}], output=tonic,
        )
        self.b.alchemy_skill = 1
        self.b.current_health = self.b.max_health
        self.b.save(update_fields=['alchemy_skill', 'current_health'])
        self.item.delete()
        offered = add_item(self.s, material, origin='loot')
        self.assertTrue(list_bot_surplus(self.s, offered))
        offered.refresh_from_db()
        self.assertEqual(bot_market_plan(self.b)[:2], ('market_buy', offered.pk))
        self.assertTrue(game.buy_item_on_market(self.b, offered, offered.market_price))
        self.assertTrue(craft_item(self.b, recipe.pk, uuid4()))
        fresh = add_item(self.s, material, origin='loot')
        self.assertFalse(MarketState(self.s.world_id).need(self.b, fresh))

    def test_bot_buys_cheaper_ingredient_from_player_on_a_crafting_turn(self):
        from .bots import tick_bot
        from .models import CraftRecipe

        material = ItemBluePrint.objects.create(name='Zioła z targu', kind='material', stackable=True,
                                                merchant=False, base_value=8)
        potion = ItemBluePrint.objects.create(name='Mikstura z ziół', kind='consumable', heal_amount=30)
        CraftRecipe.objects.create(
            key='workshop-market', name=potion.name, discipline='alchemy', level=0, skill=1,
            fee=5, ingredients=[{'blueprint': material.pk, 'count': 2}], output=potion,
        )
        self.s.is_bot = False
        self.s.save(update_fields=['is_bot'])
        self.b.is_bot = True
        self.b.bot_turn = 23
        self.b.alchemy_skill = 1
        self.b.save(update_fields=['is_bot', 'bot_turn', 'alchemy_skill'])
        offered = add_item(self.s, material, 2)
        self.assertTrue(game.list_item_on_market(self.s, offered, 16))
        self.assertFalse(MarketState(self.s.world_id).can_buy(self.b, offered))
        from .market_policy import reprice_listing
        self.assertTrue(reprice_listing(self.s, offered, 14, 16))
        self.assertEqual(tick_bot(self.b, force_active=True), ('market_buy', True))
        trade = MarketTrade.objects.get(blueprint=material)
        self.assertEqual((trade.seller_id, trade.buyer_id, trade.quantity, trade.price),
                         (self.s.pk, self.b.pk, 2, 14))
        self.assertEqual(self.b.inventory.get(blueprint=material).quantity, 2)

    def test_alchemist_sells_only_materials_above_their_recipe_reserve(self):
        from .crafting import craft_item, ingredient_reserves
        from .models import CraftRecipe
        from uuid import uuid4

        material = ItemBluePrint.objects.create(name='Zioła dwóch alchemików', kind='material',
                                                stackable=True, base_value=8)
        potion = ItemBluePrint.objects.create(name='Mikstura alchemików', kind='consumable', heal_amount=30)
        recipe = CraftRecipe.objects.create(
            key='shared-alchemy-workshop', name=potion.name, discipline='alchemy', level=0, skill=1,
            fee=5, ingredients=[{'blueprint': material.pk, 'count': 2}], output=potion,
        )
        for profile in (self.s, self.b):
            profile.alchemy_skill = 1
            profile.save(update_fields=['alchemy_skill'])
        self.item.delete()
        reserve = add_item(self.s, material, 1, origin='merchant')
        stack = add_item(self.s, material, 3, origin='loot')
        self.assertFalse(list_bot_surplus(self.s, reserve))
        self.assertTrue(list_bot_surplus(self.s, stack))
        offer = self.s.inventory.get(blueprint=material, is_market_listed=True)
        stack.refresh_from_db()
        self.assertEqual((reserve.quantity, stack.quantity, offer.quantity), (1, 1, 2))
        inventory = list(self.s.inventory.select_related('blueprint'))
        craft_reserves = ingredient_reserves(self.s, inventory)
        self.assertEqual(craft_reserves, {material.pk: 2})
        self.assertNotEqual(bot_market_plan(self.s, craft_reserves=craft_reserves)[0], 'market_cancel')
        self.assertTrue(game.buy_item_on_market(self.b, offer, offer.market_price))
        self.assertTrue(craft_item(self.s, recipe.pk, uuid4()))
        self.assertTrue(craft_item(self.b, recipe.pk, uuid4()))

    def test_bot_can_list_a_real_recipe_shortfall_from_a_surplus_stack(self):
        from .models import CraftRecipe
        from .market_intelligence import sale_lot

        material = ItemBluePrint.objects.create(name='Mięso z pól', kind='material', stackable=True, base_value=4)
        tonic = ItemBluePrint.objects.create(name='Wywar', kind='consumable', heal_amount=40)
        CraftRecipe.objects.create(
            key='tonic-small-lot', name='Wywar', discipline='alchemy', level=0, skill=1,
            fee=5, ingredients=[{'blueprint': material.pk, 'count': 2}], output=tonic,
        )
        self.b.alchemy_skill = 1
        self.b.current_health = 5
        self.b.save(update_fields=['alchemy_skill', 'current_health'])
        trophy = ItemBluePrint.objects.create(name='Znak warty', kind='quest', tradeable=False)
        OwnedItem.objects.bulk_create([OwnedItem(owner=self.s, blueprint=trophy) for _ in range(12)])
        stack = add_item(self.s, material, 7, origin='loot')
        market = MarketState(self.s.world_id)
        self.assertEqual(market.quote(self.s, stack).price, 0)
        self.assertEqual(sale_lot(market, self.s, stack)[0], 2)
        self.item.delete()
        with patch('characters.game_logic.list_item_on_market', return_value=False):
            self.assertFalse(list_bot_surplus(self.s, stack))
        stack.refresh_from_db()
        self.assertEqual(stack.quantity, 7)
        self.assertFalse(self.s.inventory.filter(blueprint=material, is_market_listed=True).exists())
        self.assertTrue(list_bot_surplus(self.s, stack))
        stack.refresh_from_db()
        self.assertEqual(stack.quantity, 5)
        lot = self.s.inventory.get(blueprint=material, is_market_listed=True)
        self.assertEqual((lot.quantity, lot.origin), (2, 'loot'))
        self.assertEqual(bot_market_plan(self.b)[:2], ('market_buy', lot.pk))
        self.assertTrue(game.buy_item_on_market(self.b, lot, lot.market_price))
        self.assertEqual(MarketTrade.objects.get().quantity, 2)
        self.assertEqual(self.b.inventory.get(blueprint=material).quantity, 2)
