from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


def default_world_id():
    from .worlds import current_world
    return current_world().pk


class World(models.Model):
    name = models.CharField(max_length=80,default='Górnicza Dolina')
    edition = models.PositiveIntegerField(default=1)
    universe = models.CharField(max_length=20,default='GOTHIC_I')
    rules_version = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=12,default='active',choices=[('active','Aktywny'),('archived','Archiwalny')])
    is_current = models.BooleanField(default=False)
    configured = models.BooleanField(default=False)
    bot_count = models.PositiveSmallIntegerField(default=6)
    created_at = models.DateTimeField(default=timezone.now)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['is_current'],condition=models.Q(is_current=True),name='one_current_world'),models.CheckConstraint(condition=models.Q(bot_count__lte=100),name='world_bot_count_bounds')]


class SchedulerLease(models.Model):
    world=models.OneToOneField(World,on_delete=models.CASCADE,related_name='scheduler_lease')
    owner=models.UUIDField(null=True,blank=True)
    heartbeat_at=models.DateTimeField(default=timezone.now)
    expires_at=models.DateTimeField(default=timezone.now,db_index=True)


class PlayerProfile(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name="characters")
    world = models.ForeignKey(World,on_delete=models.PROTECT,default=default_world_id)

    # camp and guild list
    CAMP_LIST = [
        ("NONE", "Brak przynależności"),
        ("SWAMP_CAMP", "Obóz na bagnie"),
        ("OLD_CAMP", "Stary Obóz"),
        ("NEW_CAMP", "Nowy Obóz"),
    ]

    OLD_CAMP_GUILDS = [
        ("DIGGER", "Kopacz"),
        ("SHADOW", "Cień"),
        ("GUARD", "Strażnik"),
        ("FIRE_MAGE", "Mag Ognia"),
        ("ARCH_FIRE", "Arcymag Ognia"),
        ("BARON", "Magnat"),
    ]

    NEW_CAMP_GUILDS = [
        ("MOLE", "Kret"),
        ("ROGUE", "Szkodnik"),
        ("MERC", "Najemnik"),
        ("WATER_MAGE", "Mag Wody"),
        ("ARCH_WATER", "Arcymag Wody"),
        ("ELITE_MERC", "Gwardzista Lee"),
    ]

    SWAMP_CAMP_GUILDS = [
        ("PICKER", "Zbieracz"),
        ("NOVICE", "Nowicjusz"),
        ("SWAMP_GUARD", "Strażnik świątynny"),
        ("GURU", "Guru"),
        ("ARCH_GURU", "Arcyguru"),
        ("TEMPLAR", "Templariusz bagien"),
    ]

    # main
    camp = models.CharField(max_length=20, choices=CAMP_LIST, default="NONE")
    level = models.IntegerField(default=0)
    guild = models.CharField(max_length=20, default="NONE")

    # exp
    experience = models.IntegerField(default=0)
    skill_points = models.IntegerField(default=0)

    # attributes
    smithing_skill = models.PositiveSmallIntegerField(default=0)
    alchemy_skill = models.PositiveSmallIntegerField(default=0)
    strength = models.IntegerField(default=10)
    dexterity = models.IntegerField(default=10)
    mana = models.IntegerField(default=10)
    life = models.IntegerField(default=50)

    # protection
    weapon_prot = models.IntegerField(default=0)
    arrow_prot = models.IntegerField(default=0)
    fire_prot = models.IntegerField(default=0)
    magic_prot = models.IntegerField(default=0)

    # fighting skills
    onehand_skill = models.IntegerField(default=0)
    twohand_skill = models.IntegerField(default=0)
    bow_skill = models.IntegerField(default=0)
    crossbow_skill = models.IntegerField(default=0)

    # thieving skills
    lockpick_skill = models.IntegerField(default=0)
    pickpock_skill = models.IntegerField(default=0)

    # magici skill
    magic_skill = models.IntegerField(default=0)

    # special skills
    sneaking = models.BooleanField(default=False)
    acrobatics = models.BooleanField(default=False)

    # ore balance
    ore_balance = models.IntegerField(default=50)

    equipment_mana = models.PositiveIntegerField(default=0)
    current_mana = models.PositiveIntegerField(default=10)
    mana_updated_at = models.DateTimeField(default=timezone.now)
    prepared_magic = models.ForeignKey("OwnedItem",null=True,blank=True,on_delete=models.SET_NULL,related_name="prepared_by")
    equipment_health = models.PositiveIntegerField(default=0)
    premium_balance = models.PositiveIntegerField(default=0)
    current_health = models.PositiveIntegerField(default=50)
    health_updated_at = models.DateTimeField(default=timezone.now)
    bot_turn = models.PositiveIntegerField(default=0)
    bot_last_tick = models.DateTimeField(null=True, blank=True, db_index=True)

    # energy_points
    current_energy = models.IntegerField(default=100)
    max_energy = models.IntegerField(default=100)
    energy_updated_at = models.DateTimeField(default=timezone.now)
    is_bot = models.BooleanField(default=False)
    bot_role = models.CharField(
        max_length=10,
        default="hunter",
        choices=[
            ("hunter", "Łowca"),
            ("trader", "Kupiec"),
            ("miner", "Górnik"),
        ],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user","world"],name="one_character_per_account_world"),
            models.CheckConstraint(condition=models.Q(current_energy__gte=0) & models.Q(current_energy__lte=models.F("max_energy")), name="profile_energy_bounds"),
            models.CheckConstraint(condition=models.Q(current_health__lte=models.F("life") + models.F("equipment_health")), name="profile_health_bounds"),
            models.CheckConstraint(condition=models.Q(current_mana__lte=models.F("mana") + models.F("equipment_mana")), name="profile_mana_bounds"),
            models.CheckConstraint(condition=models.Q(ore_balance__gte=0), name="profile_ore_nonnegative"),
            models.CheckConstraint(condition=models.Q(life__gte=1) & models.Q(max_energy__gte=1), name="profile_resource_caps_positive"),
        ]

    # actions time
    action_end_time = models.DateTimeField(null=True, blank=True)

    def refresh_from_db(self,*args,**kwargs):
        super().refresh_from_db(*args,**kwargs)
        if hasattr(self,'_gear_stats_cache'): del self._gear_stats_cache
        if hasattr(self,'_camp_perks'): del self._camp_perks

    @property
    def max_mana(self):
        return self.mana + self.equipment_mana

    @property
    def max_health(self):
        return self.life + self.equipment_health

    @property
    def equipment_stats(self):
        from .equipment import stats_for
        if not hasattr(self, '_gear_stats_cache'):
            self._gear_stats_cache = stats_for(self)
        return self._gear_stats_cache

    @property
    def camp_perks(self):
        if not hasattr(self,'_camp_perks'):
            self._camp_perks=(CampGuild.objects.filter(camp=self.camp,world_id=self.world_id).values('training_level','supply_level','defense_level').first() if self.camp!='NONE' else None) or dict(training_level=0,supply_level=0,defense_level=0)
        return self._camp_perks

    def effective_protection(self, kind='weapon'):
        return getattr(self, kind + '_prot') + self.equipment_stats[kind + '_prot'] + (self.camp_perks['defense_level'] if kind in {'weapon','arrow'} else 0)

    @property
    def camp_tier(self):
        from .camp_progression import BY_RANK
        rank = BY_RANK.get(self.guild)
        return rank.tier if rank and rank.camp == self.camp else 0

    @property
    def guild_name(self):
        from .camp_progression import BY_RANK
        rank = BY_RANK.get(self.guild)
        return rank.name if rank and rank.camp == self.camp else "Bez rangi"

    @property
    def display_name(self):
        names = ("Brann", "Kord", "Mira", "Hagen ze Sztolni", "Ruda", "Silas z Traktu", "Nela", "Jarven", "Falk", "Toran", "Dagna", "Orrik", "Bora", "Velin", "Gerta", "Arvid", "Tessa", "Kurt", "Nordin", "Wolmar")
        if not self.is_bot:
            return self.user.username
        name=names[(self.pk-1)%len(names)]
        group=(self.pk-1)//len(names)
        if group:
            name += " z " + ("Kopalni", "Przełęczy", "Bagien", "Kanionu", "Warty")[(group-1)%5]
            if self.pk>120:
                name += f" {((self.pk-1)//120)+1}"
        return name

    @property
    def training_cost(self):
        return 10-self.camp_perks["training_level"]

    @property
    def required_exp(self):
        n = self.level + 1
        return 250 * n * (n + 1)

    @property
    def is_busy(self):
        from django.utils import timezone

        if self.action_end_time and timezone.now() < self.action_end_time:
            return True
        return self.adventures.filter(claimed_at__isnull=True).exists()


