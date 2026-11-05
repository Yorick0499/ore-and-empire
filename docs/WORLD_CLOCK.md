# Rzeczywisty czas polski i rytm świata

Świat działa **1:1 z prawdziwym czasem** w `Europe/Warsaw`. Nie ma przyspieszonej doby. Python `zoneinfo` korzysta z bazy reguł strefy: automatycznie CET zimą i CEST latem, bez ręcznego dodawania godziny. Baza nadal przechowuje świadome daty UTC; interfejs i granice kalendarza używają Polski. Serwer/OS musi mieć aktualne dane stref czasowych.

## Sześć pór dnia

Wschód/zachód słońca i zmierzch cywilny są liczone biblioteką [Astral 3.2](https://sffjunkie.github.io/astral/package.html) dla Warszawy (52.2297 N, 21.0122 E). To wspólny punkt odniesienia serwera: lokalna długość dnia w innych częściach Polski może różnić się o kilkanaście–kilkadziesiąt minut. Brak geolokalizacji gracza i zewnętrznych zapytań pogodowych.

| Pora | Granice | Ruda | PD |
|---|---|---:|---:|
| Świt | świt cywilny (Słońce −6°) → wschód | +5% | +10% |
| Poranek | wschód → godzinę przed południem słonecznym | +10% | +5% |
| Południe | godzina przed → godzina po południu słonecznym | +5% | +10% |
| Popołudnie | godzina po południu → zachód | +10% | +5% |
| Zmierzch | zachód → koniec zmierzchu cywilnego | +10% | +5% |
| Noc | koniec zmierzchu → kolejny świt cywilny | +5% | +10% |

Pory mają rzeczywistą, sezonowo zmienną długość. Granice są lewostronnie domknięte, prawostronnie otwarte. Jesienią i zimą noc zaczyna się wcześniej. Powtórzona godzina jesiennej zmiany czasu nie tworzy dodatkowej pory ani dodatkowego resetu. Pominięta godzina wiosną nie blokuje licznika; terminy zawierają offset, a licznik mierzy rzeczywisty upływ sekund.

Pasek świata pokazuje aktualną porę, sezon i godzinę kolejnej zmiany z CET/CEST. Przy przekroczeniu granicy prosi o odświeżenie zamiast przeładowywać formularze. Następna akcja zawsze używa rzeczywistego czasu serwera. Podgląd nagrody walki obejmuje premię eventu i pory dnia.

## Pory roku i kalendarz

Sezony meteorologiczne według **polskiej daty**: 1 marca–1 czerwca wiosna, 1 czerwca–1 września lato, 1 września–1 grudnia jesień, 1 grudnia–1 marca zima. Nie są to zmienne momenty równonocy i przesileń astronomicznych. Wszystkie domyślne wydarzenia, wyzwania, cele obozu i dobowe limity rozgrywki również używają polskiego kalendarza. [Pełna lista eventów](EVENTS.md).

Migracja 0030 przesuwa wyłącznie rozpoznane dawne domyślne terminy UTC. Ręcznie zmienione daty, bonusy, wyłączenia, odebrane nagrody i snapshoty trwających wypraw pozostają. Stare osobiste kontrakty zachowują datę okresu: niewykonany poprzedni cel nie postępuje, gotową nagrodę można odebrać. W pobliżu wdrożenia granica okresu może wypaść inaczej niż w poprzedniej wersji UTC; nie ma retroaktywnego przeliczania nagród.

## Balans

Nie ma zamykania lokacji ani zmniejszania regeneracji. Maksymalna różnica między porami to pięć punktów procentowych dla zasobu, premie eventów stosują maksimum zamiast mnożenia. Handel, ceny i odłamki nie są mnożone przez porę. Przy 100 bazowej rudy i 100 PD każda pora daje łącznie 15 dodatkowych jednostek; nie oznacza to identycznej użyteczności obu zasobów. Czasy akcji i cooldowny to rzeczywiste sekundy, nie godziny zegara ściennego.

## Testy i diagnostyka

Testy obejmują lokalną północ przy innej dacie UTC, zmianę pory roku, poniedziałek tygodnia, wszystkie granice słoneczne, zmianę CET/CEST w marcu i październiku, doby 23/25 h, niezmienność snapshotów oraz ochronę niestandardowych eventów. Raporty techniczne retencji i agregacji telemetrii pozostają w UTC i są tak opisane — nie są resetami rozgrywki.
