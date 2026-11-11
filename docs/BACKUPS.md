# Kopie i odtwarzanie lokalnego świata

SQLite: `python manage.py backup_world` zapisuje spójną kopię przez API backupu SQLite, bez zatrzymywania odczytów. Domyślnie prywatny katalog `backups/` (0700), pliki 0600, ostatnich 7 kompletnych kopii. Opcje: `--directory /prywatny/katalog --keep 14`. Katalog jest ignorowany przez Git; baza zawiera dane kont i hashe haseł, więc nie wolno publikować ani bazy, ani kopii. Nie kopiujemy `.env`, pliku dostępu admina ani sekretów do manifestu. Warto kopiować gotowe archiwa na osobny dysk, z własną retencją i ochroną dostępu. Komenda nie instaluje harmonogramu: uruchamiaj przed aktualizacją i regularnie z cron/systemd.

Manifest zawiera SHA-256 bazy, rewizję kodu, migracje i wersje paczek. Odtwarzanie jest **próbą do nowego pliku**:

```
python manage.py restore_world backups/world-DATA-ID --target /prywatny/katalog/proba.sqlite3
```

Komenda odrzuca istniejący cel i aktywną bazę, sprawdza hash, integralność oraz klucze obce, migruje kopię bieżącym kodem i porównuje liczby/digesty stabilnych danych: konta/uprawnienia, postacie i salda/progresja, ekwipunek, questy, wyprawy, transakcje i ledgery obecne w starszej wersji. Nowe kolumny/tabele z migracji są dozwolone; usunięcie historii albo zmiana salda powoduje błąd. Nie odtwarza zewnętrznych grafik: uruchom `validate_content` na właściwym checkoutcie. Weryfikacja zapisywana jest obok manifestu. Panel zarządcy pokazuje ostatnią kopię i osobno datę udanej próby. Świeża kopia bez próby nie jest oznaczana jako sprawdzona.

Po awarii: zatrzymaj launcher i wszystkie procesy piszące do świata. Zachowaj uszkodzoną bazę. Wybierz kopię, przeprowadź powyższą próbę, sprawdź `validate_content`, a następnie uruchom odtworzony plik przez `ORE_DATABASE_PATH=/pełna/ścieżka/proba.sqlite3 python play.py`. Po potwierdzeniu postaci/sald/questów możesz przy zatrzymanej grze ręcznie podmienić plik główny na zweryfikowaną kopię. Komenda nigdy sama nie promuje kopii ani nie kasuje zapisu produkcyjnego. Powrót do starego kodu wymaga zgodnej kopii sprzed migracji; nie wykonuj automatycznie migracji wstecz.

Retencja usuwa wyłącznie kompletne katalogi o nazwach nadanych przez narzędzie; obce katalogi i niedokończone kopie są pomijane. Weryfikacja dotyczy konkretnej kopii, nie gwarantuje zdrowia wszystkich przyszłych backupów. Próby wykonuj cyklicznie oraz przed aktualizacjami.

PostgreSQL: te same komendy wybierają natywny `pg_dump` i próbne `pg_restore`. Użyj `backup_world`, a do próby `restore_world KOPIA --target-database NOWA_NAZWA`. Wymagane są narzędzia klienta zgodne z główną wersją serwera i uprawnienie do utworzenia osobnej bazy. Samo kopiowanie plików działającego PostgreSQL nie jest tą procedurą. [Pełny profil i procedury](PRODUCTION.md).

## Dopracowanie pełnej edycji

Kopie obejmują teraz `OwnedItem.upgrade_level`, potwierdzenia `EquipmentWork`, `FrontierProgress` i historię `FrontierRecord`. Próba odtworzenia starszej bazy stosuje migrację 0031 na osobnym pliku: stare przedmioty dostają +0, a dotychczasowy postęp i hasła muszą pozostać zgodne z manifestem. Nie nadpisujemy żywego świata podczas próby.

Migracja 0032 dodaje pochodzenie egzemplarza (`OwnedItem.origin`); stare egzemplarze zachowują konserwatywne oznaczenie `legacy`. Pochodzenie jest objęte manifestem kopii. Próba odtworzenia przed wdrożeniem rang i katalogu G1 v3 zachowała 27 tabel zapisu.

PostgreSQL ma natywny backup MVCC i próbne odtworzenie do nowej bazy, z pełnym porównaniem logicznym. Szczegóły i wymagania klienta: [PRODUCTION.md](PRODUCTION.md). Hasła i dumpy pozostają prywatne.

## Zapis treści wypraw — migracja 0038

Nowe kopie SQLite obejmują utrwaloną treść i kwoty nagród wypraw. Starsza kopia jest sprawdzana według pierwotnych kolumn, a migracja dopisuje treść z zachowanego szablonu. Nowe kopie PostgreSQL mają `adventure_schema: 1`; starsze porównuje się bez czterech dodanych pól opisowych. Kwoty, własność i pozostałe dane nadal podlegają ścisłej kontroli. Import SQLite najpierw migruje prywatną kopię i porównuje pełny aktualny zapis.

## Pochodzenie i przygotowanie połączenia (0044)

