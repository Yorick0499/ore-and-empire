from .barrier import region
"""Bounded contract list; filtering never changes the active assignment or history."""
from .text_search import literal_pattern
from django.db.models import Q
from .models import AdventureTemplate
from .market_browse import bounded_page, pager
from .world_events import reward_snapshot, reward_rates


def adventure_context(profile, params):
    categories=AdventureTemplate._meta.get_field('category').choices
    filters={'q':params.get('q','').strip()[:100],
             'category':params.get('category','') if params.get('category') in dict(categories) else '',
             'access':params.get('access','open') if params.get('access','open') in {'open','all'} else 'open',
             'sort':params.get('sort','level') if params.get('sort','level') in {'level','short','ore','experience'} else 'level'}
    stock=AdventureTemplate.objects.filter(enabled=True,universe=region(profile).universe)
    if filters['q']:stock=stock.filter(Q(name__iregex=literal_pattern(filters['q']))|Q(description__iregex=literal_pattern(filters['q']))|Q(place__iregex=literal_pattern(filters['q'])))
    if filters['category']:stock=stock.filter(category=filters['category'])
    if filters['access']=='open':stock=stock.filter(level__lte=profile.level)
    ordering={'level':('level','pk'),'short':('duration_seconds','level','pk'),'ore':('-ore_reward','level','pk'),'experience':('-experience_reward','level','pk')}
    stock=bounded_page(stock.order_by(*ordering[filters['sort']]),params,'page')
    run=profile.adventures.filter(claimed_at__isnull=True).select_related('template').first()
    quests=[]
    # The event snapshot is identical for all offers on this response.
    rates=reward_rates()
    from .regional_events import context
    regional=context(profile)
    for quest in stock:
        ore,xp,premium,events=reward_snapshot(quest.ore_reward,quest.experience_reward,quest.premium_reward,rates=rates,profile=profile,activity="adventure",target=quest.key,regional_context=regional)
        reason=''
        if run:reason='Najpierw odbierz trwającą wyprawę.'
        elif profile.action_end_time:reason='Najpierw zakończ zmianę i odbierz urobek.'
        elif profile.level<quest.level:reason=f'Wymagany poziom: {quest.level}.'
        elif profile.current_energy<quest.energy_cost:reason=f'Brakuje energii: potrzeba {quest.energy_cost}.'
        quests.append({'quest':quest,'ore':ore,'experience':xp,'premium':premium,'events':events,'available':not reason,'reason':reason})
    return {'run':run,'quests':quests,'adventure_filters':filters,'categories':categories,
            'quest_count':stock.paginator.count,'quest_pager':pager(stock,'page',filters,'Strony zleceń')}
