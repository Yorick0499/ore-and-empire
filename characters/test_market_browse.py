from urllib.parse import parse_qs, urlsplit
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from .market_browse import browse_market, PAGE_SIZE
from .models import ItemBluePrint, OwnedItem, World
from .game_logic import list_item_on_market


class MarketBrowseTests(TestCase):
    def setUp(self):
        self.profile = User.objects.create_user('browser').playerprofile
        self.seller = User.objects.create_user('seller').playerprofile
        self.sword = ItemBluePrint.objects.create(name='Miecz kopacza', kind='weapon', base_value=100)
        self.ring = ItemBluePrint.objects.create(name='Pierścień kopacza', kind='ring', base_value=80)
        self.client.force_login(self.profile.user)

    def offer(self, blueprint=None, owner=None, price=100, quantity=1, **kwargs):
        return OwnedItem.objects.create(blueprint=blueprint or self.sword, owner=owner or self.seller,
            market_price=price, is_market_listed=True, quantity=quantity, **kwargs)

    def test_combined_filters_and_quality_include_both_legacy_power_steps(self):
        first = self.offer(price=100, rarity=1, upgrade_level=1)
        second = self.offer(price=120, rarity=1, upgrade_level=2)
        self.offer(price=90, rarity=2)
        self.offer(self.ring, price=70)
        context = browse_market(self.profile, {'q':'Miecz','kind':'weapon','quality':'masterwork','max_price':'120','seller':'others','sort':'price'})
        self.assertEqual([i.pk for i in context['market_all_items']], [first.pk, second.pk])
        self.assertEqual(browse_market(self.profile, {'quality':'ordinary'})['market_all_items'].paginator.count, 1)

    def test_sort_unit_price_handles_fractional_prices_and_stable_ties(self):
        expensive_unit = self.offer(price=10)
        cheap_unit = self.offer(price=19, quantity=2)
        equal_unit = self.offer(price=38, quantity=4)
        cheaper_fraction = self.offer(price=28, quantity=3)
        context = browse_market(self.profile, {'sort':'unit'})
        self.assertEqual([i.pk for i in context['market_all_items']], [cheaper_fraction.pk, cheap_unit.pk, equal_unit.pk, expensive_unit.pk])
        self.assertEqual([i.pk for i in browse_market(self.profile, {'sort':'price-desc'})['market_all_items']], [equal_unit.pk, cheaper_fraction.pk, cheap_unit.pk, expensive_unit.pk])

    def test_only_current_world_and_own_offers_are_independent_of_filters(self):
        own = self.offer(self.ring, owner=self.profile)
        foreign_world = World.objects.create(name='Archiwum', status='archived')
        other = User.objects.create_user('archived').playerprofile
        other.world = foreign_world; other.save()
        self.offer(owner=other)
        self.offer()
        context = browse_market(self.profile, {'q':'nieistniejący','seller':'others'})
        self.assertEqual(context['market_all_items'].paginator.count, 0)
        self.assertEqual([i.pk for i in context['my_offers']], [own.pk])
        self.assertEqual(browse_market(self.profile, {'seller':'mine'})['market_all_items'].paginator.count, 1)
        self.assertEqual(browse_market(self.profile, {})['market_all_items'].paginator.count, 2)
        response = self.client.post('/plac_targowy/?q=nieistniejacy', {'action':'delist','delist_item_id':own.pk})
        self.assertEqual(response.url, '/plac_targowy/?q=nieistniejacy')
        own.refresh_from_db(); self.assertFalse(own.is_market_listed)

    def test_three_pages_are_bounded_and_links_preserve_validated_filters(self):
        for _ in range(PAGE_SIZE + 5):
            self.offer()
            self.offer(owner=self.profile)
            OwnedItem.objects.create(blueprint=self.sword, owner=self.profile)
        context = browse_market(self.profile, {'q':'kopacza','sort':'price','page':'2','bag_page':'2','own_page':'2'})
        for key in ['market_all_items','player_inventory','my_offers']:
            self.assertLessEqual(len(context[key]), PAGE_SIZE)
            self.assertEqual(context[key].number, 2)
        self.assertEqual(len(context['player_inventory']), 5)
        params = parse_qs(urlsplit(context['bag_pager']['previous_url']).query)
        self.assertEqual(params['q'], ['kopacza'])
        self.assertEqual(params['page'], ['2'])
        self.assertEqual(params['own_page'], ['2'])
        self.assertEqual(params['bag_page'], ['1'])

    def test_invalid_parameters_do_not_break_queries_or_render_raw_sort(self):
        self.offer()
        for price in ['-1','0','1000001','9'*5000,'NaN','１']:
            context = browse_market(self.profile, {'max_price':price,'sort':'DROP TABLE','kind':'invalid','quality':'invalid','page':'NaN'})
            self.assertEqual(context['market_all_items'].paginator.count, 1)
            self.assertEqual(context['market_filters']['sort'], 'newest')
            self.assertTrue(context['filter_error'])
            self.assertEqual(context['market_all_items'].number, 1)
        response = self.client.get('/plac_targowy/', {'q':'<script>alert(1)</script>'})
        self.assertNotContains(response, '<script>alert(1)</script>')

    def test_bag_excludes_protected_equipped_untradeable_and_prepared_items(self):
        visible = OwnedItem.objects.create(blueprint=self.sword, owner=self.profile)
        OwnedItem.objects.create(blueprint=self.sword, owner=self.profile, is_protected=True)
        OwnedItem.objects.create(blueprint=self.sword, owner=self.profile, is_equipped=True)
        forbidden = ItemBluePrint.objects.create(name='Trofeum', tradeable=False)
        OwnedItem.objects.create(blueprint=forbidden, owner=self.profile)
        prepared = OwnedItem.objects.create(blueprint=self.sword, owner=self.profile)
        self.profile.prepared_magic = prepared; self.profile.save()
        self.assertEqual([i.pk for i in browse_market(self.profile, {})['player_inventory']], [visible.pk])

    def test_offer_render_has_no_query_per_seller_or_blueprint(self):
        for _ in range(100): self.offer()
        self.offer(owner=self.profile)
        OwnedItem.objects.create(blueprint=self.sword, owner=self.profile)
        with self.assertNumQueries(6):
            context = browse_market(self.profile, {})
            for item in context['market_all_items']:
                _ = item.owner.display_name, item.blueprint.name, item.effective_stats, item.unit_price
            list(context['my_offers']); list(context['player_inventory'])
        response = self.client.get('/plac_targowy/', {'sort':'unit'})
        self.assertContains(response, 'Cena jednej sztuki rosnąco')
        self.assertContains(response, '101 pozycji')

    def test_unknown_legacy_dates_sort_after_real_new_offers(self):
        legacy = self.offer()
        dated = self.offer(listed_at=timezone.now()-timedelta(days=1))
        newest = self.offer(listed_at=timezone.now())
        context = browse_market(self.profile, {})
        self.assertEqual([i.pk for i in context['market_all_items']], [newest.pk, dated.pk, legacy.pk])

    def test_buy_from_old_page_cannot_pay_a_changed_price(self):
        from .market_policy import reprice_listing
        from .models import MarketTrade
        item=self.offer(price=20)
        self.assertContains(self.client.get('/plac_targowy/'),'name="expected_price" value="20"')
        self.assertTrue(reprice_listing(self.seller,item,40,20))
        before=(self.profile.ore_balance,self.seller.ore_balance)
        self.client.post('/plac_targowy/',{'action':'buy','buy_item_id':item.pk,'expected_price':20})
        self.profile.refresh_from_db();self.seller.refresh_from_db();item.refresh_from_db()
        self.assertEqual((self.profile.ore_balance,self.seller.ore_balance),before)
        self.assertEqual(item.owner_id,self.seller.pk);self.assertFalse(MarketTrade.objects.exists())
        for price in ['', 'NaN', '-1']:
            self.client.post('/plac_targowy/',{'action':'buy','buy_item_id':item.pk,'expected_price':price})
            item.refresh_from_db();self.assertEqual(item.owner_id,self.seller.pk)
        self.client.post('/plac_targowy/',{'action':'buy','buy_item_id':item.pk,'expected_price':40})
        item.refresh_from_db();self.assertEqual(item.owner_id,self.profile.pk)
        self.assertEqual(MarketTrade.objects.count(),1)
        self.assertEqual(self.client.post('/plac_targowy/',{'action':'buy','buy_item_id':item.pk,'expected_price':40}).status_code,404)
        self.assertEqual(MarketTrade.objects.count(),1)
