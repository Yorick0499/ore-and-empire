# Utrzymanie bezpieczeństwa zależności

## Co sprawdzamy

| Źródło | Zakres |
|---|---|
| `requirements.txt` | Gra i wdrożenie WSGI. Django, WhiteNoise, Gunicorn, psycopg z binariami, biblioteki danych i grafiki, stubs oraz zależności przechodnie rozwiązywane przez pip. |
| `requirements-docs.txt`, `requirements-audit.txt` | Generator dokumentacji i narzędzie audytu wraz z zależnościami przechodnimi. Każdy manifest ma odrębny raport. |
| `Dockerfile`, `deploy/compose.production.yml`, `deploy/Dockerfile.proxy` | Zbudowany obraz gry (Python 3.12 na Debianie Trixie z klientem PostgreSQL), `postgres:17` i obraz proxy z `caddy:2-alpine` z poprawkami Alpine. |
| `.github/workflows/` | Obraz PostgreSQL 16 z testów i zewnętrzne akcje przypięte do pełnego SHA. Przy przeglądzie akcji sprawdź wydania upstream oraz GitHub Advisory Database (ekosystem `actions`). |

[Dependency audit](https://github.com/Yorick0499/ore-and-empire/actions/workflows/dependency-audit.yml) działa w poniedziałki o 05:19 UTC, na żądanie i w PR-ach zmieniających pliki zależności lub CI. `pip-audit` odpytuje bazę PyPI po rozwiązaniu zależności. Sprawdza aplikację na Linuksie na Pythonie 3.12 i 3.13 oraz na Windows na 3.13. Wykryta podatność albo błąd skanu Pythona oznacza nieudane zadanie. Grype sprawdza pakiety systemowe i rozpoznane biblioteki w kontenerach. Jego błąd kończy zadanie niepowodzeniem. Wyniki kontenerów są informacyjne. Raport wyróżnia wysokie lub krytyczne podatności, dla których Grype wskazuje poprawkę. Artefakty JSON i identyfikatory przeskanowanych obrazów są dostępne przez 14 dni. Tagi obrazów mogą wskazywać z czasem nowe wydania.

[Dependabot](https://github.com/Yorick0499/ore-and-empire/blob/main/.github/dependabot.yml) co tydzień szuka nowych wersji pakietów PyPI, obrazów i akcji GitHub. Alerty i PR-y naprawcze dla podatności są osobnymi ustawieniami GitHuba. Informację o ich stanie pozostaw jako niezweryfikowaną, jeśli nie masz dostępu do ustawień. [Dokumentacja ustawień Dependabota](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/manage-your-dependency-security/configuring-dependabot-security-updates).

## Procedura audytu i aktualizacji

1. Odczytaj `AGENTS.md`, zanotuj `git rev-parse HEAD` i najnowszy udany audyt. Pracuj na osobnej gałęzi. Powtórz skany z bieżącymi bazami podatności. Zachowaj raporty tymczasowo poza repo. Przy braku sieci, bazy lub dostępu do wyników wskaż, którego zakresu nie zweryfikowano.
2. Grupuj powtórzone identyfikatory według aliasów CVE/GHSA. Dla istotnych wyników ustal z komunikatu producenta: wersje objęte problemem, wpływ na używane funkcje, wersję z poprawką oraz ewentualne wymagania nowego wydania. Dla obrazu porównaj identyfikator z artefaktu i wersję pakietu z biuletynem dystrybucji. Dla akcji sprawdź SHA wskazany przez oficjalny tag. Udokumentuj doraźne ograniczenie wpływu i termin ponownego sprawdzenia, jeśli brakuje poprawki.
3. Wybierz wspieraną wersję z poprawką. Zaczynaj od aktualizacji w ramach aktualnej serii. Większe migracje prowadź w osobnym PR. Z oficjalnych uwag do wydania wypisz zmiany konfiguracji, API, schematu i wymaganej wersji Pythona lub bazy. Dla zmiany zależności przechodniej sprawdź ograniczenia pakietu, który ją wprowadza. Po instalacji uruchom `python -m pip check` i powtórz skan.
4. Sprawdź `python manage.py check`, `python manage.py makemigrations --check --dry-run` i testy obszaru zmienionej biblioteki. Dla Django, sterownika bazy lub silnika przetestuj start na pustej bazie, zachowanie starego zapisu, próbne odtworzenie oraz CI na SQLite i PostgreSQL. Dla obrazu lub proxy sprawdź budowanie, start i kontrolę zdrowia. Dla aktualizacji akcji sprawdź oba workflowy na tej samej rewizji PR-a. Regresje napraw i ponów testy przed scaleniem.
5. Przed wdrożeniem zmiany dotykającej danych zapisz poprzednią rewizję lub digest obrazu. Sprawdź kopię i odtwórz ją do osobnej bazy. Próbę aktualizacji i powrotu przeprowadź na kopii. Gdy zmiany schematu nie da się odwrócić, plan powrotu obejmuje poprzednią wersję kodu i odtworzenie zgodnej kopii. Podsumuj zmiany, testy, wynik ponownego audytu i pozostałe ryzyka w PR. Szczegóły instalacji i zasady zgłaszania podatności dokumentują [produkcja](PRODUCTION.md), [kopie i odtwarzanie](BACKUPS.md) oraz [polityka bezpieczeństwa](../SECURITY.md).

### Skan Python poza CI

Polecenia dla Bash z katalogu repo. Audytor instaluje się w tymczasowym środowisku, a raporty zostają w prywatnym katalogu tej próby. Każde uruchomienie zgłasza własny kod wyjścia.

```bash
audit_dir=$(mktemp -d)
python -m venv "$audit_dir/venv"
"$audit_dir/venv/bin/python" -m pip install -r requirements-audit.txt
for manifest in requirements.txt requirements-docs.txt requirements-audit.txt; do
  "$audit_dir/venv/bin/python" -m pip_audit --strict -r "$manifest" \
    -f json -o "$audit_dir/${manifest%.txt}.json"
  printf '%s: kod wyjścia %s\n' "$manifest" "$?"
done
printf 'Raporty: %s\n' "$audit_dir"
```

### Polecenie dla agenta

> Wykonaj audyt zależności Ore & Empire według `docs/DEPENDENCY_SECURITY.md`. Sprawdź manifesty Pythona, obrazy i akcje dla bieżącej rewizji. Potwierdź istotne wyniki w komunikatach producentów, wprowadź bezpieczne poprawki na osobnej gałęzi i powtórz skany oraz testy. W podsumowaniu podaj wersje przed i po, CVE/GHSA, wpływ na grę, wymagania migracji, wyniki CI i ryzyka pozostałe do sprawdzenia.

## Audyt początkowy · 27 listopada 2026

Na bazie `39aa253` lokalny skan Linux/Python 3.12 rozwiązał 18 pakietów gry i jeden pakiet dokumentacji. W grze wskazał siedem odrębnych zgłoszeń. Po aktualizacji skan tych samych manifestów nie zgłosił podatności:

| Pakiet | Zmiana | Wynik i zgodność |
|---|---|---|
| Django | `6.0.7` → `6.0.10` | Skan wskazał `CVE-2026-15307` i `CVE-2026-15830`. Wydania 6.0.9 i 6.0.10 zawierają kolejne poprawki bezpieczeństwa. Zmiana kompatybilności wyszukiwania przestrzennego nie dotyczy używanych modeli gry. [6.0.8](https://docs.djangoproject.com/en/6.0/releases/6.0.8/) · [6.0.9](https://docs.djangoproject.com/en/6.0/releases/6.0.9/) · [6.0.10](https://docs.djangoproject.com/en/6.0/releases/6.0.10/). |
| sqlparse | `0.5.5` → `0.6.1` | Pięć zgłoszeń dotyczących nadmiernego zużycia zasobów przy przetwarzaniu SQL poprawiono w 0.6.0. Wydanie 0.6.1 zawiera dalsze poprawki i kończy utrzymanie parsera. Django nadal go wymaga. W kolejnych audytach sprawdzaj stanowisko Django i dostępność wspieranej ścieżki aktualizacji. [Historia wydań](https://github.com/andialbrecht/sqlparse/blob/0.6.1/CHANGELOG). |

W obrazie Caddy 2.11.9 audyt wskazał poprawki dla `zlib`, `libcrypto3` i `libssl3`. Obraz proxy instaluje aktualizacje pakietów Alpine przy budowie. Dwa zgłoszenia dotyczą modułów skompilowanych z Caddy. `GO-2026-6860` dotyczy parsowania HTML, a `GO-2026-6865` dekodowania Zstandard. Domyślna konfiguracja proxy przekazuje żądania i kompresuje odpowiedzi. Przy następnym wydaniu Caddy sprawdź wersje modułów i powtórz skan obrazu. [Alpine](https://security.alpinelinux.org/vuln/CVE-2026-4738) · [GO-2026-6860](https://pkg.go.dev/vuln/GO-2026-6860) · [GO-2026-6865](https://pkg.go.dev/vuln/GO-2026-6865).

Wynik skanu opisuje stan bazy podatności z chwili uruchomienia. Wnioski dotyczące kontenerów opieraj na raportach z ich rzeczywistymi identyfikatorami.