class ItemBluePrint(models.Model):
    name = models.CharField(max_length=120)
    damage = models.IntegerField(default=0)
    required_strength = models.IntegerField(default=0)
    base_value = models.IntegerField(default=0)

    catalog_key = models.SlugField(max_length=100, unique=True, null=True, blank=True)
    kind = models.CharField(max_length=15, default='weapon', choices=[(k,k) for k in ('weapon','armor','ring','amulet','consumable','material','ammo','rune','scroll','quest','misc')])
    weapon_type = models.CharField(max_length=12, default='onehand', choices=[(k,k) for k in ('onehand','twohand','bow','crossbow')])
    damage_type = models.CharField(max_length=8, default='weapon', choices=[(k,k) for k in ('weapon','arrow','fire','magic')])
    required_dexterity = models.PositiveIntegerField(default=0)
    min_level = models.PositiveIntegerField(default=0)
    required_camp = models.CharField(max_length=20, blank=True)
    min_camp_tier = models.PositiveSmallIntegerField(default=0)
    weapon_prot = models.PositiveIntegerField(default=0)
    arrow_prot = models.PositiveIntegerField(default=0)
    fire_prot = models.PositiveIntegerField(default=0)
    magic_prot = models.PositiveIntegerField(default=0)
    strength_bonus = models.PositiveIntegerField(default=0)
    dexterity_bonus = models.PositiveIntegerField(default=0)
    mana_bonus = models.PositiveIntegerField(default=0)
    life_bonus = models.PositiveIntegerField(default=0)
    heal_amount = models.PositiveIntegerField(default=0)
    energy_amount = models.PositiveIntegerField(default=0)
    stackable = models.BooleanField(default=False)
    merchant = models.BooleanField(default=True)
    tradeable = models.BooleanField(default=True)
    source_game = models.CharField(max_length=20, default='adaptation')
    source_url = models.URLField(blank=True)
    original_stats = models.JSONField(default=dict, blank=True)
    art_key = models.CharField(max_length=100, blank=True)

    def save(self,*args,**kwargs):
        old_bonus=type(self).objects.filter(pk=self.pk).values_list('life_bonus','mana_bonus').first() if self.pk else None
        super().save(*args,**kwargs)
        if old_bonus is not None and old_bonus != (self.life_bonus,self.mana_bonus):
            from .equipment import sync_health
            for profile in PlayerProfile.objects.filter(inventory__blueprint=self,inventory__is_equipped=True).distinct():
                sync_health(profile)

    @property
    def original_rows(self):
        names = {'damage':'Obrażenia','requirement':'Wymagany atrybut broni','reach':'Zasięg','cut_damage':'Obrażenia sieczne','blunt_damage':'Obrażenia obuchowe','value':'Cena G1','base_value':'Cena G1','availability':'Najwcześniejszy rozdział G1','weapon_prot':'Ochrona przed bronią','arrow_prot':'Ochrona przed pociskami','fire_prot':'Ochrona przed ogniem','magic_prot':'Ochrona przed magią','life_bonus':'Bonus życia','mana_bonus':'Bonus many','strength_bonus':'Bonus siły','dexterity_bonus':'Bonus zręczności','effect':'Efekt G1','browser_price':'Cena adaptacji (nie G1)'}
        return [(label,self.original_stats[key]) for key,label in names.items() if key in self.original_stats]

    @property
    def kind_name(self):
        return {'weapon':'Broń','armor':'Pancerz','ring':'Pierścień','amulet':'Amulet','consumable':'Pożywienie / mikstura','material':'Materiał / trofeum','ammo':'Amunicja','rune':'Runa','scroll':'Zwój','quest':'Przedmiot fabularny','misc':'Pozostałe'}.get(self.kind,self.kind)

    @property
    def damage_name(self):
        return {'weapon':'broń','arrow':'pociski','fire':'ogień','magic':'magia'}.get(self.damage_type,self.damage_type)

    @property
    def weapon_name(self):
        return {'onehand':'Jednoręczna','twohand':'Dwuręczna','bow':'Łuk','crossbow':'Kusza'}.get(self.weapon_type,self.weapon_type)

    @property
    def magic_supported(self):
        from .magic import BY_CODE
        return self.catalog_key in BY_CODE

    @property
    def equippable(self):
        return self.kind in {'weapon','armor','ring','amulet'}


