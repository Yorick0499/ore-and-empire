# Polityka bezpieczeństwa Ore & Empire

Poprawki trafiają do `main`. Podaj dokładny commit lub tag, którego dotyczy zgłoszenie. Starsze instalacje aktualizuje się według [instrukcji wdrożenia](docs/PRODUCTION.md). Zgłoszenia odnoszące się do wcześniejszych rewizji pomagają ustalić zakres problemu.

Cykliczne skany, ocenę wyników oraz testowanie aktualizacji opisuje [procedura utrzymania zależności](docs/DEPENDENCY_SECURITY.md).

## Gdzie zgłosić podatność

Po zalogowaniu na GitHubie przejdź do **Security → Advisories → Report a vulnerability**, jeśli przycisk jest dostępny. Formularz służy do poufnego kontaktu z opiekunem. Jeśli opcja prywatnego zgłoszenia jest niedostępna, otwórz ogólną prośbę o prywatny kontakt i poczekaj na odpowiedź. Prośba jest publiczna. Pozostaw jej ogólny tytuł. Szczegółów podatności, dowodów i odnośników do nich używaj wyłącznie w uzgodnionym kanale prywatnym. [Prywatny formularz GitHub](https://github.com/Yorick0499/ore-and-empire/security/advisories/new) · [Prośba o prywatny kontakt](https://github.com/Yorick0499/ore-and-empire/issues/new?template=private-contact.yml).

## Co przekazać prywatnie

- Rewizję oraz tryb instalacji, np. lokalny SQLite albo wdrożenie PostgreSQL za proxy.
- Dotkniętą funkcję, warunki potrzebne do wystąpienia problemu i obserwowany wpływ na konta, dane lub instalację.
- Zwięzły opis zachowania w odizolowanej instancji z syntetycznymi danymi. Oznacz, co sprawdzono i co jest przypuszczeniem. Jeśli z raportu pomaga skorzystać log, dołącz tylko istotny, oczyszczony fragment.

Próby prowadź na własnej instancji testowej lub za zgodą jej operatora. Dane innych graczy, hasła, tokeny, prywatne konfiguracje i pełne kopie baz trzymaj poza zgłoszeniem. Przy podejrzeniu incydentu w działającej instalacji zawiadom też jej operatora właściwym prywatnym kanałem.

## Ocena i publikacja

Opiekun potwierdza przyjęcie po odczytaniu zgłoszenia, ocenia wpływ i w razie potrzeby prosi o dalsze informacje. Priorytet zależy od wpływu i zakresu dotkniętych instalacji. Termin i zakres ujawnienia ustalcie w prywatnym wątku. Opublikuj szczegóły po skoordynowaniu ich z opiekunem, a użytkownikom udostępnij wskazówki do aktualizacji. Jeżeli potrzebny jest status, dopisz wiadomość w tym samym prywatnym wątku.
