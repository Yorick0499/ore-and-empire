"""Read-only next steps from a character's actual contracts and resources."""
from django.db.models import F
from django.urls import reverse
from django.utils import timezone
from .models import StoryQuest
from .gothic_campaign import CHAPTERS
from .story_quests import available,progress_for,ready
from .locations import LOCATIONS


def journey(profile):
    steps=[];now=timezone.now()
    def add(title,route,description='',ends_at=None,query=''):
        steps.append({'title':title,'url':reverse(route)+query,'description':description,'ends_at':ends_at})
    runs=list(profile.story_runs.select_related('quest').order_by('-accepted_at','-pk')[:100])
    claimed=[r for r in runs if r.status=='claimed'];active=next((r for r in runs if r.status!='claimed'),None)
    chapter=max([1,*[r.snapshot.get('chapter',1) for r in runs]])
    chapter=max(1,min(6,chapter));name=next(n for number,n,_ in CHAPTERS if number==chapter)
    finished=hasattr(profile,'campaign_completion')
    if profile.action_end_time:
        if profile.action_end_time<=now:add('Odbierz urobek','mine_page','Zmiana w kopalni już się skończyła.')
        else:add('Trwa twoja zmiana w kopalni','mine_page','Po zakończeniu wróć po urobek.',profile.action_end_time)
    adventure=profile.adventures.filter(claimed_at__isnull=True).select_related('template').first()
    if adventure:
        add('Odbierz zapłatę za wyprawę' if adventure.ends_at<=now else 'Trwa wyprawa: '+adventure.public_name,'adventures_page',
            'Nagroda czeka na ręczny odbiór.' if adventure.ends_at<=now else 'Możesz zamknąć grę i wrócić później.',None if adventure.ends_at<=now else adventure.ends_at)
    if active:
        if ready(profile,active):add('Odbierz: '+active.snapshot['title'],'story_page','Cele przydziału są wykonane.')
        elif active.status=='accepted':add('Rozpocznij: '+active.snapshot['title'],'story_page','Postęp liczy się od rozpoczęcia przydziału.')
        else:
            goal=next((g for g in active.snapshot['objectives'] if progress_for(profile,active,g)<(1 if g['kind']=='wait' else g.get('count',1))),None)
            if goal:
                kind=goal['kind'];route={'mine':'mine_page','item':'shop_page','train':'train_page'}.get(kind,'story_page');query=''
                if kind in {'hunt','boss'}:
                    location=next((loc for loc in LOCATIONS if loc.accessible(profile) and (goal['target'] in loc.monsters or (kind=='boss' and loc.key==goal['target']))),None)
                    if location:route=location.route;query='?location='+location.key
                add(goal['label'],route,active.snapshot['title'],query=query)
    else:
        completed={r.snapshot['key']:r for r in claimed};taken={r.quest_id for r in runs}
        quest=next((q for q in StoryQuest.objects.filter(enabled=True).exclude(pk__in=taken).order_by('chapter','level','pk') if available(profile,q,completed=completed)),None)
        if quest:add('Dostępny przydział: '+quest.title,'story_page','Fabuła jest opcjonalna; możesz też rozwijać się przez polowania i wspólnotę.')
    if profile.challenges.filter(claimed_at__isnull=True,progress__gte=F('required')).exists():add('Odbierz nagrodę wyzwania','challenges_page')
    if profile.skill_points:
        add(f'Wydaj punkty nauki: {profile.skill_points}','train_page','Wybierz atrybut lub umiejętność broni; pamiętaj o koszcie rudy.')
    if not profile.inventory.filter(is_equipped=True,equipped_slot='weapon').exists() and not profile.prepared_magic_id:
        add('Znajdź i załóż pierwszą broń','shop_page','Kupno nie zakłada sprzętu — potem otwórz Ekwipunek.',query='?kind=weapon&usable=1&affordable=1')
    if profile.camp=='NONE':add('Wybierz obóz i wspólne cele','camp_page','Obóz jest twoją gildią. Wybór przynależności jest stały.')
    else:add('Sprawdź wspólne cele swojego obozu','camp_guild','Twój wkład oraz działania mieszkańców rozwijają tę samą wspólnotę.')
    if finished:add('Dalsza droga: Warty za Przełęczą','frontier_page','Szukaj lepszego łupu i walcz o wynik miesiąca.')
    previous=250*profile.level*(profile.level+1);span=max(1,profile.required_exp-previous)
    return {'steps':steps[:7],'chapter':chapter,'chapter_name':name,'finished':finished,
            'xp_value':max(0,min(span,profile.experience-previous)),'xp_span':span,
            'xp_remaining':max(0,profile.required_exp-profile.experience),'next_level':profile.level+1}
