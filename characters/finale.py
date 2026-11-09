"""Personal finale never ends a server. Only its operator may seal a snapshot."""
from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError
from .models import CampaignCompletion, EditionConclusion, PlayerProfile, World, AdminAction
from .worlds import current_world
from .realms import camps as realm_camps


def finale_ready(profile):
    return profile.level >= 30 and profile.camp != "NONE" and profile.story_runs.filter(quest__key="ritual-ready", status="claimed").exists()


def record_completion(profile, attempt):
    if not attempt.won or attempt.profile_id != profile.pk or attempt.boss_key != "sleeper_sanctum" or not finale_ready(profile):
        return False
    row, _ = CampaignCompletion.objects.get_or_create(profile=profile, defaults={"battle":attempt,"snapshot":{
        "name":profile.display_name,"camp":profile.camp,"level":profile.level,"experience":profile.experience,
        "bot":profile.is_bot,"world_name":profile.world.name,"edition":profile.world.edition,
        "rules_version":profile.world.rules_version,"finale_version":1}})
    return row


@transaction.atomic
def conclude_edition(operator, world_id, confirmation):
    from django.contrib.auth.models import User
    operator=User.objects.get(pk=operator.pk)
    if not operator.is_active or not operator.is_superuser:raise PermissionDenied
    world = World.objects.select_for_update().get(pk=current_world().pk)
    if world.pk != world_id or confirmation != world.name:raise ValidationError("Przepisz nazwę bieżącego świata.")
    existing = EditionConclusion.objects.filter(world=world).first()
    if existing:return existing
    if not CampaignCompletion.objects.filter(profile__world=world,profile__is_bot=False).exists():
        raise ValidationError("Najpierw przynajmniej jeden gracz musi ukończyć finał.")
    population = PlayerProfile.objects.filter(world=world,user__is_active=True,user__is_staff=False).select_related("user").order_by("-level","-experience","pk")
    rankings = [{"id":p.pk,"name":p.display_name,"camp":p.camp,"level":p.level,"experience":p.experience,"is_bot":p.is_bot} for p in population]
    camp_rankings = sorted([{"name":label,"experience":sum(p["experience"] for p in rankings if p["camp"]==camp),"residents":sum(p["camp"]==camp for p in rankings)} for camp,label in PlayerProfile.CAMP_LIST if camp in realm_camps(world)],key=lambda row:-row["experience"])
    result = EditionConclusion.objects.create(world=world,operator=operator,snapshot={"name":world.name,"edition":world.edition,"rules_version":world.rules_version,"rankings":rankings,"camp_rankings":camp_rankings,"finishers":list(CampaignCompletion.objects.filter(profile__world=world).values_list("profile_id",flat=True))})
    AdminAction.objects.create(actor=operator,profile=operator.playerprofile,action="conclude_edition",details={"world":world.pk,"edition":world.edition,"rules_version":world.rules_version})
    return result