class OwnedItem(models.Model):
    listed_at = models.DateTimeField(null=True,blank=True,db_index=True)
    blueprint = models.ForeignKey(ItemBluePrint, on_delete=models.CASCADE)
    owner = models.ForeignKey(
        PlayerProfile, on_delete=models.CASCADE, related_name="inventory"
    )
    quantity = models.PositiveIntegerField(default=1)
    upgrade_level = models.PositiveSmallIntegerField(default=0)
    origin = models.CharField(max_length=12, default="legacy", choices=[(v,v) for v in ("legacy","loot","merchant","craft","reward","admin")])

    @property
    def can_salvage(self):
        return self.quantity == 1 and self.blueprint.equippable and (self.origin == "loot" or (self.origin == "legacy" and (self.blueprint.catalog_key or "").startswith("colony-loot-")))

    @property
    def effective_stats(self):
        from .enhancements import effective_stats
        return effective_stats(self)

    @property
    def upgrade_cost(self):
        from .enhancements import upgrade_cost
        return upgrade_cost(self)

    @property
    def display_name(self):
        return self.blueprint.name + (f" · {self.quality_name}" if self.upgrade_level else "")

    @property
    def quality(self):
        from .enhancements import QUALITY_RANKS
        return QUALITY_RANKS[(self.upgrade_level+1)//2]

    @property
    def quality_name(self):
        return self.quality['name']

    equipped_slot = models.CharField(max_length=10, blank=True)
    is_equipped = models.BooleanField(default=False)
    is_market_listed = models.BooleanField(default=False)
    market_price = models.IntegerField(null=True, blank=True)

    @property
    def slot_name(self):
        return {'weapon':'Broń','armor':'Pancerz','amulet':'Amulet','ring1':'Pierścień I','ring2':'Pierścień II'}.get(self.equipped_slot,'Plecak')

    def save(self, *args, **kwargs):
        previous = type(self).objects.filter(pk=self.pk).values('owner_id','is_equipped').first() if self.pk else None
        was_equipped = bool(previous and previous['is_equipped'])
        if not self.is_equipped:
            self.equipped_slot = ''
        elif not self.equipped_slot:
            self.equipped_slot = {'ring': 'ring1', 'amulet': 'amulet', 'armor': 'armor'}.get(self.blueprint.kind, 'weapon')
        if kwargs.get('update_fields') and ('is_equipped' in kwargs['update_fields'] or 'equipped_slot' in kwargs['update_fields']):
            kwargs['update_fields'] = list(set(kwargs['update_fields']) | {'equipped_slot'})
        super().save(*args, **kwargs)
        if self.is_equipped or was_equipped:
            from .equipment import sync_health
            ids={self.owner_id}
            if was_equipped: ids.add(previous['owner_id'])
            for profile in PlayerProfile.objects.filter(pk__in=ids): sync_health(profile)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gte=1), name='owned_quantity_positive'),
            models.CheckConstraint(condition=models.Q(upgrade_level__lte=10) & (models.Q(upgrade_level=0) | models.Q(quantity=1)), name='owned_upgrade_bounds'),
            models.UniqueConstraint(fields=['owner','equipped_slot'], condition=models.Q(is_equipped=True), name='one_equipment_per_slot'),
            models.CheckConstraint(condition=(models.Q(is_equipped=False, equipped_slot='') | (models.Q(is_equipped=True) & models.Q(equipped_slot__in=['weapon','armor','amulet','ring1','ring2']))), name='equipment_slot_consistent'),
        ]


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not kwargs.get("raw",False):
        profile = PlayerProfile.objects.create(user=instance)
        from .economic_ledger import record_opening
        record_opening(profile)


