# Buildy i drogi frakcyjne od nowej postaci

Stan 13 XI 2026, po #141. Zweryfikowana droga gry od początku przez kampanię mieszkańca NK do ósmej rangi i dalszych wart. Nie oznacza odtworzenia wszystkich zadań Bezimiennego ani wszystkich efektów oryginalnych przedmiotów.

## Wybór własnej drogi

| Początek | Build i podstawowa droga | Wspólnota po Barierze |
|---|---|---|
| Stary Obóz | Wojownik: Kopacz → Cień → Strażnik → Magnat | Bandyci |
| Stary Obóz | Ogień: Kopacz → Cień → Mag Ognia → Arcymag Ognia | Klasztor Magów Ognia |
| Nowy Obóz | Łucznik: Kret → Szkodnik → Najemnik → Gwardzista Lee | Najemnicy |
| Nowy Obóz | Woda: Kret → Szkodnik → Mag Wody → Arcymag Wody | Magowie Wody |
| Khorinis | Wojownik: Rekrut → Strażnik → Sierżant → Dowódca | Miasto i dalszy Zakon |
| Klasztor Khorinis | Ogień: Nowicjusz → Adept → Mag → Arcymag | Wspólny Klasztor |
| Farma Onara | Łucznik: Pracownik → Zbrojny → Najemnik → Dowódca | Wspólni Najemnicy |
| Bractwo | Guru: Zbieracz → Nowicjusz → Guru → Arcyguru | Jednorazowy wybór Ognia albo Wody; próba wybiera Wodę |
| Bractwo | Wojownik: Zbieracz → Nowicjusz → Strażnik → Templariusz | Jednorazowy wybór wspólnoty; próba wybiera Miasto |

To dziewięć scenariuszy, a nie wszystkie kombinacje broni i wyborów. Ograniczenia Guru i pozostałe dozwolone wybory mają oddzielne testy macierzy. Przed Barierą są cztery szczeble; dalsze cztery wymagają połączenia i własnych opłaconych awansów. Historyczne pochodzenie pozostaje zapisane.

## Przygotowanie, które ma znaczenie

Wojownik rozwija siłę i umiejętność wybranej broni. Łucznik potrzebuje zręczności, łuku i strzał; podstawowe rangi mogą wymagać także siły. Wyższe rangi wojowników przyjmują siłę **lub** zręczność. Broń trzeba założyć po zakupie, a łupy można porównać przed wymianą.

Mag rozwija manę i płaci PN/rudą za kręgi. Pierwsze kręgi są dostępne przed tytułem pełnego maga po osiągnięciu odpowiedniej rangi. Runy i zwoje kupuj w **Magii** — oferta wiedzy jest oddzielna od zwykłego kupca. Nie każda tożsamość z katalogu jest działającym zaklęciem. Osobno kupione zwoje tego samego typu są teraz wspólnym zapasem walki. Po zużyciu przygotowanego egzemplarza pozostający zapas nadal jest przygotowany. Dodatkowe chronione i wystawione na targ egzemplarze nie są zużywane. Runa ma wymaganą szkołę/krąg; zwoju może użyć każdy, lecz każda inkantacja zużywa sztukę i manę. Odporność na własny żywioł może wymagać kupionego zwoju innego typu albo innej taktyki.

Sama mana na pierwszy rzut nie wystarcza na długą walkę. Polowanie i boss pokazują obrażenia czaru po odporności, orientacyjną liczbę potrzebnych rzutów, koszt many i rzuty dostępne z obecnego zapasu. Prognoza zdrowia uwzględnia brak many/zwojów oraz późniejszą walkę pięściami. Fazy bossa są liczone w prognozie zdrowia. Zapas rzutów jest szacunkiem pokonania samym czarem, nie warunkiem wejścia ani obietnicą zwycięstwa.

Ochrona, pierścienie, amulet i pas są częścią przygotowania, nie tylko broń. Przy wzroście maksymalnego zdrowia/many poczekaj na rzeczywistą regenerację albo zużyj legalne zapasy. Zachowaj kilka PN na treningi wymagane w zadaniu awansu. Gdy zabraknie rudy, zlecenia dochodowe finansują dalsze lekcje; odłamki zdobyte w grze mogą opłacić istniejący itemshop. Konto premium nie jest potrzebne.

## Od mieszkańca do dalszej gry

[Instrukcja uruchomienia obu regionów](COMPLETE_JOURNEY.md). Osobisty finał nie usuwa Bariery. Globalny Śniący jest celem wspólnoty i wymaga wkładu trzech kont; pięć postaci jednego konta nie zastępuje społeczności. Boty mogą pomagać na tych samych zasadach. Do czasu zwycięstwa Khorinis nadal ma zlecenia, polowania, awanse i rozwój wspólnoty.

Po bezpiecznej aktywacji jest jeden serwer, wspólny rynek/ranking i podróże. Jarkendar jest publiczny po osobistym odblokowaniu portalu. Dalej prowadzą Kruk, smoki i Irdorath. Po finale pozostają [cztery regionalne ścieżki i cel tygodniowy](REGIONAL_ENDGAME.md), kuźnia, wspólnota i wynik miesiąca. Dorobek nie resetuje się wraz z miesiącem.

## Odtwarzalna kontrola grywalności

```sh
python manage.py simulate_builds --report /tmp/ore-builds.json
# Szybsze sprawdzenie konkretnej drogi:
python manage.py simulate_builds --case new-archer --report /tmp/ore-archer.json
```

Nowe pliki raportów; istniejące nie są nadpisywane. Komenda zawsze uruchamia osobną bazę SQLite, nie dziedziczy prywatnego PostgreSQL ani bazy gry. Scenariusze zaczynają z normalną postacią poziomu 0. Punkty, atrybuty, sprzęt, zaklęcia, amunicja, zadania i wszystkie osiem rang są rzeczywiście zdobywane/opłacane. Nie włącza się zwycięstw ani osobistych kamieni milowych fiksturą.

W tej macierzy globalne zwycięstwo społeczności jest zdarzeniem zewnętrznym po ukończeniu podstawowej drogi; **nie mierzy czasu oczekiwania całego serwera na Barierę**. Osobna komenda `simulate_journey` sprawdza prawdziwą walkę trzech zdobytych od 0 kont, kopię, odtworzenie i aktywację. Te dowody uzupełniają się, nie należy dodawać ani bezpośrednio porównywać ich czasów.

Czas każdej operacji jest modelowany jako 10 sekund, regeneracja i timery są wirtualne. Oczekiwanie na wydobycie pochodzi teraz z faktycznego `action_end_time`: zmiana w UI trwa 15 **sekund**, nie 15 minut. Poprzednie raporty pełnej drogi zawierały konserwatywne nadmiarowe czekanie i pozostają historyczne. Nie zmieniono timera gry ani zapisów.

CI dzieli dziewięć organicznych dróg na trzy niezależne grupy: broń, magia i Bractwo. Szybkie testy prognoz/izolacji oraz PostgreSQL pozostają osobno. [Wyniki i ograniczenia](reports/buildy-frakcje-2026-11-12.json).

Automatyczne zwycięstwa dowodzą możliwości progresji, nie subiektywnej satysfakcji człowieka. Strategie znają cele, używają NPC i nie konkurują na rynku/PvP. Nie przechodzą wszystkich 400 regionalnych stopni. Regionalne wydarzenia #137 są wdrożone. Dłuższa gospodarka 250 botów i obserwacje ludzi pozostają dalszym rozwojem w #9. [Świeża powtórka wszystkich dziewięciu dróg i ograniczenia](reports/grywalnosc-wydania-2026-11-13.json).
