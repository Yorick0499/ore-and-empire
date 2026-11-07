# Kopie i odtwarzanie lokalnego świata

SQLite: `python manage.py backup_world` zapisuje spójną kopię przez API backupu SQLite, bez zatrzymywania odczytów. Domyślnie prywatny katalog `backups/` (0700), pliki 0600, ostatnich 7 kompletnych kopii. Opcje: `--directory /prywatny/katalog --keep 14`. Katalog jest ignorowany przez Git; baza zawiera dane kont i hashe haseł, więc nie wolno publikować ani bazy, ani kopii. Nie kopiujemy `.env`, pliku dostępu admina ani sekretów do manifestu. Warto kopiować gotowe archiwa na osobny dysk, z własną retencją i ochroną dostępu. Komenda nie instaluje harmonogramu: uruchamiaj przed aktualizacją i regularnie z cron/systemd.

Manifest zawiera SHA-256 bazy, rewizję kodu, migracje i wersje paczek. Odtwarzanie jest **próbą do nowego pliku**:

```
python manage.py restore_world backups/world-DATA-ID --target /prywatny/katalog/proba.sqlite3
```

Komenda odrzuca istniejący cel i aktywną bazę, sprawdza hash, integralność oraz klucze obce, migruje kopię bieżącym kodem i porównuje liczby/digesty stabilnych danych: konta/uprawnienia, postacie i salda/progresja, ekwipunek, questy, wyprawy, transakcje i ledgery obecne w starszej wersji. Nowe kolumny/tabele z migracji są dozwolone; usunięcie historii albo zmiana salda powoduje błąd. Nie odtwarza zewnętrznych grafik: uruchom `validate_content` na właściwym checkoutcie. Weryfikacja zapisywana jest obok manifestu. Panel zarządcy pokazuje ostatnią kopię i osobno datę udanej próby. Świeża kopia bez próby nie jest oznaczana jako sprawdzona.

Po awarii: zatrzymaj launcher i wszystkie procesy piszące do świata. Zachowaj uszkodzoną bazę. Wybierz kopię, przeprowadź powyższą próbę, sprawdź `validate_content`, a następnie uruchom odtworzony plik przez `ORE_DATABASE_PATH=/pełna/ścieżka/proba.sqlite3 python play.py`. Po potwierdzeniu postaci/sald/questów możesz przy zatrzymanej grze ręcznie podmienić plik główny na zweryfikowaną kopię. Komenda nigdy sama nie promuje kopii ani nie kasuje zapisu produkcyjnego. Powrót do starego kodu wymaga zgodnej kopii sprzed migracji; nie wykonuj automatycznie migracji wstecz.

Retencja usuwa wyłącznie kompletne katalogi o nazwach nadanych przez narzędzie; obce katalogi i niedokończone kopie są pomijane. Weryfikacja dotyczy konkretnej kopii, nie gwarantuje zdrowia wszystkich przyszłych backupów. Próby wykonuj cyklicznie oraz przed aktualizacjami.

PostgreSQL: te komendy jawnie odmawiają działania. W przyszłym wdrożeniu używaj `pg_dump` (spójny snapshot), zaszyfrowanej/offsite retencji oraz `pg_restore` do osobnej bazy i równoważnej walidacji. Samo skopiowanie plików działającego PostgreSQL nie jest tą procedurą. Gotowość tego backendu pozostaje w #19.

## Dopracowanie pełnej edycji

Kopie obejmują teraz `OwnedItem.upgrade_level`, potwierdzenia `EquipmentWork`, `FrontierProgress` i historię `FrontierRecord`. Próba odtworzenia starszej bazy stosuje migrację 0031 na osobnym pliku: stare przedmioty dostają +0, a dotychczasowy postęp i hasła muszą pozostać zgodne z manifestem. Nie nadpisujemy żywego świata podczas próby.

Migracja 0032 dodaje pochodzenie egzemplarza (`OwnedItem.origin`); stare egzemplarze zachowują konserwatywne oznaczenie `legacy`. Pochodzenie jest objęte manifestem kopii. Próba odtworzenia przed wdrożeniem rang i katalogu G1 v3 zachowała 27 tabel zapisu.
