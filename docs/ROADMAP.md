# Bieżąca roadmapa

Stan: 6 listopada 2026. Kanoniczna lista zadań: [GitHub #9](https://github.com/Yorick0499/ore-and-empire/issues/9). Pracujemy na osobnych gałęziach, z polskimi commitami i PR-ami; po zielonym CI i scaleniu gałąź jest usuwana.

## Wdrożone

- Lokalny launcher, trwałe konto i postać, jeden aktywny nazwany świat, 0–20 botów.
- Pełna pętla wydobycia, polowania, regeneracji, poziomów, sprzętu, magii, rynku i rzemiosła.
- 41 lokacji, 53 zwykłych przeciwników, trzej bossowie solo, sześć rozdziałów i finał postaci.
- Trzy obozy jako gildie, 18 osobistych rang, wspólne cele, skarbiec, ulepszenia i wyprawy przeciw wspólnemu HP. Nie planujemy osobnego systemu drużyn.
- Jedenaście wypraw czasowych, wyzwania dzienne/tygodniowe, reputacja, osiągnięcia i odłamki zdobywane w grze.
- Boty baseline-14, jawne imiona/oznaczenia, faktyczne zakupy, regeneracja, awanse, finał i audyt działań.
- Karczma, kroniki, powiadomienia, rankingi, sala chwały i jednorazowe podsumowanie operatora.
- Czas polski 1:1, słoneczne pory dnia Warszawy, sezony meteorologiczne i kalendarz eventów.
- Administrator, inicjalizacja i kontrolowany reset z zachowaniem kont administratorów, prywatne kopie oraz próby odtwarzania.
- 520 rekordów paczki G1, 110 lokalnych obrazów z przypisanymi źródłami i gotycki motyw.

## Następne fundamenty

1. **#19:** PostgreSQL, prawdziwa współbieżność, dzierżawa i wyłączność schedulera.
2. **#24:** publiczny hosting, nadzór procesu, ograniczenia logowań i profil produkcyjny. Obecny launcher jest lokalny/LAN.
3. Dalsze strojenie gospodarki na podstawie pomiarów. Rosnący obrót nie dowodzi stabilnej podaży waluty.

## Gothic II: Noc Kruka

Osobiste ukończenie ani zapis końcowego rankingu nie przenosi do Gothic II i nie czyści świata.

- #30: reguły i jednorazowy transfer dorobku.
- #31: świeży start nowych postaci i balans weteranów.
- #32: Khorinis, gildie, potwory, przedmioty i zadania NK.
- #33: konto premium i osobne uprawnienie do Jarkendaru; saldo odłamków nie daje obecnie takiego dostępu.
- #34: izolacja wielu grywalnych edycji.
- #35: kontrolowany start II edycji i archiwizacja I.

Opcjonalnie #28: polityki LLM z limitami i porównaniem do botów regułowych. Żadna z tych funkcji nie jest wymagana do lokalnego przejścia bieżącej kampanii.