class MarketTrade(models.Model):
    quantity = models.PositiveIntegerField(null=True,blank=True)
    """Append-only trade facts; item ownership may change after the transaction."""

    blueprint = models.ForeignKey(ItemBluePrint, on_delete=models.PROTECT)
    seller = models.ForeignKey(
        PlayerProfile, on_delete=models.PROTECT, related_name="sales"
    )
    buyer = models.ForeignKey(
        PlayerProfile, on_delete=models.PROTECT, related_name="purchases"
    )
    price = models.PositiveIntegerField()
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(price__gt=0), name="trade_positive_price"
            ),
            models.CheckConstraint(
                condition=~models.Q(seller=models.F("buyer")),
                name="trade_distinct_players",
            ),
        ]


class BossAttempt(models.Model):
    profile = models.ForeignKey(
        PlayerProfile, on_delete=models.CASCADE, related_name="boss_attempts"
    )
    boss_key = models.CharField(max_length=40)
    created_at = models.DateTimeField(default=timezone.now)
    won = models.BooleanField()
    experience_reward = models.PositiveIntegerField(default=0)
    ore_reward = models.PositiveIntegerField(default=0)
    combat_log = models.JSONField(default=list)

    class Meta:
        ordering = ["-created_at", "-pk"]
        indexes = [models.Index(fields=["profile", "boss_key", "-created_at"])]


class BotDecision(models.Model):
    """Policy observation and actual outcome; no usernames or credentials."""

    profile = models.ForeignKey(PlayerProfile, on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    schema_version = models.PositiveSmallIntegerField(default=1)
    policy_version = models.CharField(max_length=40,default="legacy-unknown")
    reason = models.CharField(max_length=40,default="legacy-unspecified")
    experience_delta = models.IntegerField(default=0)
    role = models.CharField(max_length=10)
    observation = models.JSONField()
    action = models.CharField(max_length=20)
    target_id = models.PositiveBigIntegerField(null=True)
    success = models.BooleanField()
    ore_delta = models.IntegerField()
    energy_delta = models.IntegerField()
    health_delta = models.IntegerField(default=0)
    premium_delta = models.IntegerField(default=0)

    class Meta:
        ordering = ["-created_at", "-pk"]
        indexes = [models.Index(fields=["profile","-created_at","-id"])]


class CampQuest(models.Model):
    profile = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="camp_quests")
    rank_key = models.CharField(max_length=20)
    accepted_at = models.DateTimeField(default=timezone.now)
    progress = models.JSONField(default=dict)
    promoted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["profile", "rank_key"], name="unique_camp_quest")]


