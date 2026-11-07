# Bieżąca roadmapa

Stan: 7 listopada 2026. Kanoniczna lista zadań: [GitHub #9](https://github.com/Yorick0499/ore-and-empire/issues/9). Pracujemy na osobnych gałęziach, z polskimi commitami i PR-ami; po zielonym CI i scaleniu gałąź jest usuwana.

## Wdrożone

- Lokalny launcher, trwałe konto i postać, jeden aktywny nazwany świat, 0–100 botów.
- Pełna pętla wydobycia, polowania, regeneracji, poziomów, sprzętu, magii, rynku i rzemiosła.
- 41 lokacji, 53 zwykłych przeciwników, trzej bossowie solo, sześć rozdziałów i finał postaci.
- Trzy obozy jako gildie, 18 osobistych rang, wspólne cele, skarbiec, ulepszenia i wyprawy przeciw wspólnemu HP. Nie planujemy osobnego systemu drużyn.
- Jedenaście wypraw czasowych, wyzwania dzienne/tygodniowe, reputacja, osiągnięcia i odłamki zdobywane w grze.
- Boty baseline-18, jawne imiona/oznaczenia, faktyczne zakupy, regeneracja, awanse, finał i audyt działań.
- Karczma, kroniki, powiadomienia, rankingi, sala chwały i jednorazowe podsumowanie operatora.
- Czas polski 1:1, słoneczne pory dnia Warszawy, sezony meteorologiczne i kalendarz eventów.
- Administrator, inicjalizacja i kontrolowany reset z zachowaniem kont administratorów, prywatne kopie oraz próby odtwarzania.
- 522 rekordy paczki G1, 632 przypisania lokalnych ilustracji z przypisanymi źródłami i gotycki motyw.

## Następne fundamenty

1. **#19 wdrożone:** PostgreSQL, weryfikowany import SQLite, rzeczywiste testy współbieżności i dzierżawa schedulera. [Instrukcja](POSTGRESQL.md).
2. **#24 wdrożone:** opcjonalny profil produkcyjny, HTTPS, nadzorowany worker, limity logowań i zweryfikowany staging. [Instrukcja](PRODUCTION.md). Domyślna instalacja pozostaje lokalna; nie opublikowano prywatnego serwera.
3. Dalsze strojenie gospodarki na podstawie pomiarów. Rosnący obrót nie dowodzi stabilnej podaży waluty.

## Gothic II: Noc Kruka

Osobiste ukończenie ani zapis końcowego rankingu nie przenosi do Gothic II i nie czyści świata.

- #30: reguły i jednorazowy transfer dorobku.
- #31: świeży start nowych postaci i balans weteranów.
- #32: Khorinis, gildie, potwory, przedmioty i zadania NK.
- #33: konto premium i osobne uprawnienie do Jarkendaru; saldo odłamków nie daje obecnie takiego dostępu.
- #34: izolacja wielu grywalnych edycji.
- #35: kontrolowany start II edycji i archiwizacja I.

Opcjonalne #28 wdrożone: lokalna polityka LLM, trwały budżet, fallback i porównanie z regułami. [Wyniki](LOCAL_AI_POLICIES.md). Model nie jest włączony domyślnie. Żadna z tych funkcji nie jest wymagana do lokalnego przejścia bieżącej kampanii.

## Dopracowanie pełnej edycji

Zadania [#65](https://github.com/Yorick0499/ore-and-empire/issues/65), [#66](https://github.com/Yorick0499/ore-and-empire/issues/66) i [#67](https://github.com/Yorick0499/ore-and-empire/issues/67): 35 wzorów dropu, ulepszenia +10, 100 powtarzalnych wart i miesięczny ranking, do 100 botów z harmonogramem. [Reguły endgame](LOOT_AND_ENDGAME.md) · [wydajność](BOT_PERFORMANCE.md).

## Wygoda codziennej gry — #80–#82

Przegląd obecnej pętli wyłonił trzy zadania: zabezpieczanie rynsztunku przed
utratą (#80), filtrowany i stronicowany targ (#81) oraz odczytowe porównanie
sprzętu z wyborem slotu pierścienia (#82). Reguły i obsługa: [ekwipunek](EQUIPMENT.md)
i [targ](MARKET_POLICY.md). Indeksy #9/#10 pozostają otwarte; II edycja #30–#35
nadal jest odłożona.
