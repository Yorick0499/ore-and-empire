# Prywatna kronika mieszkańca

Stan zasad: 13 listopada 2026, po PR #141 (migracja 0054).

`/dziennik/` zawiera raporty walk, rozliczenia walut i powiadomienia bieżącej postaci, po 20 wpisów na stronie. Szczegół walki ponownie sprawdza właściciela; ID obcej postaci ani innego świata nie daje dostępu. Historia wykorzystuje istniejące trwałe fakty, nie chwilową sesję. Rozliczenia pokazują również wydatki i transfery, aby saldo miało pełny kontekst.

Powiadomienia powstają z zakończonych, nieodebranych wypraw, ostatnich 50 sprzedaży, awansów obozowych i wydarzeń rozpoczynających się w ciągu doby w dostępnym kontekście świata; po połączeniu wydarzenia obejmują wspólne regiony. Są deduplikowane i mają trwały stan przeczytania. Nie są wysyłane poza grę. Odświeżenie widoku nie przyznaje nagród; trzeba odebrać je zwykłą akcją. Licznik w nawigacji aktualizuje się przy kolejnym żądaniu strony. Oznaczenie jako przeczytane dotyczy wyłącznie własnej postaci i wymaga CSRF.

Lokacje można filtrować według dostępności, maksymalnego wymaganego poziomu, aktywności i aktualnej edycji. Filtr nie omija walidacji serwisów rozgrywki. Archiwalne światy nie udostępniają tu grywalnych lokacji.

Daty w kronice i wyprawach mają znacznik `time` i prezentację czasu polskiego; kalendarz używa krótkich polskich dat CET/CEST. Bez JavaScript pozostaje czytelny czas polski. Timery odtwarzają czas z zapisanego terminu, a odbiór i tak waliduje serwer.

## Trwała historia po Barierze

Zmiana aktywnej postaci nie udostępnia jej cudzych raportów. Połączenie, sukcesja, dalsze rangi i regionalny endgame zachowują historyczne identyfikatory; rachunki nie są przepisywane według nowych premii. Odsłony świata mają oddzielną trwałą historię w kalendarzu, a odczyt nie nadaje postępu. [Aktualizacje świata](WORLD_UPDATES.md).
