from django.core.management.base import BaseCommand
from django.db import transaction
from characters.models import StoryQuest, ItemBluePrint
from characters.gothic_campaign import campaign_definitions


PROLOGUE = [
    {'key': 'prologue-arrival', 'title': 'Pod obcym niebem', 'description': 'Przy placu wymian spotykasz kopacza wracającego ze zmiany. Zanim ruszysz w dolinę, wysłuchaj jego ostrzeżenia i zdecyduj, jak zaczniesz nowe życie.',
     'objectives': [{'id': 'promise', 'kind': 'talk', 'label': 'Odpowiedz kopaczowi', 'options': {'work': 'Najpierw znajdę uczciwą pracę.', 'learn': 'Najpierw poznam zasady kolonii.'}}],
     'rewards': {'ore': 10, 'experience': 50}},
    {'key': 'prologue-shift', 'title': 'Bryłka za przysługę', 'description': 'Kopacz wskazał ci drogę do Starej Kopalni. Odbierz urobek po prawdziwej zmianie, a dowiesz się, dlaczego cała dolina żyje rudą.',
     'prerequisites': ['prologue-arrival'], 'objectives': [{'id': 'shift', 'kind': 'mine', 'label': 'Ukończ zmianę i odbierz rudę', 'count': 1}],
     'rewards': {'ore': 15, 'experience': 100}},
    {'key': 'prologue-path', 'title': 'Droga między ogniskami', 'description': 'Przy ścieżce do Starego Obozu kręci się młody ścierwojad. Rozpraw się z nim i dostarcz wieść pod bramę. W kolonii użyteczność znaczy więcej niż obietnice.',
     'prerequisites': ['prologue-shift'], 'objectives': [{'id': 'beast', 'kind': 'hunt', 'target': 'young_scavenger', 'label': 'Pokonaj młodego ścierwojada'}, {'id': 'gate', 'kind': 'travel', 'target': 'old_camp', 'label': 'Dotrzyj pod bramę Starego Obozu'}],
     'rewards': {'ore': 20, 'experience': 150, 'premium': 1}},
]


class Command(BaseCommand):
    help = 'Create missing one-time story definitions; preserve administrator edits and accepted snapshots.'

    @transaction.atomic
    def handle(self, *args, **options):
        rusty = ItemBluePrint.objects.filter(name='Zardzewiały miecz').first()
        if not rusty:
            from django.core.management import call_command
            call_command('seed_world', stdout=self.stdout)
            rusty = ItemBluePrint.objects.get(name='Zardzewiały miecz')
        for entry in PROLOGUE + campaign_definitions(rusty.pk):
            data = dict(entry)
            key = data.pop('key')
            quest, _ = StoryQuest.objects.get_or_create(key=key, defaults=data)
            quest.full_clean()
        from django.apps import apps
        from characters.story_narrative import apply_narrative
        apply_narrative(apps)
        self.stdout.write('Story campaign ready; existing definitions and progress retained.')