class AdventureTemplate(models.Model):
    key = models.SlugField(unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    level = models.PositiveIntegerField(default=0)
    duration_seconds = models.PositiveIntegerField(default=60)
    energy_cost = models.PositiveIntegerField(default=5)
    ore_reward = models.PositiveIntegerField(default=10)
    experience_reward = models.PositiveIntegerField(default=50)
    premium_reward = models.PositiveIntegerField(default=1)
    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ["level", "pk"]
        constraints = [models.CheckConstraint(condition=models.Q(duration_seconds__gte=1), name="adventure_duration_positive")]


class WorldEvent(models.Model):
    world = models.ForeignKey(World,on_delete=models.PROTECT,default=default_world_id)
    key = models.SlugField(unique=True, max_length=100)
    name = models.CharField(max_length=100)
    description = models.TextField()
    kind = models.CharField(max_length=12, choices=[("seasonal", "Sezonowy"), ("holiday", "Świąteczny"), ("random", "Losowy"), ("manual", "Specjalny")], default="manual")
    starts_at = models.DateTimeField(db_index=True)
    ends_at = models.DateTimeField(db_index=True)
    enabled = models.BooleanField(default=True)
    ore_percent = models.PositiveIntegerField(default=100)
    experience_percent = models.PositiveIntegerField(default=100)
    premium_bonus = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["starts_at", "pk"]
        constraints = [models.CheckConstraint(condition=models.Q(ends_at__gt=models.F("starts_at")), name="event_end_after_start")]


class AdventureRun(models.Model):
    profile = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="adventures")
    template = models.ForeignKey(AdventureTemplate, on_delete=models.PROTECT)
    started_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField()
    claimed_at = models.DateTimeField(null=True, blank=True)
    ore_reward = models.PositiveIntegerField()
    experience_reward = models.PositiveIntegerField()
    premium_reward = models.PositiveIntegerField()
    event_names = models.JSONField(default=list)

    class Meta:
        ordering = ["-started_at", "-pk"]
        constraints = [models.UniqueConstraint(fields=["profile"], condition=models.Q(claimed_at__isnull=True), name="one_unclaimed_adventure")]


class PremiumEntry(models.Model):
    profile = models.ForeignKey(PlayerProfile, on_delete=models.PROTECT, related_name="premium_entries")
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    amount = models.IntegerField()
    balance_after = models.PositiveIntegerField()
    reason = models.CharField(max_length=120)
    reference = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        constraints = [models.CheckConstraint(condition=~models.Q(amount=0), name="premium_entry_nonzero")]


class StoreProduct(models.Model):
    key = models.SlugField(unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    kind = models.CharField(max_length=10, choices=[("weapon", "Oręż"), ("energy", "Energia"), ("health", "Zdrowie")])
    price = models.PositiveIntegerField()
    level = models.PositiveIntegerField(default=0)
    effect = models.PositiveIntegerField(default=0)
    blueprint = models.ForeignKey(ItemBluePrint, null=True, blank=True, on_delete=models.PROTECT)
    enabled = models.BooleanField(default=True)
    art_key = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["price", "pk"]
        constraints = [models.CheckConstraint(condition=models.Q(price__gte=1), name="store_price_positive")]


class StorePurchase(models.Model):
    profile = models.ForeignKey(PlayerProfile, on_delete=models.PROTECT, related_name="store_purchases")
    product = models.ForeignKey(StoreProduct, on_delete=models.PROTECT)
    request_key = models.UUIDField()
    created_at = models.DateTimeField(default=timezone.now)
    price = models.PositiveIntegerField()
    effect = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["profile", "request_key"], name="unique_store_request")]


class AdminAction(models.Model):
    actor = models.ForeignKey(User, on_delete=models.PROTECT)
    profile = models.ForeignKey(PlayerProfile, on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now)
    action = models.CharField(max_length=30)
    details = models.JSONField(default=dict)

    class Meta:
        ordering = ["-created_at", "-pk"]


class TavernTopic(models.Model):
    author = models.ForeignKey(PlayerProfile, on_delete=models.PROTECT)
    title = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now, db_index=True)
    locked = models.BooleanField(default=False)

    class Meta:
        ordering = ['-updated_at', '-pk']


