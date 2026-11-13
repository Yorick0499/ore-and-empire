"""Public editorial pools. Changing a world's chapter never changes event rewards."""
from dataclasses import dataclass

VERSION = 1
ANNUAL_KEYS = ('miners', 'winter', 'spring', 'harvest', 'solstice', 'balance')
ACTIVITIES = ('mine', 'hunt', 'adventure', 'boss')


@dataclass(frozen=True)
class Stage:
    key: str
    title: str
    summary: str
    annual: tuple
    monthly: tuple
    random: tuple
    regional: tuple


STAGES = (
    Stage('colony', 'Kolonia pod Barierą',
          'Bariera wciąż oddziela dolinę; trzy obozy dbają o własne zapasy i szlaki.',
          ('Święto Kopaczy', 'Zimowe ogniska trzech obozów', 'Przebudzenie lasu pod Barierą',
           'Zbiory obozowych zapasów', 'Noc ognisk nad ryżowiskami', 'Dni wymiany między obozami'),
          ('Obozowe drogi pod szronem', 'Drewno dla zimowych ognisk', 'Roztopy przy obozowych mostach',
           'Zioła dla obozowych uzdrowicieli', 'Przeprawy przez dolinę pod Barierą', 'Karawany między obozami',
           'Letnie obchody kopalń', 'Zbiory na polach ryżowych', 'Jesienne transporty rudy',
           'Zapasy obozów przed chłodem', 'Mgły nad doliną pod Barierą', 'Pierwsze zimowe warty obozów'),
          ('Szczęśliwa żyła Starej Kopalni', 'Bogaty urobek Wolnej Kopalni', 'Rudny uskok pod Barierą'),
          ('Ruda dla obozów', 'Patrole pod Barierą', 'Przysługi trzech obozów', 'Ochrona obozowych szlaków')),
    Stage('island', 'Khorinis przed połączeniem',
          'Miasto, klasztor i ludzie Onara utrzymują życie wyspy, zanim upadnie odległa Bariera.',
          ('Święto czeladników Khorinis', 'Zimowe ognie portu', 'Wiosenne prace na farmach',
           'Święto plonów Lobarta i Onara', 'Noc latarni Khorinis', 'Dni zgody miasta i farm'),
          ('Oblodzone trakty Khorinis', 'Drewno dla portowych domów', 'Roztopy przy farmie Lobarta',
           'Zioła dla klasztornych aptekarzy', 'Naprawa mostów na wyspie', 'Letnie dostawy do portu',
           'Patrole pól Onara', 'Żniwa na farmach Khorinis', 'Jesienne zapasy miasta',
           'Opał dla klasztoru i farm', 'Mgły na wybrzeżu Khorinis', 'Zimowa straż portowych bram'),
          ('Rudny uskok kamieniołomu', 'Cenny urobek dla portowych kupców', 'Odkrycie wyspiarskich górników'),
          ('Zapasy kamieniołomu', 'Patrole wokół Khorinis', 'Dostawy miasta i farm', 'Ochrona wyspiarskich szlaków')),
    Stage('barrier', 'Pęknięcie Bariery',
          'Bariera upadła; dawni mieszkańcy Kolonii i Khorinis otwierają wspólne drogi.',
          ('Święto wolnych kopaczy', 'Zimowe ognie połączonych osad', 'Wiosna otwartych przełęczy',
           'Plony wspólnych szlaków', 'Noc ognisk bez Bariery', 'Dni spotkania dwóch krain'),
          ('Odśnieżanie otwartej przełęczy', 'Zimowe dostawy między krainami', 'Roztopy na wolnych szlakach',
           'Wspólne wyprawy zielarzy', 'Naprawa przepraw po upadku Bariery', 'Karawany wolnych osad',
           'Obchody nowo otwartych dróg', 'Zbiory dla przybyszów z Kolonii', 'Ruda na odbudowę przełęczy',
           'Wspólne zapasy na zimę', 'Meldunki z zamglonej przełęczy', 'Zimowe warty połączonych osad'),
          ('Żyła odsłonięta po upadku Bariery', 'Znalezisko na wolnym szlaku', 'Ruda dla odbudowy przełęczy'),
          ('Ruda wolnych szlaków', 'Patrole po upadku Bariery', 'Karawany dwóch krain', 'Ochrona otwartych przejść')),
    Stage('jarkendar', 'Zaginiona Dolina',
          'Badacze dotarli do Jarkendaru; wyprawy potrzebują zaopatrzenia i ochrony ruin.',
          ('Święto robotników kanionu', 'Zimowe ogniska badaczy', 'Wiosenne obchody Zaginionej Doliny',
           'Zbiory dla ekspedycji Budowniczych', 'Noc ognisk pirackiego brzegu', 'Dni badaczy równowagi'),
          ('Zimowe dostawy za portal', 'Ogniska w obozach ekspedycji', 'Roztopy na szlakach badaczy',
           'Zioła z bagien Jarkendaru', 'Naprawa przepraw w kanionie', 'Karawany do Zaginionej Doliny',
           'Letnie obchody ruin Budowniczych', 'Zbiory dla robotników kopalni', 'Jesienne transporty za portal',
           'Zapasy ekspedycji przed zimą', 'Meldunki z mgieł Jarkendaru', 'Zimowe straże przy portalu'),
          ('Rudna szczelina kanionu', 'Znalezisko robotników Zaginionej Doliny', 'Urobek dla ekspedycji za portalem'),
          ('Zapasy ekspedycji', 'Obchody badaczy', 'Zaopatrzenie Zaginionej Doliny', 'Ochrona badań i ruin')),
    Stage('night', 'Cienie nad Khorinis',
          'Zwiadowcy ostrzegają przed Poszukiwaczami; osady wzmacniają straże i sieć meldunków.',
          ('Święto strażników zaopatrzenia', 'Zimowe ogniska przeciw ciemności', 'Wiosenne obchody zwiadowców',
           'Plony pod strażą osad', 'Noc latarni na zagrożonych traktach', 'Dni czujności wspólnot'),
          ('Zwiad na ośnieżonych traktach', 'Dostawy dla zimowych strażnic', 'Roztopy pod okiem zwiadowców',
           'Zioła dla rannych strażników', 'Łącznicy na wezbranych przeprawach', 'Konwoje pod osłoną patroli',
           'Letnie meldunki o Poszukiwaczach', 'Zbiory pod strażą wspólnot', 'Transporty do zagrożonych osad',
           'Zapasy w strażnicach szlaków', 'Sygnały latarni we mgle', 'Zimowe obchody przeciw ciemności'),
          ('Rudne znalezisko zwiadowców', 'Zabezpieczona żyła przy strażnicy', 'Cenny urobek spod zagrożonego traktu'),
          ('Zapasy strażnic', 'Zwiad przeciw ciemności', 'Konwoje pod strażą', 'Ochrona przed ciemnością')),
    Stage('dragons', 'Przebudzenie smoków',
          'Rozpoczynają się smocze wyprawy; pięć frakcji gromadzi zapasy dla łowców.',
          ('Święto kopalń smoczych wypraw', 'Zimowe ogniska łowców smoków', 'Wiosenne przygotowania łowców',
           'Plony dla smoczych patroli', 'Noc sygnałowych ognisk łowców', 'Dni przymierza przeciw smokom'),
          ('Ośnieżone szlaki łowców smoków', 'Opał dla obozów łowców', 'Roztopy pod smoczymi szczytami',
           'Zioła na wyprawy przeciw smokom', 'Przeprawy dla smoczych patroli', 'Letnie konwoje łowców',
           'Zwiad u podnóża smoczych leży', 'Zbiory dla obozów łowców', 'Ruda na oręż przeciw smokom',
           'Zapasy smoczych wypraw na zimę', 'Sygnały patroli pod smoczymi szczytami', 'Zimowe straże łowców smoków'),
          ('Żyła rudy na oręż łowców', 'Znalezisko pod smoczymi szczytami', 'Urobek dla smoczych wypraw'),
          ('Ruda dla łowców', 'Zwiad smoczych wypraw', 'Konwoje łowców', 'Osłona smoczych wypraw')),
    Stage('irdorath', 'Żagle ku Irdorath',
          'Otwarto przeprawę ku Irdorath; port i patrole wspierają wyprawę morską.',
          ('Święto stoczni i kopalń', 'Zimowe ognie wyprawy morskiej', 'Wiosenne przygotowania floty',
           'Plony dla załóg dalekiego rejsu', 'Noc latarni szlaku Irdorath', 'Dni przymierza dalekich brzegów'),
          ('Zimowe transporty do stoczni', 'Opał dla załóg i portowych wart', 'Roztopy na szlakach do portu',
           'Zioła dla medyków pokładowych', 'Naprawy nabrzeży przed rejsem', 'Letnie zaopatrzenie floty',
           'Patrole dalekich brzegów', 'Zbiory dla załóg wyprawy', 'Jesienne konwoje do portu',
           'Zapasy pokładowe przed sztormami', 'Latarnie we mgle dalekich brzegów', 'Zimowe warty szlaku Irdorath'),
          ('Rudne znalezisko dla stoczni', 'Żyła na zapasy dalekiej wyprawy', 'Cenny urobek portowego konwoju'),
          ('Zapasy wyprawy morskiej', 'Patrole dalekich brzegów', 'Konwoje dla floty', 'Osłona szlaku Irdorath')),
    Stage('orc-war', 'Orkowie u bram',
          'Po finale NK wspólnoty bronią osad i dostaw przed orkowym naporem.',
          ('Święto zaopatrzenia twierdz', 'Zimowe ognie obrońców', 'Wiosenne obchody linii obrony',
           'Żniwa pod osłoną obrońców', 'Noc sygnałowych ognisk twierdz', 'Dni jedności obrońców krain'),
          ('Odśnieżanie linii zaopatrzenia', 'Opał dla obleganych strażnic', 'Roztopy przy obronnych mostach',
           'Zioła dla lazaretów wspólnot', 'Naprawa przepraw obrońców', 'Letnie konwoje do twierdz',
           'Patrole przeciw orkowym zwiadowcom', 'Żniwa pod strażą frakcji', 'Ruda na uzbrojenie obrońców',
           'Zapasy osad przed oblężeniem', 'Meldunki z mgieł orkowego pogranicza', 'Zimowe straże wspólnych granic'),
          ('Zabezpieczona żyła na orkowym pograniczu', 'Ruda dla obrońców twierdz', 'Znalezisko eskorty zaopatrzenia'),
          ('Zapasy obrońców', 'Patrole przeciw orkom', 'Konwoje do twierdz', 'Osłona wspólnej obrony')),
)
BY_STAGE = {stage.key: stage for stage in STAGES}


