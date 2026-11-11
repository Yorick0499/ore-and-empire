"""Small first chapter of the joined world; further NK catalog remains a separate task."""
from .models import StoryQuest


def seed():
    StoryQuest.objects.get_or_create(key='barrier-new-road',defaults={
        'title':'Szlak po upadku Bariery','description':'Mieszkańcy obu regionów zabezpieczają wspólny trakt. Nie jesteś Bezimiennym: odpowiadasz za bezpieczeństwo podróżnych.',
        'universe':'JOINED','chapter':7,'level':30,'energy_cost':10,
        'objectives':[{'id':'report','kind':'talk','label':'Zgłoś gotowość do wspólnej warty','options':{'ready':'Obejmuję wartę na nowym szlaku.'}}],
        'rewards':{'ore':100,'experience':1000},
    })
    StoryQuest.objects.get_or_create(key='barrier-fire-dragon',defaults={
        'title':'Zagrożenie znad szczytu','description':'Smok ognia zagraża odblokowanemu szlakowi. Przygotuj ochronę przed ogniem i pomóż osłonić mieszkańców.',
        'universe':'JOINED','chapter':7,'level':35,'energy_cost':10,'prerequisites':['barrier-new-road'],
        'objectives':[{'id':'dragon','kind':'boss','label':'Pokonaj smoka ognia','target':'k2_dragon_fire','count':1}],
        'rewards':{'ore':300,'experience':3000,'premium':2},
    })
