"""Public chronicle for visitors, derived from announcements already published."""
from django.contrib.auth.views import LoginView

from .models import WorldRelease
from .world_releases import RELEASES

CHRONICLE = {
    'foundations': (
        'Kroniki dwóch krain',
        'Pod Barierą ruda kupuje chleb i ochronę. Po drugiej stronie morza port Khorinis żyje z pracy doków i dostaw z farm. Wybierz, gdzie zaczniesz swoją historię.',
    ),
    'barrier': (
        'Bariera runęła',
        'Nad Górniczą Doliną po raz pierwszy od lat widać czyste niebo. Kupcy ruszają do Khorinis, a dawni więźniowie szukają miejsca w nowych gildiach.',
    ),
    'jarkendar': (
        'Odnaleziono Zaginioną Dolinę',
        'Magowie Wody otworzyli kamienny portal. Za nim czekają ruiny Budowniczych, niebezpieczne bagna i piraci, którzy chętnie pohandlują z przybyszami. Każdy wędrowiec zdobywa własne prawo przejścia.',
    ),
    'night': (
        'Cienie nad Khorinis',
        'Z traktów zaczęli znikać podróżni. Straż poszukuje zwiadowców, a badacze próbują odczytać tablice pozostawione w ruinach Zaginionej Doliny.',
    ),
    'dragons': (
        'Smoki obudziły się w Dolinie',
        'Na przełęczach pojawiły się ślady ognia. Z Khorinis płyną zapasy, a gildie zbierają ludzi zdolnych poprowadzić wyprawy przeciw smokom.',
    ),
    'irdorath': (
        'Pierwszy statek dopłynął do Irdorath',
        'Z portu wypłynęła załoga z przydziałem do najdalszej z wypraw. Teraz kolejni mieszkańcy mogą starać się o miejsce na pokładzie i wyruszyć ku skalistej wyspie.',
    ),
    'orc-war': (
        'Orkowie u bram',
        'Patrole przynoszą wieści o nowych oddziałach na wspólnych szlakach. Gildie zwołują warty, aby obronić drogi i osady obu krain.',
    ),
}


def public_chronicle():
    releases = WorldRelease.objects.filter(world__is_current=True, key__in=CHRONICLE)
    announced = set(releases.values_list('key', flat=True))
    key, version, _, _, art, _ = next(
        (row for row in reversed(RELEASES) if row[0] in announced), RELEASES[0],
    )
    title, story = CHRONICLE[key]
    return {'title': title, 'story': story, 'version': version, 'art': art}


class ChronicleLoginView(LoginView):
    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs, chronicle=public_chronicle())
