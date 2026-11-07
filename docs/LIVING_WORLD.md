# Żyjąca kolonia — gracze i boty

Aktualna wersja używa polityki **baseline-17** i obserwacji schema 17. Boty regułowe nie wymagają API AI. Ich role łowcy, kupca i kopacza są preferencjami, a nie ograniczeniem dostępnych działań.

`python play.py --bots 6 --port 8001` uruchamia lokalny serwer i jeden serializujący scheduler. Bot wykonuje najwyżej jedną akcję na rundę. Nie łącz launchera z drugim `run_bots --loop`. Zatrzymanie programu zatrzymuje tury; po powrocie zasoby regenerują się ze zwykłego upływu czasu, ale serwer nie odgrywa wszystkich opuszczonych akcji.

## Co robi mieszkaniec

- Wybiera obóz, przyjmuje próby awansu i przechodzi kampanię swojej ścieżki.
- Kopie, odbiera pracę, poluje w dostępnych lokacjach, walczy z bossami i zdobywa rzeczywiste PD.
- Kupuje i zakłada lepszy oręż/pancerz, sprzedaje zbędne zapasy, zachowuje materiały dostaw i receptur.
- Uczy się i wydaje zdobyte PN; część mieszkańców rozwija magię. Przygotowuje się do osobistego finału.
- Odpoczywa, regeneruje HP/energię/manę, kupuje potrzebne leczenie lub odnowienie w granicach wspólnych limitów.
- Przyjmuje wyzwania, odbiera ukończone nagrody i osiągnięcia, wspiera projekty/skarbiec/wyprawy obozu.
- Handluje według potrzeb i ceny jednostkowej; przecenia i wycofuje zalegające oferty, odzyskuje miejsce w zapasie.

Bot nie może nadawać sobie waluty, XP, ekwipunku ani dowolnych ID celów. Kontroler tworzy allowlistę dozwolonych akcji i wywołuje te same transakcyjne serwisy co człowiek. Czas polski, eventy, koszty i wymagania są wspólne. Zwycięstwo bota w finale nie zamyka serwera.

Sześć przedmiotów to limit roboczego zapasu polityki, nie ogólny limit plecaka każdego gracza. Niezbywalne trofea fabularne nie zajmują tego roboczego limitu. Handel przenosi rudę; nie emituje jej samym przekazaniem przedmiotu.

## Jak zobaczyć, że boty grają

`/zycie-kolonii/` pokazuje imiona, role, ostatni heartbeat i ostatnie 40 udanych działań. Aktywność wygasa po 90 sekundach. Sam odczyt nie odgrywa tury ani nie tworzy losowej transakcji. Monitor zarządcy pokazuje powody odpoczynku/odrzucenia i przepływy; czytaj go razem z realnym zużyciem przedmiotów, nie samym obrotem bot–bot.

`/karczma/` to trwałe forum: 20 wątków i 30 wiadomości na stronie, do 1000 znaków, 20 sekund między wpisami gracza. HTML jest escapowany. Administrator może zamykać wątki i usuwać wpisy.

Bot odpowiada regułowo na świeży wpis człowieka, odwołując się do zapisanej akcji. Nie udaje rozumienia dowolnych pytań. Limit: raz na 10 minut na bota, najwyżej jedna automatyczna odpowiedź na wpis. Samodzielny wątek wymaga co najmniej trzech akcji; najwyżej jeden na dobę na bota i jeden na 15 minut w kolonii przy wspieranym pojedynczym schedulerze. Boty są jawnie oznaczone.

## Treść i uprawnienia

[Instrukcja całej gry](GAME_GUIDE.md) opisuje zasoby, wyprawy, premie, odłamki i rankingi. [EVENTS.md](EVENTS.md) wymienia pełny domyślny kalendarz, [WORLD_CLOCK.md](WORLD_CLOCK.md) wyjaśnia czas polski i CET/CEST. [MARKET_POLICY.md](MARKET_POLICY.md), [MAGIC.md](MAGIC.md), [CRAFTING.md](CRAFTING.md) opisują poszczególne decyzje i limity.

Konta techniczne `colony-bot-N` nie mają używalnych haseł. Administrator tworzony jest lokalnie, bez wspólnych danych dostępu w repozytorium. [Zarządzanie światem](WORLD_MANAGEMENT.md), [backup](BACKUPS.md) i [monitoring](WORLD_MONITOR.md) zawierają procedury operatora.

## Walidacja

Baseline-16 uzupełnia strzały lub bełty do własnej broni i rezerwuje je przed wyprzedażą. Brak dostępnej amunicji wyklucza walkę fizyczną z planu; bot nadal może pracować i wykonywać inne działania. Prognozy uwzględniają zręczność broni dystansowej oraz bonusy sprzętu. [Audyt i regresje](BUG_AUDIT.md).

Pełna symulacja przechodzi kampanię zwykłym graczem i trzema obozami botów bez nadawania zasobów. Mieszana sesja potwierdza zdobywanie poziomu i rzeczywisty zakup od bota. Oddzielne testy sprawdzają odrzucone polityki, koszty, regenerację, retry, rollback i uprawnienia. Historyczne schematy 7–15 są odtwarzalne; wyniku dawnych losowych walk nie udajemy jako deterministycznego replayu.

## Dopracowanie pełnej edycji

Po finale bot ocenia bezpieczną wartę, w razie potrzeby powtarza niższy stopień, ulepsza noszony sprzęt i rozbiera zbędne łupy. Pył jest chroniony przed automatycznym wystawianiem. Porównanie pancerzy uwzględnia ulepszenie, aby bot nie zamieniał mocniejszego egzemplarza na słabszy łup. [Rozłożenie pracy do 100 botów i pomiary](BOT_PERFORMANCE.md).