class TavernMessage(models.Model):
    topic = models.ForeignKey(TavernTopic, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(PlayerProfile, on_delete=models.PROTECT, related_name='tavern_messages')
    body = models.TextField(max_length=1000)
    created_at = models.DateTimeField(default=timezone.now)
    reply_to = models.OneToOneField('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='bot_response')
    decision = models.ForeignKey(BotDecision, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['created_at', 'pk']


class StoryQuest(models.Model):
    """Editable next-acceptance definition; accepted runs retain a full snapshot."""
    key = models.SlugField(unique=True)
    version = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=120)
    description = models.TextField()
    chapter = models.PositiveSmallIntegerField(default=1)
    level = models.PositiveIntegerField(default=0)
    camp = models.CharField(max_length=20, blank=True, choices=PlayerProfile.CAMP_LIST)
    universe = models.CharField(max_length=30, default='GOTHIC_I')
    prerequisites = models.JSONField(default=list, blank=True)
    any_prerequisites = models.JSONField(default=list, blank=True)
    required_choices = models.JSONField(default=dict, blank=True)
    objectives = models.JSONField(default=list)
    rewards = models.JSONField(default=dict)
    energy_cost = models.PositiveIntegerField(default=0)
    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ['chapter', 'level', 'pk']

    def clean(self):
        from .story_quests import validate_definition
        validate_definition(self)


class StoryRun(models.Model):
    profile = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name='story_runs')
    quest = models.ForeignKey(StoryQuest, on_delete=models.PROTECT)
    snapshot = models.JSONField()
    status = models.CharField(max_length=10, choices=[('accepted', 'Przyjęte'), ('active', 'W toku'), ('ready', 'Gotowe'), ('claimed', 'Zakończone')], default='accepted')
    progress = models.JSONField(default=dict)
    choices = models.JSONField(default=dict)
    accepted_at = models.DateTimeField(default=timezone.now)
    activated_at = models.DateTimeField(null=True, blank=True)
    claimed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-accepted_at', '-pk']
        constraints = [
            models.UniqueConstraint(fields=['profile', 'quest'], name='unique_story_run'),
            models.UniqueConstraint(fields=['profile'], condition=~models.Q(status='claimed'), name='one_open_story_run'),
        ]


class LootTable(models.Model):
    key = models.CharField(max_length=60, unique=True)
    version = models.PositiveIntegerField(default=1)
    entries = models.JSONField(default=list)
    enabled = models.BooleanField(default=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        entries = self.entries
        valid = isinstance(entries,list) and len(entries) <= 20
        if valid:
            for e in entries:
                if not isinstance(e,dict) or type(e.get('weight')) is not int or not 1 <= e['weight'] <= 10000 or type(e.get('blueprint')) is not int or not ItemBluePrint.objects.filter(pk=e['blueprint']).exists() or not 1 <= e.get('min',1) <= e.get('max',1) <= 100:
                    valid = False
                    break
        if not valid or sum(e['weight'] for e in entries) > 10000:
            raise ValidationError('Niepoprawna tabela łupu; wagi muszą sumować się do najwyżej 10000.')


class BattleRecord(models.Model):
    combat_details = models.JSONField(default=dict)
    profile = models.ForeignKey(PlayerProfile, on_delete=models.PROTECT, related_name='battles')
    request_key = models.UUIDField()
    monster_key = models.CharField(max_length=60)
    location_key = models.CharField(max_length=60)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    won = models.BooleanField()
    combat_log = models.JSONField(default=list)
    experience = models.PositiveIntegerField(default=0)
    ore = models.PositiveIntegerField(default=0)
    loot = models.JSONField(default=list)
    loot_version = models.PositiveIntegerField(default=0)
    boss_attempt = models.OneToOneField(BossAttempt, null=True, blank=True, on_delete=models.PROTECT)

    class Meta:
        ordering = ['-created_at','-pk']
        constraints = [models.UniqueConstraint(fields=['profile','request_key'], name='one_battle_request')]


class ContentPack(models.Model):
    key = models.SlugField()
    game = models.CharField(max_length=30)
    version = models.PositiveIntegerField()
    sha256 = models.CharField(max_length=64)
    item_count = models.PositiveIntegerField()
    installed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['key','game','version'],name='unique_content_pack_version')]


class EconomicEntry(models.Model):
    profile = models.ForeignKey(PlayerProfile,on_delete=models.PROTECT,related_name='economic_entries')
    resource = models.CharField(max_length=8,choices=[('ore','Ruda'),('shards','Odłamki')])
    amount = models.IntegerField()
    balance_after = models.PositiveIntegerField()
    category = models.CharField(max_length=10,choices=[(x,x) for x in ('opening','source','sink','transfer','admin')])
    operation = models.CharField(max_length=50)
    reference = models.UUIDField()
    created_at = models.DateTimeField(default=timezone.now,db_index=True)

    class Meta:
        ordering = ['-created_at','-pk']
        constraints = [models.UniqueConstraint(fields=['profile','resource','reference'],name='unique_economic_reference'),models.CheckConstraint(condition=~models.Q(amount=0),name='economic_nonzero')]


class EnergyRefill(models.Model):
    profile = models.ForeignKey(PlayerProfile,on_delete=models.PROTECT,related_name='energy_refills')
    created_at = models.DateTimeField(default=timezone.now,db_index=True)
    reference = models.CharField(max_length=100,unique=True)


@receiver(post_delete,sender=OwnedItem)
def equipped_item_removed(sender,instance,**kwargs):
    if instance.is_equipped:
        profile=PlayerProfile.objects.filter(pk=instance.owner_id).first()
        if profile:
            from .equipment import sync_health
            sync_health(profile)


class BotDailySummary(models.Model):
    day = models.DateField()
    profile = models.ForeignKey(PlayerProfile,on_delete=models.PROTECT)
    decisions = models.PositiveIntegerField(default=0)
    successes = models.PositiveIntegerField(default=0)
    experience_delta = models.BigIntegerField(default=0)
    ore_delta = models.BigIntegerField(default=0)
    premium_delta = models.BigIntegerField(default=0)
    actions = models.JSONField(default=dict)
    schema_version = models.PositiveSmallIntegerField(default=1)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['day','profile'],name='unique_bot_daily_summary')]
        indexes=[models.Index(fields=['day','profile'])]


