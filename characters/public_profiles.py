"""Read-only character cards and the six visible equipment slots."""
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_safe

from .barrier import region
from .models import OwnedItem, PlayerProfile
from .realms import open_worlds


EQUIPMENT = (
    ('amulet', 'Amulet', '◇'),
    ('armor', 'Pancerz', '⬡'),
    ('ring1', 'Pierścień I', '○'),
    ('weapon', 'Broń', '†'),
    ('ring2', 'Pierścień II', '○'),
    ('belt', 'Pas', '═'),
)

ITEM_STATS = (
    ('damage', 'Obrażenia'),
    ('weapon_prot', 'Ochrona przed bronią'),
    ('arrow_prot', 'Ochrona przed pociskami'),
    ('fire_prot', 'Ochrona przed ogniem'),
    ('magic_prot', 'Ochrona przed magią'),
    ('strength_bonus', 'Siła'),
    ('dexterity_bonus', 'Zręczność'),
    ('mana_bonus', 'Mana'),
    ('life_bonus', 'Życie'),
)


@require_safe
def character_profile(request, character_id):
    equipped = OwnedItem.objects.filter(is_equipped=True).select_related('blueprint')
    subject = get_object_or_404(
        PlayerProfile.objects.filter(
            world__in=open_worlds(), user__is_active=True, user__is_staff=False, is_draft=False,
        ).select_related('world', 'origin_world', 'visiting_world', 'faction_membership__rank_progress')
        .prefetch_related(Prefetch('inventory', queryset=equipped, to_attr='public_equipment')),
        pk=character_id,
    )
    by_slot = {item.equipped_slot: item for item in subject.public_equipment}
    slots = []
    for key, label, symbol in EQUIPMENT:
        item = by_slot.get(key)
        values = item.effective_stats if item else {}
        slots.append({'key': key, 'label': label, 'symbol': symbol, 'item': item,
                      'stats': [(name, values[stat]) for stat, name in ITEM_STATS if values.get(stat)]})
    name = subject.display_name if subject.is_bot else subject.name or f'Mieszkaniec #{subject.pk}'
    return render(request, 'characters/public_profile.html', {
        'character_name': name,
        'character': subject,
        'character_origin': subject.origin_world or subject.world,
        'character_region': region(subject),
        'slots': slots,
    })
