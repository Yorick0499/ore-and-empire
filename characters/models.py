from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class PlayerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # main
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

    # energy_points
    current_energy = models.IntegerField(default=100)
    max_energy = models.IntegerField(default=100)

    # actions time
    action_end_time = models.DateTimeField(null=True, blank=True)

    @property
    def required_exp(self):
        n = self.level + 1
        return 250 * n * (n + 1)

    @property
    def is_busy(self):
        from django.utils import timezone

        if self.action_end_time and timezone.now() < self.action_end_time:
            return True
        return False


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        PlayerProfile.objects.create(user=instance)
