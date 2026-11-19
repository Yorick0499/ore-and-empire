"""Paid, time-based Khorinis assignments used by the native rank trials."""

DUTIES = {
    'service': (3, 45, 16, 120, 350, (
        ('city', 'Warta miejska', 'Koszary w Khorinis', 'watch'),
        ('goods', 'Dostawa zapasów', 'Port Khorinis', 'delivery'),
        ('fields', 'Pomoc przy żniwach', 'Farma Onara', 'supply'),
    )),
    'route': (5, 60, 20, 190, 650, (
        ('patrol', 'Patrol szlaku kupców', 'Trakt do Martwej Harpii', 'watch'),
        ('pilgrims', 'Eskorta pielgrzymów', 'Klasztor Innosa', 'delivery'),
        ('convoy', 'Konwój farm', 'Farma Onara', 'supply'),
    )),
    'frontier': (11, 90, 25, 290, 1100, (
        ('port', 'Nocna warta portowa', 'Port Khorinis', 'watch'),
        ('coast', 'Ubezpieczenie rybaków', 'Wybrzeże Khorinis', 'scout'),
        ('forest', 'Daleki zwiad leśny', 'Mroczny las Khorinis', 'scout'),
    )),
}

RANK_DUTIES = (
    None,
    ('duty:service', 3, 'Odbierz trzy zlecenia służby w Khorinis'),
    ('duty:route', 7, 'Odbierz zlecenia ochrony szlaków'),
    ('duty:frontier', 10, 'Odbierz zlecenia dalekiej warty'),
)


def duty_prefix(stage):
    return f'k2-duty-{stage}-'


def duty_stage(key):
    for stage in DUTIES:
        if key.startswith(duty_prefix(stage)):
            return stage
    return None


def seed_duties(stage=None):
    from .models import AdventureTemplate
    stages = DUTIES.items() if stage is None else ((stage, DUTIES[stage]),)
    for stage, (level, minutes, energy, ore, experience, assignments) in stages:
        for key, name, place, category in assignments:
            AdventureTemplate.objects.get_or_create(
                key=duty_prefix(stage) + key,
                defaults={'universe': 'GOTHIC_II', 'category': category, 'name': name, 'place': place,
                          'description': 'Opłacana służba wspólnoty. Odbiór po powrocie zalicza tę pracę do aktywnej próby awansu.',
                          'level': level, 'duration_seconds': minutes * 60, 'energy_cost': energy,
                          'ore_reward': ore, 'experience_reward': experience, 'premium_reward': 0},
            )
