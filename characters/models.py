from django.db import models
from django.contrib.auth.models import User


class PlayerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # main
    GUILD_LIST = [
        ("NONE", "Skazaniec"),
        ("OLD_CAMP", "Stary Obóz"),
        ("NEW_CAMP", "Nowy Obóz"),
    ]
    guild = models.CharField(max_length=20)
    level = models.IntegerField(default=0)

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

    @property
    def required_exp(self):
        return (self.level + 0.5) * 100