class CampGuild(models.Model):
    world = models.ForeignKey(World,on_delete=models.PROTECT,default=default_world_id)
    camp = models.CharField(max_length=20,choices=PlayerProfile.CAMP_LIST[1:])
    experience = models.PositiveIntegerField(default=0)
    level = models.PositiveSmallIntegerField(default=1)
    treasury = models.PositiveIntegerField(default=0)
    training_level = models.PositiveSmallIntegerField(default=0)
    supply_level = models.PositiveSmallIntegerField(default=0)
    defense_level = models.PositiveSmallIntegerField(default=0)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['world','camp'],name='one_camp_guild_per_world'),models.CheckConstraint(condition=models.Q(camp__in=['OLD_CAMP','NEW_CAMP','SWAMP_CAMP']),name='valid_camp_guild'),models.CheckConstraint(condition=models.Q(training_level__lte=3,supply_level__lte=3,defense_level__lte=3,level__gte=1,level__lte=10),name='camp_guild_upgrade_bounds')]
    @property
    def name(self):return dict(PlayerProfile.CAMP_LIST)[self.camp]


class CampProject(models.Model):
    guild = models.ForeignKey(CampGuild,on_delete=models.PROTECT,related_name='projects')
    day = models.DateField()
    title = models.CharField(max_length=120)
    objectives = models.JSONField()
    progress = models.JSONField(default=dict)
    experience_reward = models.PositiveIntegerField(default=30)
    treasury_reward = models.PositiveIntegerField(default=50)
    completed_at = models.DateTimeField(null=True,blank=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['guild','day'],name='one_camp_project_per_day')]


class CampContribution(models.Model):
    guild = models.ForeignKey(CampGuild,on_delete=models.PROTECT)
    profile = models.ForeignKey(PlayerProfile,on_delete=models.PROTECT)
    project = models.ForeignKey(CampProject,null=True,blank=True,on_delete=models.PROTECT)
    source = models.UUIDField()
    kind = models.CharField(max_length=30)
    amount = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(default=timezone.now,db_index=True)
    @property
    def kind_name(self):
        return {'mine':'Zmiana w kopalni','hunt':'Ochrona szlaków','donation':'Wpłata rudy','upgrade:training':'Rozwój szkoły','upgrade:supply':'Rozwój magazynu','upgrade:defense':'Rozwój wart'}.get(self.kind,self.kind)

    class Meta:
        ordering=['-created_at','-pk']
        constraints=[models.UniqueConstraint(fields=['profile','source'],name='one_camp_contribution_request')]


class CampRaid(models.Model):
    guild = models.ForeignKey(CampGuild,on_delete=models.PROTECT,related_name='raids')
    day = models.DateField()
    name = models.CharField(max_length=120)
    art_key = models.CharField(max_length=60)
    maximum_health = models.PositiveIntegerField()
    health = models.PositiveIntegerField()
    attack = models.PositiveIntegerField()
    protection = models.PositiveIntegerField()
    minimum_level = models.PositiveSmallIntegerField(default=3)
    completed_at = models.DateTimeField(null=True,blank=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['guild','day'],name='one_camp_raid_per_day'),models.CheckConstraint(condition=models.Q(health__lte=models.F('maximum_health'),maximum_health__gte=1),name='camp_raid_health_bounds')]


class CampRaidStrike(models.Model):
    raid = models.ForeignKey(CampRaid,on_delete=models.PROTECT,related_name='strikes')
    profile = models.ForeignKey(PlayerProfile,on_delete=models.PROTECT)
    request_key = models.UUIDField()
    damage = models.PositiveIntegerField()
    health_cost = models.PositiveIntegerField()
    mana_cost = models.PositiveIntegerField(default=0)
    casts = models.PositiveIntegerField(default=0)
    log = models.JSONField(default=list)
    created_at = models.DateTimeField(default=timezone.now,db_index=True)
    class Meta:
        ordering=['-created_at','-pk']
        constraints=[models.UniqueConstraint(fields=['profile','request_key'],name='one_camp_raid_strike_request')]
        indexes=[models.Index(fields=['raid','profile','-created_at'])]


class CampRaidReward(models.Model):
    raid = models.ForeignKey(CampRaid,on_delete=models.PROTECT)
    profile = models.ForeignKey(PlayerProfile,on_delete=models.PROTECT)
    ore = models.PositiveIntegerField(default=10)
    experience = models.PositiveIntegerField(default=50)
    premium = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(default=timezone.now)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['raid','profile'],name='one_camp_raid_reward')]


