"""Private projections of existing facts; opening the journal never grants rewards."""
from datetime import timedelta
from django.utils import timezone
from .models import JournalNotice, AdventureRun, MarketTrade, CampQuest, WorldEvent


def sync_notices(profile):
    now = timezone.now()
    facts = []
    for run in AdventureRun.objects.filter(profile=profile, claimed_at__isnull=True, ends_at__lte=now).select_related("template"):
        facts.append((f"adventure:{run.pk}", f"Wyprawa ukończona: {run.public_name}", "adventures_page"))
    for sale in MarketTrade.objects.filter(seller=profile).select_related("blueprint")[:50]:
        facts.append((f"sale:{sale.pk}", f"Sprzedano: {sale.blueprint.name} — {sale.price} rudy", "market_page"))
    for quest in CampQuest.objects.filter(profile=profile, promoted_at__isnull=False)[:20]:
        facts.append((f"promotion:{quest.pk}", f"Awans obozowy: {quest.rank_key}", "camp_page"))
    for event in WorldEvent.objects.filter(world=profile.world, enabled=True, starts_at__gt=now, starts_at__lte=now+timedelta(days=1))[:20]:
        facts.append((f"event:{event.pk}:{event.starts_at.isoformat()}", f"Wkrótce: {event.name}", "events_page"))
    existing = set(JournalNotice.objects.filter(profile=profile, key__in=[f[0] for f in facts]).values_list("key", flat=True))
    JournalNotice.objects.bulk_create([JournalNotice(profile=profile,key=key,title=title[:200],destination=dest) for key,title,dest in facts if key not in existing], ignore_conflicts=True)


def journal_context(request):
    if not request.user.is_authenticated:
        return {}
    if request.resolver_match and request.resolver_match.url_name=='characters_page' and not getattr(request.user,'_server_profile',None):return {}
    profile = request.user.playerprofile
    sync_notices(profile)
    return {"unread_notices": profile.notices.filter(read_at__isnull=True).count()}
