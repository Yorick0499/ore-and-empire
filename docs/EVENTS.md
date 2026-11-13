# Wszystkie wydarzenia, święta i premie

Domyślny kalendarz najnowszej wersji. Wszystkie podane daty i godziny są w **Europe/Warsaw**: CET (UTC+1) zimą, CEST (UTC+2) latem. Zmiana czasu jest automatyczna. Początek należy do wydarzenia, koniec już nie. „5–9” oznacza od 5. dnia 00:00 do 9. dnia 00:00, czyli cztery dni kalendarzowe.

Administrator może zmieniać terminy i premie albo wyłączać eventy. Poniższe tabele dotyczą domyślnych definicji; bieżące działanie pokazuje `/wydarzenia/`. Ceny i koszty energii pozostają takie same podczas eventów.

## Sześć wydarzeń corocznych

| Wydarzenie | Termin w Polsce | Ruda | PD | Odłamki ze zlecenia czasowego |
|---|---|---:|---:|---:|
| Przebudzenie lasu | 20 marca 00:00 – 28 marca 00:00 | 100% | 130% | +1 |
| Święto Kopaczy | 25 października 00:00 – 8 listopada 00:00 | 125% | 110% | +1 |
| Dni Równowagi | 20 marca 00:00 – 23 marca 00:00 | 115% | 120% | +0 |
| Noc Tysiąca Ognisk | 20 czerwca 00:00 – 25 czerwca 00:00 | 110% | 120% | +0 |
| Święto Plonów | 22 września 00:00 – 29 września 00:00 | 120% | 115% | +0 |
| Zimowe ogniska kolonii | 20 grudnia 00:00 – 6 stycznia następnego roku 00:00 | 110% | 125% | +1 |

Nazwy i terminy są fanowskim kalendarzem Kolonii, nie odtworzeniem oficjalnych świąt z Gothic ani pełnym kalendarzem świąt państwowych.

## Dwanaście wydarzeń sezonowych

Każde trwa od 5. do 9. dnia wskazanego miesiąca. Brak dodatkowych odłamków.

| Pora roku | Miesiąc | Wydarzenie | Ruda | PD |
|---|---|---|---:|---:|
| Zima | Styczeń | Szlaki pod szronem | 115% | 110% |
| Zima | Luty | Warty przy zimowych ogniskach | 110% | 115% |
| Wiosna | Marzec | Roztopy na trakcie | 115% | 110% |
| Wiosna | Kwiecień | Wiosenne zbiory ziół | 110% | 115% |
| Wiosna | Maj | Przeprawy przez wezbrane strumienie | 115% | 110% |
| Lato | Czerwiec | Letnie karawany | 110% | 115% |
| Lato | Lipiec | Długie patrole lata | 115% | 110% |
| Lato | Sierpień | Zbiory na polach ryżowych | 110% | 115% |
| Jesień | Wrzesień | Jesienne transporty rudy | 115% | 110% |
| Jesień | Październik | Zapasy przed chłodem | 110% | 115% |
| Jesień | Listopad | Mgły nad doliną | 115% | 110% |
| Zima | Grudzień | Pierwsze zimowe warty | 110% | 115% |

## Wydarzenie losowe

**Szczęśliwa żyła rudy:** 150% rudy, 100% PD, bez bonusowych odłamków. Przy zmianie polskiej daty serwer liczy SHA-256 tekstu `ore-empire-events-v1:YYYY-MM-DD`. Pierwsze osiem cyfr szesnastkowych daje liczbę `draw`; zdarzenie istnieje, jeśli `draw % 4 == 0`. Godzina startu w Polsce to `draw % 20`, czyli 00:00–19:00. Trwa cztery rzeczywiste godziny, również podczas zmiany czasu.

To odtwarzalne losowanie daty, nie gwarancja wydarzenia dokładnie co cztery dni. Restart, ponowne logowanie i odświeżanie nie losują go na nowo. W świeżym świecie wydarzenie pojawi się po inicjalizacji kalendarza; launcher odświeża kalendarz przy zmianie lokalnej daty.

## Eventy administratora

W `/admin/` zarządca może dodać WorldEvent dla bieżącego świata: nazwę, opis, typ, datę startu/końca, procent rudy, procent PD i bonus odłamków. Daty formularzy są polskie. Koniec musi następować po starcie. Typy: sezonowy, świąteczny, losowy, specjalny. Ręcznie zmienione daty nie są nadpisywane przez automatyczny kalendarz.

## Jak premie się łączą

- Dla rudy i PD osobno wybierana jest najwyższa aktywna premia, włączając porę dnia. Bonusy nie sumują się i nie mnożą.
- Bonus odłamków pochodzi z najwyższego aktywnego eventu; pora dnia nie tworzy dodatkowych odłamków. Dotyczy wyłącznie zlecenia, którego bazowa nagroda zawiera odłamki.
- Przykład: Mgły nad doliną + Święto Kopaczy + noc dają 125% rudy, 115% PD i +1 odłamek ze zlecenia, a nie sumę wszystkich bonusów.
- Wyprawa czasowa zapisuje nagrodę przy starcie. Zakończenie eventu ani zmiana czasu przed odbiorem nie zmienia zapisanej kwoty.
- Polowanie/boss liczy premię w chwili walki, kopalnia w chwili odbioru urobku. Obóz może dodatkowo dodawać stały bonus magazynu do wydobycia.
- Stałe nagrody fabuły, osiągnięć, wyzwań i wypraw wspólnoty mają własne reguły; nie są automatycznie mnożone przez kalendarz.
- Nic nie zamyka lokacji, sklepów, kampanii ani funkcji o określonej porze.

## Pozostałe cele okresowe

Dzienne/tygodniowe wyzwania i zlecenia obozu nie są eventami premiującymi wszystkie nagrody. Resetują się według polskiej daty; tydzień zaczyna się w poniedziałek. Tak samo dobowa wyprawa obozowa i limit pięciu napojowych odnowień energii. Doby zmiany czasu mają odpowiednio 23 lub 25 godzin, ale nadal jeden reset o lokalnej północy.

## Regionalne okna i aktualizacje świata — #137

[Cztery pule regionalne i siedem nazwanych odsłon](WORLD_UPDATES.md). Dwie czterogodzinne odsłony na krainę i dobę, zależne od pory roku i odkryć świata. Do3 faktycznie podwyższonych nagród,300 dodatkowej rudy i3000 dodatkowych PD na postać/polski dzień, łącznie we wszystkich krainach. Bez nowych odłamków; obowiązuje maksimum z premią globalną. Odczyt kalendarza nie przyznaje ani nie rezerwuje nagród.
