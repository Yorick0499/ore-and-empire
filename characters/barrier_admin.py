"""Bounded operator projection and audited pause; activation remains the worker's job."""
from django.core.exceptions import PermissionDenied,ValidationError
from django.db import transaction
from django.db.models import Count,Sum
from django.utils import timezone
from .models import World,CampGuild,SleeperRace,SleeperSiege,SleeperStrike,BarrierEvent
from .realms import G1


def authorize(operator):
    from django.contrib.auth.models import User
    if not User.objects.filter(pk=operator.pk,is_active=True,is_superuser=True).exists():raise PermissionDenied('Wymagany aktywny administrator.')


def projection(operator):
    authorize(operator)
    colony=World.objects.filter(is_current=True,configured=True,status='active',universe='GOTHIC_I').first()
    island=World.objects.filter(is_open=True,configured=True,status='active',universe='GOTHIC_II').first()
    race=SleeperRace.objects.filter(colony=colony).select_related('winner').first() if colony else None
    sieges={s.guild_id:s for s in SleeperSiege.objects.filter(race=race)} if race else {}
    totals={r['siege_id']:r for r in SleeperStrike.objects.filter(siege__race=race,damage__gt=0).values('siege_id').annotate(accounts=Count('account_id',distinct=True),damage=Sum('damage'))} if race else {}
    rows=[]
    for guild in CampGuild.objects.filter(world=colony,camp__in=G1).order_by('camp') if colony else []:
        siege=sieges.get(guild.pk);score=totals.get(siege.pk,{}) if siege else {}
        rows.append({'guild':guild,'qualified':guild.level==10,'siege':siege,'accounts':score.get('accounts',0),'damage':score.get('damage',0)})
    plan=None
    if colony and island:
        from .convergence import dry_run
        plan=dry_run(colony.pk,island.pk)
    active=bool(race and race.lease_owner and race.lease_expires_at and race.lease_expires_at>timezone.now())
    return {'race':race,'rows':rows,'plan':plan,'active_lease':active,'events':race.events.order_by('-created_at','-pk')[:40] if race else []}


@transaction.atomic
def set_paused(operator,race_id,paused,expected_state):
    authorize(operator)
    race=SleeperRace.objects.select_for_update().get(pk=race_id)
    if race.state!=expected_state:raise ValidationError('Stan zmienił się. Odśwież panel przed ponowieniem.')
    if race.state=='joined':raise ValidationError('Zakończonego połączenia nie można cofnąć pauzą.')
    if race.lease_owner and race.lease_expires_at and race.lease_expires_at>timezone.now():raise ValidationError('Wykonawca jest aktywny. Poczekaj na zakończenie lub wygaśnięcie dzierżawy.')
    if race.paused!=paused:
        race.paused=paused;race.save(update_fields=['paused'])
        BarrierEvent.objects.create(race=race,kind='paused' if paused else 'unpaused',details={'operator':operator.pk})
    return race
