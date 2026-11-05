"""Real old-schema -> current-schema regression, not a fresh DB smoke test."""
from django.db import connection, IntegrityError, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class LegacyResourceMigrationTests(TransactionTestCase):
    def setUp(self):
        super().setUp()
        executor = MigrationExecutor(connection)
        self.latest = executor.loader.graph.leaf_nodes('characters')
        self.old_target = [('characters', '0009_campquest')]
        executor.migrate(self.old_target)
        self.old = executor.loader.project_state(self.old_target).apps

    def tearDown(self):
        MigrationExecutor(connection).migrate(self.latest)
        super().tearDown()

    def make_profile(self, username, **overrides):
        User = self.old.get_model('auth', 'User')
        Profile = self.old.get_model('characters', 'PlayerProfile')
        user = User.objects.create(username=username)
        return Profile.objects.create(user_id=user.pk, **overrides)

    def migrate_forward(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.latest)
        return executor.loader.project_state(self.latest).apps

    def test_legacy_limits_are_normalized_and_valid_progress_survives(self):
        valid = self.make_profile('valid-save', life=70, current_energy=40, max_energy=120,
                                  ore_balance=75, level=4, experience=6000, skill_points=3,
                                  camp='OLD_CAMP', guild='SHADOW')
        bad = self.make_profile('invalid-save', life=-5, current_energy=-20,
                                max_energy=0, ore_balance=-9, experience=1234)
        excessive = self.make_profile('over-cap-save', life=80, current_energy=999,
                                      max_energy=100, ore_balance=900)
        Blueprint = self.old.get_model('characters', 'ItemBluePrint')
        Item = self.old.get_model('characters', 'OwnedItem')
        CampQuest = self.old.get_model('characters', 'CampQuest')
        sword = Blueprint.objects.create(name='Saved sword', damage=20, base_value=80)
        item = Item.objects.create(owner_id=valid.pk, blueprint_id=sword.pk, is_equipped=True)
        quest = CampQuest.objects.create(profile_id=valid.pk, rank_key='GUARD', progress={'hunt:minecrawler': 2})
        apps = self.migrate_forward()
        Profile = apps.get_model('characters', 'PlayerProfile')
        restored = Profile.objects.get(pk=valid.pk)
        self.assertEqual((restored.life, restored.current_health, restored.current_energy, restored.max_energy, restored.ore_balance), (70, 70, 40, 120, 75))
        self.assertEqual((restored.level, restored.experience, restored.skill_points, restored.guild), (4, 6000, 3, 'SHADOW'))
        repaired = Profile.objects.get(pk=bad.pk)
        self.assertEqual((repaired.life, repaired.current_health, repaired.current_energy, repaired.max_energy, repaired.ore_balance, repaired.experience), (1, 1, 0, 1, 0, 1234))
        excessive = Profile.objects.get(pk=excessive.pk)
        self.assertEqual((excessive.current_energy, excessive.ore_balance), (100, 900))
        self.assertTrue(apps.get_model('characters', 'OwnedItem').objects.get(pk=item.pk).is_equipped)
        self.assertEqual(apps.get_model('characters', 'CampQuest').objects.get(pk=quest.pk).progress, {'hunt:minecrawler': 2})
        before = list(Profile.objects.order_by('pk').values())
        self.migrate_forward()
        self.assertEqual(list(Profile.objects.order_by('pk').values()), before)
        for updates in ({'current_energy': -1}, {'current_energy': 121}, {'ore_balance': -1}, {'life': 0}, {'current_health': 71}):
            with self.assertRaises(IntegrityError), transaction.atomic():
                Profile.objects.filter(pk=valid.pk).update(**updates)

    def test_upgrade_from_0010_also_handles_invalid_already_initialized_health(self):
        profile = self.make_profile('partially-upgraded', life=80, max_energy=100, current_energy=500)
        middle = [('characters', '0010_playerprofile_bot_turn_playerprofile_current_health_and_more')]
        executor = MigrationExecutor(connection)
        executor.migrate(middle)
        Profile = executor.loader.project_state(middle).apps.get_model('characters', 'PlayerProfile')
        Profile.objects.filter(pk=profile.pk).update(current_health=999, life=0, max_energy=-5)
        apps = self.migrate_forward()
        repaired = apps.get_model('characters', 'PlayerProfile').objects.get(pk=profile.pk)
        self.assertEqual((repaired.life, repaired.current_health, repaired.current_energy, repaired.max_energy), (1, 1, 1, 1))
