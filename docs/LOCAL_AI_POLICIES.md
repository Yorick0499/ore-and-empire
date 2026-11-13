# Opcjonalne lokalne polityki AI (#28)

Stan zasad: 13 listopada 2026, po PR #141 (migracja 0054).

**Domyślnie działają boty regułowe baseline-24.** Gra, launcher i CI nie wymagają modelu, GPU ani płatnego API. Eksperyment `ollama-1` jest dostępny wyłącznie po świadomym włączeniu w oddzielnym workerze; nie zmieniono polityki prywatnego świata użytkownika.

## Co model może wybrać

Gra buduje małą listę dozwolonych par akcja/cel na podstawie niemutowalnej obserwacji. Model zwraca wyłącznie numer pozycji. Może wybrać zwykłą pracę w kopalni, zaplanowane bezpieczne polowanie albo dostępną wyprawę. Może podejmować te zwykłe zajęcia także w trakcie realizacji celów łowieckich/wydobywczych. Nie wybiera dowolnego ID, ceny, statystyk, nagrody ani SQL.

Rozmowy/odbiór fabuły, awanse, nagrody, zakupy, odzysk, przekuwanie, krytyczna regeneracja i przygotowanie walk pozostają obsługiwane regułami. Każdą akcję i własność celu ponownie sprawdzają zwykłe serwisy gry. Model nie dostaje ORM, kont, haseł, nazw graczy, panelu zarządcy, czatu ani narzędzi. Odpowiedź tekstowa nie jest wykonywana ani publikowana w karczmie.

## Konfiguracja lokalna

1. Przygotuj lokalny serwer Ollama i wybrany model, np. `qwen2.5:0.5b`. Gra nie pobiera modeli automatycznie. Uruchamiaj Ollama z wyłączoną chmurą (`OLLAMA_NO_CLOUD=1`).
2. W osobnej, wcześniej skonfigurowanej instalacji [workera](PRODUCTION.md) ustaw prywatnie `ORE_BOT_POLICY=ollama`, `ORE_LLM_MODEL=qwen2.5:0.5b`, `ORE_LLM_ENDPOINT=http://127.0.0.1:11434/api/chat`. Obsługiwane są tylko endpointy loopback; przekierowania i tagi cloud są odrzucane.
3. Opcjonalne limity: `ORE_LLM_TIMEOUT` (domyślnie 2 s, maksymalnie 10), `ORE_LLM_MAX_CALLS` (20/h), `ORE_LLM_MAX_TOKENS` (50 000/h) i `ORE_LLM_MAX_SECONDS` (60 s/h). Produkcyjny budżet jest zapisany na świat w bazie i nie zeruje się po restarcie workera. Każde wywołanie rezerwuje konserwatywnie 4096+48 tokenów oraz cały timeout, więc domyślne limity dopuszczają najwyżej 12 wywołań na godzinę.
4. Przełącz `ORE_BOT_POLICY=rules` i zrestartuj worker, by wrócić do reguł. `play.py` nadal używa reguł; nie uruchamiaj obok niego drugiego schedulera tego samego świata.

W Compose adres loopback oznacza ten sam kontener/sieć procesów; domyślny obraz nie zawiera Ollama. Eksperyment sprawdzono na natywnym workerze i serwerze modelu na jednym hoście. Nie otwieraj endpointu modelu publicznie i nie zastępuj loopback adresem zewnętrznego dostawcy — adapter go nie obsługuje.

Adapter wymusza 0 warstw GPU i dwa wątki inferencji, kontekst 4096 i maksymalnie 48 tokenów odpowiedzi. Wywołanie HTTP odbywa się w małym osobnym procesie bez odziedziczonych sekretów aplikacji/bazy. Cały proces jest kończony po deadline, także przy powolnych nagłówkach/DNS. Błąd, timeout, przekroczenie odpowiedzi, nieprawidłowy indeks lub budżet prowadzą do decyzji regułowej. Po błędzie działa trwała przerwa 60 s. Timeout nie jest gwarancją natychmiastowego zatrzymania obliczeń po stronie serwera modelu, dlatego ograniczamy także liczbę prób i długość odpowiedzi. Nie ma opłat za zewnętrzne API; pozostaje lokalny koszt CPU/RAM/czasu.