Kopie SQLite i ich próby odtworzenia weryfikują dodatkowo pochodzenie postaci, stan przygotowania połączenia i jego dziennik, timery pracy/wypraw, bieżące zasoby oraz próby bossów używane przez cooldowny. Stare manifesty pozostają obsługiwane według zapisanych w nich kolumn. PostgreSQL zapisuje `origin_schema: 1`; przy porównywaniu kopii sprzed 0044 pomija wyłącznie nowo wyliczone pole pochodzenia. Nowe kopie wymagają jego pełnej zgodności. Procedurę operatora i ograniczenia `ready` opisuje [przygotowanie połączenia](CHARACTERS_AND_WORLDS.md).

## Przejście po obozowym Śniącym

Od 0046 kopie obejmują wyścig, uderzenia, wkład kont, nagrody i audyt Bariery; 0047 dodaje dalszą rangę Związku najemników. Stare kopie nadal sprawdza się według ich własnej specyfikacji. PostgreSQL rozróżnia `barrier_schema`, aby dopisane puste pola nie unieważniały dawnego dowodu.

Worker tworzy nową prywatną kopię w `backups/barrier/ID_WYSCIGU/` pod blokadą zapisu i sprawdza odtworzenie do osobnej bazy. Połączenie zostaje zatwierdzone dopiero po powodzeniu obu operacji. PostgreSQL wymaga zgodnych `pg_dump`/`pg_restore` oraz uprawnień utworzenia/usunięcia bazy próbnej. W czasie operacji występuje krótka przerwa 503. Ciężki zapis może odroczyć próbę; nie omija ona kopii przy błędzie lub braku miejsca.

```bash
# Odczyt stanu. ID wyścigu pochodzi z własnej bazy, nie jest UUID przygotowania 0044.
python manage.py barrier_transition ID_WYSCIGU
python manage.py barrier_transition ID_WYSCIGU --pause --operator LOGIN_ADMINA
python manage.py barrier_transition ID_WYSCIGU --unpause --operator LOGIN_ADMINA
python manage.py barrier_transition ID_WYSCIGU --resume --operator LOGIN_ADMINA
```

CLI nie potrafi nadać zwycięstwa ani ominąć jego dowodu. Po zabiciu wykonawcy poczekaj na wygaśnięcie 10-minutowej dzierżawy. Ostatni cios i zwycięzca pozostają zapisani; nie odtwarzaj historycznego przygotowania 0044 na nowszy postęp. Po awarii sprawdź narzędzia bazy, wolne miejsce i uprawnienia, następnie wznów tę samą operację. Zakończonego połączenia nie cofa się flagą pauzy. Rzeczywisty rollback całej instalacji wymaga zatrzymania wszystkich pisarzy i osobnej, uzgodnionej procedury odtworzenia świeżej kopii; CLI nigdy automatycznie nie nadpisuje żywej bazy.

## Panel wyścigu i audytu — #35

Aktywny administrator otwiera `/zarzadca/bariera/` z ustawień świata. Panel pokazuje trzy obozy, poziom i kwalifikację, wspólne HP, sumę obrażeń oraz liczbę różnych kont z dodatnim wkładem. Plan odczytowy pokazuje postacie, konta, oferty, nierozliczone aktywności i konflikty, bez tworzenia wyścigu ani kopii. Audyt jest ograniczony do ostatnich 40 zdarzeń; prywatne ścieżki plików nie trafiają do strony.

Pauza i wznowienie korzystają z jednej usługi dla WWW i CLI. Wymagają administratora, zgodnego aktualnego stanu i braku aktywnego wykonawcy. Powtórzona pauza nie dodaje kolejnego zdarzenia. Wznowienie tylko usuwa pauzę: przejście po rzeczywistym zwycięstwie podejmuje worker. Panel nie nadaje zwycięstwa, nie wykonuje długiej kopii w HTTP i nie cofa `joined`.

Podczas przejścia administrator może odczytać ten panel, choć pozostała gra zwraca 503. Zapisy w panelu nadal są wtedy zablokowane. Po przerwaniu procesu odczekaj do wygaśnięcia dzierżawy, sprawdź narzędzia/miejsce/uprawnienia i wznów tę samą operację. Restart, retry i odtwarzanie zachowują dotychczasowe mechanizmy i testy etapu #120.

## Zgodność rang od migracji 0048

Nowe kopie PostgreSQL mają `rank_path_schema=1`, a dowód obejmuje `legacy_water_path`. Dla wcześniejszych kopii PG weryfikator sprawdza poprawne wyliczenie nowego znacznika z dawnej frakcji, rangi i nieodebranego awansu; dopiero potem pomija tę jedną dodaną kolumnę przy porównaniu starego hasha. Pozostałe pola i liczby rekordów nadal muszą być identyczne. Błędny znacznik odrzuca odtworzenie; nie wystarcza zgodność samej rudy. Nowe dowody SQLite również obejmują znacznik. Test0047→0048 porównuje pełny logiczny snapshot oraz wszystkie stare pola i zadania. [Zakres rang](CAMPS.md).
