from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class PlayerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

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

    premium_balance = models.PositiveIntegerField(default=0)
    current_health = models.PositiveIntegerField(default=50)
    health_updated_at = models.DateTimeField(default=timezone.now)
    bot_turn = models.PositiveIntegerField(default=0)

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
            models.CheckConstraint(condition=models.Q(current_energy__gte=0) & models.Q(current_energy__lte=models.F("max_energy")), name="profile_energy_bounds"),
            models.CheckConstraint(condition=models.Q(current_health__lte=models.F("life")), name="profile_health_bounds"),
            models.CheckConstraint(condition=models.Q(ore_balance__gte=0), name="profile_ore_nonnegative"),
            models.CheckConstraint(condition=models.Q(life__gte=1) & models.Q(max_energy__gte=1), name="profile_resource_caps_positive"),
        ]

    # actions time
    action_end_time = models.DateTimeField(null=True, blank=True)

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
    name = models.CharField(max_length=50)
    damage = models.IntegerField(default=0)
    required_strength = models.IntegerField(default=0)
    base_value = models.IntegerField(default=0)


class OwnedItem(models.Model):
    blueprint = models.ForeignKey(ItemBluePrint, on_delete=models.CASCADE)
    owner = models.ForeignKey(
        PlayerProfile, on_delete=models.CASCADE, related_name="inventory"
    )
    is_equipped = models.BooleanField(default=False)
    is_market_listed = models.BooleanField(default=False)
    market_price = models.IntegerField(null=True, blank=True)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        PlayerProfile.objects.create(user=instance)


class MarketTrade(models.Model):
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
