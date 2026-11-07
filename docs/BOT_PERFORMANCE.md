# Żywy świat: do 100 botów

Nazwę i liczbę **0–100** mieszkańców ustawisz w panelu Zarządca → Świat → Ustawienia bez resetu (`/zarzadca/swiat/reset/`). Zapis tworzy brakujące konta i zmienia aktywną populację bez kasowania postępu. Zmniejszenie liczby usypia nadmiarowe konta; nie usuwa ich dobytku. W nowej instalacji liczbę wybierasz podczas inicjalizacji; `play.py --bots 100` jest wartością początkową, a dla skonfigurowanej instalacji obowiązuje zapis panelu. Konto techniczne bota nie ma używalnego hasła.

## Jak rozkładamy pracę

Lokalny launcher `play.py` obsługuje HTTP i boty jednym procesem; nie uruchamiaj drugiego `run_bots --loop` na tej samej bazie. Między żądaniami wykonuje **najwyżej jedną turę**, a nie 100 akcji w jednej fali. Zachowuje kolejność mieszkańców także po odświeżeniu populacji co 5 sekund. Nie nadrabia setek zaległych tur po wyłączeniu komputera. Odpoczywający bot ma co najmniej 30 sekund przerwy przed ponownym sprawdzeniem.

Minimalny odstęp to maksimum z 0,2 sekundy, `--interval / liczba_botów` oraz czterokrotności średniego kosztu ostatnich tur. Dla 100 mieszkańców pełny obieg wynosi co najmniej około 20 sekund plus czas samych akcji i obsługi HTTP. Dla sześciu zachowana jest częstotliwość zbliżona do dawnego obiegu. Dłuższe tury automatycznie spowalniają kolejkę: cel to około 20% czasu na boty, **nie twardy limit CPU**. Nie ma LLM, płatnego API, treningu modeli ani obliczeń na GPU.

Polityka **baseline-18 / schema 19** wykorzystuje łupy, wspólny rynek, wyposażenie, rzemiosło, kampanię i cele po finale. Wersje 7–17 pozostają odtwarzalne. Miękki próg zapasu ogranicza zakupy; łupy mogą go przekroczyć, a nadmiar sprzętu jest rozbierany przez zwykły serwis. Pył do ulepszeń jest rezerwowany przed automatyczną wyprzedażą. Imiona są rozróżnialne także przy 100 botach.

Szczegółowe decyzje pozostają ograniczane retencją (`--history-days`, domyślnie 30 pełnych dni UTC) z zachowaniem agregatów. Powtarzane czekanie nie zapisuje nowej decyzji częściej niż co pięć minut. Backup obejmuje przedmioty z poziomami ulepszeń, prace kuźni, postęp i historię wart.

## Odtwarzalny pomiar

Po audycie transakcji i prognoz przygotowano [osobny pomiar baseline-16](reports/audyt-stu-botow-2026-11-06.json). Poprzednie raporty i wartości liczbowe niżej zachowano jako wyniki baseline-15; nie nadpisujemy historycznych pomiarów.

```bash
python scripts/benchmark_bots.py --seconds 60 --report /tmp/sto-botow.json
python scripts/benchmark_bots.py --mature --seconds 60 --report /tmp/sto-botow-endgame.json
```

Skrypt zawsze tworzy osobną tymczasową bazę i lokalny launcher na wolnym porcie, a na końcu zamyka tylko swój proces. Nie korzysta z zapisu użytkownika. Mierzy RSS procesu serwera, wykorzystanie jednego rdzenia CPU oraz rzeczywiste odpowiedzi HTTP ekranu logowania podczas działania botów. Kontrolowana opcja `--mature` nadaje poziom 30 i zakończenie kampanii wyłącznie do pomiaru kosztu rozwiniętej populacji; nie udaje przejścia gry. Autentyczny przebieg od zera oraz dalsza gra tych samych postaci są oddzielnie w `simulate_release`.

Raporty: [nowa populacja](reports/sto-botow-2026-11-06.json), [populacja po finale](reports/sto-botow-endgame-2026-11-06.json). To krótkie pomiary na maszynie wykonującej zadanie, nie obietnica parametrów komputera gracza. Nie zastępują obciążenia uwierzytelnionych ekranów, wielodniowej gospodarki ani wdrożenia PostgreSQL/publicznego hostingu. Lokalny SQLite i pojedynczy proces pozostają świadomym zakresem pierwszej wersji.

Pomiar 6 listopada 2026, po 60 sekund: nowa populacja — 55,61 MiB RSS, 17,25% jednego rdzenia, p95 HTTP 36,90 ms, 505 żądań bez błędów; rozwinięta — 55,77 MiB, 20,08%, p95 48,48 ms, 490 żądań bez błędów. W obu próbach wszystkie 100 botów miało turę w działającym launcherze i nie zapisano odrzuconych decyzji. Wyniki nie obejmują pamięci procesu przygotowania fixture ani przeglądarki.

Pomiar po rozszerzeniu katalogu: [100 botów, baseline-17](reports/rynsztunek-sto-botow-2026-11-07.json). Jedna runda trwała 3,247 s w izolowanym świecie. To krótki test nowej populacji; nie symuluje wielodniowej gospodarki. Kuźnia działa przed finałem, a regeneracja przed walką fabularną ma pierwszeństwo przed patrolem.

Polityka baseline-18 daje potrzebnemu treningowi pierwszeństwo przed opcjonalnym patrolem. Test PostgreSQL z innymi identyfikatorami postaci objął również dwie ścieżki magiczne w jednej populacji. Planowanie nie blokuje gracza na czas decyzji bota, a scheduler ma wspólną dzierżawę — [szczegóły](POSTGRESQL.md).

Eksperymentalne Ollama jest opcjonalne i objęte trwałym budżetem. [Porównanie](LOCAL_AI_POLICIES.md) nie wykazało powodu do zmiany domyślnych stu botów na LLM. Reguły nie potrzebują GPU ani działającego serwera modelu.