def stage_for(universe, flags):
    if 'barrier' not in flags:
        return BY_STAGE['island' if universe == 'GOTHIC_II' else 'colony']
    return next(BY_STAGE[key] for key in ('orc-war', 'irdorath', 'dragons', 'night', 'jarkendar', 'barrier') if key in flags)


def global_text(stage, category, index):
    if category == 'annual':
        title = stage.annual[ANNUAL_KEYS.index(index)]
        detail = 'Święto mieszkańców. Premie obejmują zwykłe nagrody aktywności; bonusowe odłamki tylko zlecenia, które już je przyznają.'
    elif category == 'monthly':
        title = stage.monthly[index - 1]
        detail = 'Miesięczne prace sezonowe. Obowiązuje najwyższa premia dla zasobu, bez mnożenia i bez zamykania szlaków.'
    else:
        title = stage.random[index]
        detail = 'Odkrycie górników i dostawców zwiększa nagrody w rudzie przez cztery rzeczywiste godziny.'
    return title, f'{stage.summary} {detail}'


def regional_text(stage, title, activity, place, season):
    if activity == 'raid':
        return title, f'{stage.summary} Cel tygodnia wspólnoty po finale NK, od poziomu 45. Wspólne HP i zwykłe nagrody tygodnia, bez dodatkowej premii regionalnej.'
    prefix = stage.regional[ACTIVITIES.index(activity)]
    name = f'{prefix} — {title[0].lower() + title[1:]}'
    detail = f'{season} · {place}. {stage.summary} Wskazana aktywność od poziomu 15; do trzech podwyższonych nagród na polski dzień, wspólnie dla krain. Bez dodatkowych odłamków.'
    return name, detail


def validate_pools():
    if len(BY_STAGE) != 8:
        raise ValueError('Incomplete world-stage pools')
    for stage in STAGES:
        if (len(stage.annual), len(stage.monthly), len(stage.random), len(stage.regional)) != (6, 12, 3, 4):
            raise ValueError('Incomplete calendar pool: ' + stage.key)
        for rows in (stage.annual, stage.monthly, stage.random, stage.regional):
            if len(rows) != len(set(rows)) or any(not value.strip() or len(value) > 100 for value in rows):
                raise ValueError('Invalid event names: ' + stage.key)
    return len(STAGES)
