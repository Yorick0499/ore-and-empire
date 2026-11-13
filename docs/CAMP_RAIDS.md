# Asynchroniczne wyprawy wspólnoty

Stan: 14 XI 2026, wyprawy na rozkaz #152 (migracja 0055). Wyprawa wspólnoty ma wspólne HP i osobne wypady uczestników. Nie jest bossem solo ani globalnym wyścigiem Śniącego. Nie wymaga drużyny lub jednoczesnego zalogowania. Przed Barierą dotyczy rodzimego obozu/frakcji; po niej bieżącej wspólnoty sukcesji. [Sukcesja](CAMP_GUILDS.md).

## Wyprawa dzienna

Członek od osobistego szczebla 1 może ogłosić jeden cel na wspólnotę/polski dzień. Podstawowe tematy obejmują ochronę szybu, orkowy patrol i węża rozlewiska; inne frakcje mają własne etykiety. Parametry utrwalają się przy zwołaniu: `500+100×poziom` HP, atak `10+2×poziom`, ochrona `4+2×poziom`. Minimalny poziom uczestnika 3.

Wypad: do 3 rund, 20 energii, rzeczywiste zdrowie, mana/zwoje albo amunicja; 60 sekund cooldownu postaci. Przygotowany czar wymaga zasobów. Po jego wyczerpaniu walka przechodzi na pięści. Ranny uczestnik wycofuje się z 1 HP, zachowując zadane obrażenia jako wkład.

Powyżej 60% HP trwa rozpoznanie, potem szał (+5 ataku), od 25% ostatni zryw (+10 ataku i połowa pancerza). Fazy działają również wewnątrz wypadu. Końcowy cios liczy najwyżej pozostałe HP. Lód i przerwania działają przez zwykły silnik.

Zwycięstwo daje wspólnocie raz 60 PD i 100 rudy. Uczestnik z dodatnimi obrażeniami odbiera raz 50 PD, 10 rudy i 1 odłamek. Samo członkostwo nie daje nagrody. Odbiór może nastąpić później, także po zmianie dnia. Nowy dzień otwiera nowy cel, bez przenoszenia obrażeń.

## Dodatkowe wyprawy na rozkaz gracza

Na `/wspolnota/` sekcja „Wyprawy na rozkaz — droga do poziomu 10” pozwala ogłaszać kolejne cele tego samego dnia. Wymagania: **ludzka postać**, Kolonia przed globalnym połączeniem, najwyższa czwarta ranga i wspólnota poniżej poziomu 10. Uprawnione rangi: Magnat, Arcymag Ognia, Gwardzista Lee, Arcymag Wody, Templariusz i Arcyguru. Sama stara wartość `camp_tier=3` nie wystarcza starszemu Magowi Wody, jeśli nie osiągnął faktycznej arcyrangi.

Ogłoszenie nie kosztuje zasobów i nie daje PD. Trzeba pokonać pełny cel przez zwykłe wypady. Parametry, koszt 20 energii, zdrowie/mana/amunicja, odstęp 60 s i nagrody są takie jak w wyprawie dziennej: **60 PD wspólnoty i 100 rudy skarbca za zwycięstwo**, a raz za rzeczywisty wkład 50 PD, 10 rudy i 1 odłamek. Jedna dodatkowa wyprawa może być aktywna naraz. Po jej pokonaniu można od razu ogłosić następną; dzienna wyprawa nadal ma swój osobny limit.

Cel na rozkaz nie resetuje HP o północy. Po osiągnięciu poziomu 10 nie ogłasza się następnego, ale rozpoczęty można dokończyć przed połączeniem. Globalne połączenie kończy możliwość atakowania niedokończonych celów na rozkaz; zapisany wkład pozostaje historią, a za ukończone cele można nadal odebrać niewypłacone nagrody. Nie odblokowuje to Śniącego bez osobistych wymagań, Echa i pieczęci kont.

Boty nie mogą ogłaszać dodatkowych celów. Mogą normalnie uczestniczyć i odbierać nagrody: najpierw kończą aktywną dzienną walkę, potem pomagają przy ludzkim rozkazie. Kadencja i okna sesji pozostają takie jak wcześniej.

[Próba Arcymaga Wody](reports/wyprawy-na-rozkaz-2026-11-14.json) doprowadziła wspólnotę od 1 do 10: 15 zwycięstw, 31 płatnych wypadów, 620 energii i 1232 many, około 8,86 wirtualnej godziny z normalną regeneracją, bez odnowień sklepu i zwojów. Początek to jawnie przygotowany Arcymag poziomu 35, nie przejście od nowego konta ani pomiar aktywnego czasu człowieka. Boty w tej próbie nie pomagały; ich udział sprawdza osobny test.

UUID ogłoszenia identyfikuje rozkaz danej postaci. Powtórzenie ukończonego rozkazu nie tworzy nowego celu. Blokada wspólnoty i ograniczenie bazy chronią przed dwoma równoczesnymi aktywnymi rozkazami, również gdy ogłasza je dwóch graczy. Zwycięstwo i poziom wspólnoty zapisują się razem.

## Cel tygodniowy po NK

Od poziomu 45, po odebranym `nk-undead`, połączeniu i rozstrzygniętej frakcji działa dodatkowy cel tygodnia, niezależny od dziennego. Tydzień zaczyna się w poniedziałek 00:00 Europe/Warsaw. HP: `10000+1000×poziom` wspólnoty, atak 100, ochrona 60; zwykły koszt wypadu 20 energii i odstęp 60 sekund. Nagroda uczestnika: raz 100 rudy, 1000 PD i 5 pyłu, bez odłamków. Zwycięstwo daje wspólnocie istniejące 60 PD i 100 rudy.

Tematy regionalne rotują; po odkryciu „Orkowie u bram” co piąty tydzień może przypaść orkowy wódz. Zwołana wyprawa zachowuje snapshot, nawet gdy później zmieni się odsłona lub tydzień. Orkowy temat nie tworzy drugiej wypłaty ani dodatkowej premii regionalnej. [Endgame](REGIONAL_ENDGAME.md), [aktualizacje](WORLD_UPDATES.md).

## Nagrody, stare wyprawy i blokady

UUID, trwały zapis wypadu i blokady chronią koszt, obrażenia, ostatni cios i nagrody. Zmiana celu przy użytym UUID jest odrzucana. Wynik, koszty, wspólne HP, skarbiec/PD i raport są jedną transakcją; awaria cofa całość. Odbiór ma unikalny klucz uczestnik/wyprawa.

Przy sukcesji niedokończone wyprawy rozdzielanych wspólnot są archiwizowane, bez kopiowania postępu. Za zakończone historyczne cele nadal odbiera nagrodę rzeczywisty uczestnik. [Dokładne zasady](CAMP_GUILDS.md). Kopie zachowują wkład i wypłaty; retencja telemetrii ich nie kasuje.

Boty baseline-24 zwołują, atakują i odbierają przez te same usługi, ze zwykłymi zasobami i bramkami. Lokalnie działa jeden launcher SQLite; produkcyjnie PostgreSQL i jeden worker z dzierżawami. Rzeczywiste współbieżne uderzenia i odbiory sprawdza CI PostgreSQL. [Weryfikacja](SOLO_PLAYTEST.md).