class PersonalChallenge(models.Model):
    profile=models.ForeignKey(PlayerProfile,on_delete=models.PROTECT,related_name='challenges')
    cadence=models.CharField(max_length=8)
    period=models.DateField()
    camp=models.CharField(max_length=20)
    kind=models.CharField(max_length=12)
    required=models.PositiveIntegerField()
    progress=models.PositiveIntegerField(default=0)
    ore=models.PositiveIntegerField()
    experience=models.PositiveIntegerField()
    premium=models.PositiveIntegerField()
    reputation=models.PositiveIntegerField()
    claimed_at=models.DateTimeField(null=True,blank=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['profile','cadence','period'],name='one_personal_challenge_period')]


class CampReputation(models.Model):
    @property
    def camp_name(self):return dict(PlayerProfile.CAMP_LIST).get(self.camp,self.camp)
    profile=models.ForeignKey(PlayerProfile,on_delete=models.PROTECT)
    camp=models.CharField(max_length=20)
    value=models.PositiveIntegerField(default=0)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['profile','camp'],name='one_reputation_per_camp')]


class PlayerAchievement(models.Model):
    profile=models.ForeignKey(PlayerProfile,on_delete=models.PROTECT,related_name='achievements')
    key=models.CharField(max_length=30)
    progress=models.PositiveIntegerField(default=0)
    completed_at=models.DateTimeField(null=True,blank=True)
    claimed_at=models.DateTimeField(null=True,blank=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['profile','key'],name='one_player_achievement')]


class CraftRecipe(models.Model):
    key=models.SlugField(unique=True)
    name=models.CharField(max_length=100)
    discipline=models.CharField(max_length=12,choices=[('smithing','Kowalstwo'),('alchemy','Alchemia')])
    skill=models.PositiveSmallIntegerField(default=1)
    level=models.PositiveSmallIntegerField(default=0)
    fee=models.PositiveIntegerField()
    ingredients=models.JSONField()
    output=models.ForeignKey(ItemBluePrint,on_delete=models.PROTECT)
    quantity=models.PositiveSmallIntegerField(default=1)
    enabled=models.BooleanField(default=True)


class CraftRecord(models.Model):
    profile=models.ForeignKey(PlayerProfile,on_delete=models.PROTECT,related_name='crafts')
    recipe=models.ForeignKey(CraftRecipe,on_delete=models.PROTECT)
    request_key=models.UUIDField()
    snapshot=models.JSONField()
    created_at=models.DateTimeField(default=timezone.now)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['profile','request_key'],name='one_craft_request')]


class MarketEvent(models.Model):
    profile=models.ForeignKey(PlayerProfile,on_delete=models.PROTECT)
    item=models.ForeignKey(OwnedItem,null=True,blank=True,on_delete=models.SET_NULL)
    blueprint=models.ForeignKey(ItemBluePrint,on_delete=models.PROTECT)
    action=models.CharField(max_length=20)
    price=models.PositiveIntegerField(default=0)
    quantity=models.PositiveIntegerField(default=1)
    reason=models.CharField(max_length=40,blank=True)
    created_at=models.DateTimeField(default=timezone.now,db_index=True)
    class Meta:
        ordering=['-created_at','-pk']


class JournalNotice(models.Model):
    profile = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name="notices")
    key = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    destination = models.CharField(max_length=40)
    created_at = models.DateTimeField(default=timezone.now)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        constraints = [models.UniqueConstraint(fields=["profile", "key"], name="unique_private_notice")]


class CampaignCompletion(models.Model):
    profile = models.OneToOneField(PlayerProfile, on_delete=models.PROTECT, related_name="campaign_completion")
    battle = models.OneToOneField(BossAttempt, on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now)
    snapshot = models.JSONField(default=dict)

class EditionConclusion(models.Model):
    world = models.OneToOneField(World, on_delete=models.PROTECT, related_name="conclusion")
    operator = models.ForeignKey("auth.User", on_delete=models.PROTECT)
    created_at = models.DateTimeField(default=timezone.now)
    snapshot = models.JSONField(default=dict)


class EquipmentWork(models.Model):
    profile = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name='equipment_work')
    request_key = models.UUIDField()
    item_id_snapshot = models.PositiveIntegerField()
    action = models.CharField(max_length=12)
    snapshot = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['profile','request_key'], name='equipment_work_request')]


class FrontierProgress(models.Model):
    profile = models.OneToOneField(PlayerProfile, on_delete=models.CASCADE, related_name='frontier')
    unlocked = models.PositiveIntegerField(default=1)
    wins = models.PositiveIntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)


class FrontierRecord(models.Model):
    profile = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, related_name='patrols')
    request_key = models.UUIDField()
    depth = models.PositiveIntegerField()
    season = models.CharField(max_length=7, db_index=True)
    won = models.BooleanField(default=False)
    points = models.PositiveIntegerField(default=0)
    snapshot = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['profile','request_key'], name='frontier_request')]
        ordering = ['-created_at','-pk']
        indexes = [models.Index(fields=['profile','season'], name='frontier_profile_season')]
