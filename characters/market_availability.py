"""Availability of sellers for public listings and settlement."""

from django.db.models import Q


def available_seller(prefix=''):
    return Q(**{f'{prefix}user__is_active': True, f'{prefix}is_draft': False})


def listings_in(world_ids):
    from .models import OwnedItem

    return OwnedItem.objects.filter(
        available_seller('owner__'), owner__world_id__in=world_ids, is_market_listed=True,
    )
