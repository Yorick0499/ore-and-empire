"""Public colony life: real action facts and bounded, rule-based tavern replies."""
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from .models import PlayerProfile, BotDecision, TavernTopic, TavernMessage

ACTION_NAMES = {
    'ammo':'uzupełnił amunicję u kupca',
    'improve':'ulepszył wyposażenie w kuźni', 'salvage':'odzyskał pył z łupów', 'patrol':'podjął wartę za Przełęczą',
    'craft':'wytworzył przedmiot z materiałów','craft_material':'kupił materiały warsztatowe','craft_learn':'uczył się rzemiosła',
    'market_buy':'kupił potrzebne zapasy na targu','market_reprice':'obniżył cenę zalegającej oferty','market_cancel':'wycofał niesprzedany towar','market_sell':'upłynnił niesprzedane zapasy',
    'raid_strike':'wsparł wspólną wyprawę obozu','camp_donate':'wpłacił rudę do wspólnego skarbca','challenge_claim':'rozliczył osobisty przydział',
    'consume': 'zużył zapasy z plecaka',
    'story_accept': 'przyjął zadanie fabularne', 'story_start': 'rozpoczął zadanie fabularne',
    'story_claim': 'zakończył zadanie fabularne', 'story_talk': 'odbył rozmowę w ramach zadania',
    'story_travel': 'wyruszył w podróż fabularną',
    'mine': 'rozpoczął zmianę w kopalni', 'claim': 'odebrał wydobytą rudę',
    'hunt': 'wrócił z polowania', 'boss': 'podjął wyprawę na bossa',
    'train': 'trenował u nauczyciela', 'equip': 'zmienił oręż',
    'buy': 'kupił przedmiot na targu', 'stock': 'zaopatrzył się u kupca',
    'sell': 'sprzedał stary oręż kupcowi',
    'list': 'wystawił przedmiot na targu', 'camp': 'dołączył do obozu',
    'accept': 'przyjął próbę obozową', 'promote': 'awansował w obozie',
    'adventure': 'wyruszył na zlecenie', 'adventure_claim': 'odebrał zapłatę za zlecenie',
    'shop': 'wydał odłamki u handlarza',
}


def activity_rows(limit=40):
    from .worlds import current_world
    facts = BotDecision.objects.filter(profile__world=current_world(),success=True, action__in=ACTION_NAMES, profile__user__is_active=True).select_related('profile__user')[:limit]
    return [{'fact': fact, 'text': ACTION_NAMES[fact.action]} for fact in facts]


@transaction.atomic
def post_message(profile, body, *, topic_id=None, title=None):
    profile = PlayerProfile.objects.select_for_update().get(pk=profile.pk)
    from .worlds import playable
    if not playable(profile):raise ValueError("Postać należy do innego świata.")
    if profile.is_bot:
        raise ValueError('Boty rozmawiają przez scheduler.')
    body = (body or '').strip()
    title = (title or '').strip()
    if not 1 <= len(body) <= 1000 or (topic_id is None and not 3 <= len(title) <= 100):
        raise ValueError('Podaj treść (1–1000 znaków) i tytuł nowego wątku (3–100 znaków).')
    if profile.tavern_messages.filter(created_at__gt=timezone.now() - timedelta(seconds=20)).exists():
        raise ValueError('Zaczekaj 20 sekund przed kolejnym wpisem.')
    if topic_id is None:
        topic = TavernTopic.objects.create(author=profile, title=title)
    else:
        topic = TavernTopic.objects.select_for_update().filter(pk=topic_id,author__world_id=profile.world_id, locked=False).first()
        if topic is None:
            raise ValueError('Wątek nie istnieje lub został zamknięty.')
    message = TavernMessage.objects.create(topic=topic, author=profile, body=body)
    topic.updated_at = message.created_at
    topic.save(update_fields=['updated_at'])
    return topic


@transaction.atomic
def bot_conversation(profile):
    # The shared topic lock serializes different bots answering the same visitor.
    now = timezone.now()
    from .world_clock import POLISH_TIME
    if profile.tavern_messages.filter(created_at__gt=now - timedelta(minutes=10)).exists():
        return
    topic = TavernTopic.objects.select_for_update().filter(author__world_id=profile.world_id,locked=False, messages__author__is_bot=False, messages__created_at__gte=now - timedelta(days=1)).order_by('-updated_at').first()
    if not topic:
        fact = BotDecision.objects.filter(profile=profile, success=True, action__in=ACTION_NAMES).first()
        if not fact or profile.bot_turn < 3:
            return
        if TavernTopic.objects.filter(author=profile, created_at__gt=now - timedelta(days=1)).exists():
            return
        if TavernTopic.objects.filter(author__world_id=profile.world_id,author__is_bot=True, created_at__gt=now - timedelta(minutes=15)).exists():
            return
        topic = TavernTopic.objects.create(author=profile, title=f'Wieści ze szlaku: {profile.display_name}'[:100])
        TavernMessage.objects.create(topic=topic, author=profile, decision=fact, body=f'Wpadłem na chwilę do karczmy. Mój ostatni zapis: {ACTION_NAMES[fact.action]} ({fact.created_at.astimezone(POLISH_TIME):%d.%m %H:%M %Z}, Polska). Co słychać na waszych szlakach?')
        return
    latest = topic.messages.order_by('-created_at', '-pk').first()
    if latest.author.is_bot or hasattr(latest, 'bot_response'):
        return
    fact = BotDecision.objects.filter(profile=profile, success=True, action__in=ACTION_NAMES).first()
    if not fact:
        return
    topic_text = (topic.title + ' ' + latest.body).lower()
    if any(word in topic_text for word in ('rud', 'kopal', 'zarob')):
        advice = 'Rudy szukaj w Starej Kopalni. Pilnuj energii i odbierz urobek po zmianie.'
    elif any(word in topic_text for word in ('broń', 'bron', 'targ', 'handel')):
        advice = 'Przed zakupem na targu porównaj cenę z kupcem i sprawdź wymaganą siłę.'
    elif any(word in topic_text for word in ('obóz', 'oboz', 'awans')):
        advice = 'O awans pytaj w swoim obozie. Same bryłki nie wystarczą — trzeba przejść próbę.'
    else:
        advice = 'Pod barierą warto mieć dobry oręż i zostawić sobie siły na powrót.'
    body = f'{latest.author.user.username}, {advice} Mój ostatni zapis: {ACTION_NAMES[fact.action]} ({fact.created_at.astimezone(POLISH_TIME):%d.%m %H:%M %Z}, Polska).'
    TavernMessage.objects.create(topic=topic, author=profile, body=body, reply_to=latest, decision=fact)
    topic.updated_at = now
    topic.save(update_fields=['updated_at'])