## Audyt i replay

Obserwacje/rekordy mają schemat 23. Reguły to baseline-24; historyczne wersje pozostają odtwarzalne. Adapter ollama-1 zachowuje zamrożoną baseline-18 swojego protokołu. `BotDecision.policy_snapshot` zapisuje wersję protokołu, model, dozwolone wybory, wybrany indeks, status fallbacku, hash promptu, opóźnienie i zużycie tokenów. Nie zapisuje surowej odpowiedzi ani sekretów endpointu.

Replay weryfikuje listę wyborów i hash na podstawie zapisanej obserwacji oraz zamrożonej baseline-18. **Nie pyta ponownie modelu**. Status `forced-rules` oznacza obowiązkową decyzję reguł, `accepted` poprawny wybór modelu, `fallback` błąd, a `budget-or-cooldown` brak dostępnego budżetu. Sam napis `ollama-1` nie znaczy, że każdą akcję wybrał model.

## Rzeczywiste porównanie

`python manage.py benchmark_policies --model qwen2.5:0.5b --endpoint http://127.0.0.1:11434/api/chat --steps 100 --calls 8 --timeout 5 --report /nowy/raport.json`

Polecenie tworzy dwie osobne kopie jednego syntetycznego zapisu: trzy boty, 100 kroków, po 30 minut zwykłej regeneracji na krok, identyczne początkowe ziarno. Test dotyczy pętli MMORPG i zadań obozowych; nie seeduje kampanii fabularnej. Nie nadaje zasobów w trakcie próby ani nie dotyka bazy gracza. Warmup modelu jest osobno wykazanym kosztem, poza budżetem decyzji. Odmienne decyzje zmieniają dalsze losowania; to jedna krótka próba, nie statystyczny dowód jakości gospodarki.

[Raport](reports/polityki-lokalne-ai-2026-11-07.json), CPU, bez GPU i chmury:

| Wynik | Reguły | Lokalny model + reguły |
| --- | ---: | ---: |
| Czas próby | 9,654 s | 24,710 s |
| Łączne PD | 8626 | 7698 |
| Ruda na końcu | 264 | 301 |
| Wygrane walki | 56 | 53 |
| Transakcje graczy/botów | 1 | 1 |
| Nieudane akcje | 0 | 0 |
| Wybory modelu | 0 | 8 |

W obu wariantach różnica uzgodnienia ledgeru rudy/odłamków wynosiła zero. Model przesunął aktywność w stronę zasobów, ale kosztował więcej czasu i uzyskał mniej PD. Wynik nie uzasadnia włączenia go domyślnie. Domyślna populacja obecnej gry wynosi 125+125 botów i nadal korzysta z reguł; powyższy raport zachowuje zakres eksperymentu z 7 XI.

[Osobny staging](reports/ai-budzet-po-restarcie-2026-11-07.json) wykonał dwie rzeczywiste, poprawne decyzje modelu na trzech aktywnych botach. Restart workera zachował licznik 2/2 i nie odnowił limitu. Po próbie procesy testowe zatrzymano. Testy automatyczne używają małego kontrolowanego serwera HTTP, nie pobierają modelu; sprawdzają timeout, złośliwe indeksy/pola, przekierowania, sekrety, replay, fallback oraz budżet po restarcie.

Źródło protokołu: [Ollama — lokalne chat API](https://docs.ollama.com/api/chat).

Porównanie `benchmark_policies` wymusza ograniczoną liczbę aktywnych tur: pomija sesje i symulowane zakupy premium, aby porównywać decyzje przy tym samym czasie gry. Osobny scenariusz 48 godzin w `simulate_release` respektuje prawdziwe sesje i rejestruje symulowane zakupy jako oddzielne źródło.

## Bieżący świat

Eksperyment nie zastępuje osobnych testów sukcesji, NK, regionalnych wart i wydarzeń. Wynik historycznego porównania trzech botów nie potwierdza zachowania całej populacji 250 ani wszystkich później dodanych mechanik. [Bieżące testy i ograniczenia](SOLO_PLAYTEST.md).
