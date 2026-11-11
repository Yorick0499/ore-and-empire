#!/usr/bin/env python3
"""Build/check one offline HTML book from an explicit public-source allowlist.

No Django initialization, private configuration, database or credential reads.
Install requirements-docs.txt in a documentation build environment.
"""
import argparse
import base64
import hashlib
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import quote, unquote, urlsplit
import markdown

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / 'docs/public'
OUTPUT = ROOT / 'docs/dokumentacja.html'


def slug(value):
    return re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')


def data_uri(path):
    if not path.is_file():
        raise ValueError(f'Missing public asset: {path.relative_to(ROOT)}')
    mime = {'.jpg':'image/jpeg','.jpeg':'image/jpeg','.png':'image/png','.webp':'image/webp','.ttf':'font/ttf'}[path.suffix.lower()]
    return f'data:{mime};base64,' + base64.b64encode(path.read_bytes()).decode('ascii')


class Rewrite(HTMLParser):
    def __init__(self, source, chapter_id, chapters, reports, screens):
        super().__init__(convert_charrefs=False)
        self.source, self.chapter_id = source, chapter_id
        self.chapters, self.reports, self.screens = chapters, reports, screens
        self.parts = []

    def link(self, value):
        parts = urlsplit(value)
        if parts.scheme or parts.netloc:
            if parts.scheme not in {'http', 'https', 'mailto', 'data'}:
                raise ValueError(f'Unsupported public link: {value}')
            return value
        if not parts.path:
            return '#' + self.chapter_id + ('--' + unquote(parts.fragment) if parts.fragment else '')
        if parts.path.startswith('/'):
            return 'http://127.0.0.1:8001' + value
        path = (self.source.parent / unquote(parts.path)).resolve()
        if not path.is_relative_to(ROOT):
            raise ValueError('Public link escapes repository')
        if path == OUTPUT:
            return '#top'
        if path in self.chapters:
            return '#' + self.chapters[path] + ('--' + unquote(parts.fragment) if parts.fragment else '')
        if path in self.reports:
            return '#' + self.reports[path]
        if path in self.screens:
            return '#' + self.screens[path]
        relative = path.relative_to(ROOT).as_posix()
        kind = 'tree' if path.is_dir() else 'blob'
        return 'https://github.com/Yorick0499/ore-and-empire/' + kind + '/main/' + quote(relative, safe='/')

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.parts.append('<div class="table-wrap" role="region" aria-label="Tabela dokumentacji — przewijaj w poziomie" tabindex="0">')
        attrs = dict(attrs)
        if 'id' in attrs:
            attrs['id'] = self.chapter_id + '--' + attrs['id']
        if 'href' in attrs:
            attrs['href'] = self.link(attrs['href'])
            if attrs['href'].startswith(('http:', 'https:')):
                attrs.update(target='_blank', rel='noopener noreferrer')
        if tag == 'img':
            src = attrs.get('src', '')
            if urlsplit(src).scheme:
                raise ValueError('External images are not permitted in the offline book')
            path = (self.source.parent / unquote(src)).resolve()
            if path not in self.screens:
                raise ValueError(f'Image is not in the public screenshot allowlist: {src}')
            attrs.update(src=data_uri(path), loading='lazy', decoding='async')
        if re.fullmatch(r'h[1-5]', tag):
            tag = 'h' + str(int(tag[1]) + 1)
        rendered = ''.join(' ' + key + ('' if value is None else '="' + escape(value, quote=True) + '"') for key, value in attrs.items())
        self.parts.append('<' + tag + rendered + '>')

    def handle_endtag(self, tag):
        original = tag
        if re.fullmatch(r'h[1-5]', tag):
            tag = 'h' + str(int(tag[1]) + 1)
        self.parts.append('</' + tag + '>')
        if original == 'table':
            self.parts.append('</div>')

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_data(self, data): self.parts.append(data)
    def handle_entityref(self, name): self.parts.append('&' + name + ';')
    def handle_charref(self, name): self.parts.append('&#' + name + ';')


class Validate(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids = set(); self.links = []; self.assets = []; self.errors = []; self.inline = {'style': 0, 'script': 0}
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            if attrs['id'] in self.ids: self.errors.append('Duplicate id: ' + attrs['id'])
            self.ids.add(attrs['id'])
        if tag == 'a' and attrs.get('href', '').startswith('#'): self.links.append(attrs['href'][1:])
        if tag in {'img', 'script', 'link'} and ('src' in attrs or 'href' in attrs):
            url = attrs.get('src', attrs.get('href'))
            if not url.startswith('data:'): self.errors.append('Non-embedded rendering dependency: ' + url)
        if tag == 'img' and not attrs.get('alt'): self.errors.append('Image without alternate text')
        if tag in self.inline: self.inline[tag] += 1
    def finish(self):
        self.errors.extend('Missing internal target: ' + value for value in self.links if value not in self.ids)
        if self.inline != {'style': 1, 'script': 1}: self.errors.append('Expected one embedded stylesheet and script')
        if self.errors: raise ValueError('\n'.join(self.errors))


def build():
    manifest = json.loads((PUBLIC / 'manifest.json').read_text(encoding='utf-8'))
    entries = [(group['title'], path, title) for group in manifest['groups'] for path, title in group['chapters']]
    chapters = {(ROOT / path).resolve(): 'doc-' + slug(Path(path).stem) for _, path, _ in entries}
    if len(chapters) != len(entries): raise ValueError('Duplicate public chapter')
    expected = {p.resolve() for p in (ROOT / 'docs').glob('*.md')}
    if not expected.issubset(chapters): raise ValueError('Missing documentation chapters: ' + str(expected - chapters.keys()))
    screen_manifest = json.loads((ROOT / 'docs/screenshots/manifest.json').read_text(encoding='utf-8'))
    screenshots = {(ROOT / 'docs/screenshots' / row['file']).resolve(): 'screen-' + slug(Path(row['file']).stem) for row in screen_manifest['files']}
    report_paths = [(ROOT / path).resolve() for path in manifest['reports']]
    if any(not p.is_relative_to(ROOT / 'docs/reports') or p.suffix != '.json' or p.name.startswith('.') for p in report_paths): raise ValueError('Invalid public report path')
    if set(report_paths) != {p.resolve() for p in (ROOT / 'docs/reports').glob('*.json')}: raise ValueError('Review and list every public report explicitly in docs/public/manifest.json')
    reports = {p.resolve(): 'report-' + slug(p.stem) for p in report_paths}
    styles = (PUBLIC / 'book.css').read_text(encoding='utf-8').replace('__FONT__', data_uri(ROOT / 'characters/static/characters/fonts/GothicII.ttf')).replace('__HERO__', data_uri(ROOT / 'characters/static/characters/art/xardas_tower.webp'))
    script = (PUBLIC / 'book.js').read_text(encoding='utf-8')
    script_hash = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
    articles, navigation = [], []
    for group in manifest['groups']:
        nav = []
        for path, title in group['chapters']:
            source = (ROOT / path).resolve(); chapter_id = chapters[source]
            if not source.is_file(): raise ValueError(f'Missing public source: {path}')
            if source != ROOT / 'README.md' and (not source.is_relative_to(ROOT / 'docs') or source.suffix != '.md'): raise ValueError('Source is not public Markdown')
            raw = source.read_text(encoding='utf-8')
            html = markdown.markdown(raw, extensions=['tables', 'fenced_code', 'sane_lists', 'toc'])
            rewrite = Rewrite(source, chapter_id, chapters, reports, screenshots); rewrite.feed(html)
            note = ''
            if group['title'] == 'Archiwum projektu':
                note = '<aside class="history-note">Archiwum rozwoju. Instrukcje i liczby odnoszą się do opisanej rewizji; aktualna obsługa jest w podręczniku instalacji i zarządcy.</aside>'
            elif Path(path).name in {'ECONOMY.md', 'BOT_PERFORMANCE.md', 'BUG_AUDIT.md', 'SOLO_PLAYTEST.md'}:
                note = '<aside class="history-note">Rozdział zawiera datowane wyniki i modele. Wynik historyczny nie jest prognozą obecnego świata; aktualne reguły są opisane w odpowiednich sekcjach.</aside>'
            articles.append(f'<article id="{chapter_id}" class="chapter" data-doc-section tabindex="-1"><div class="chapter-meta"><span>{escape(group["title"])}</span><span>{escape(path)}</span><a href="{manifest["repository"]}/blob/main/{path}" target="_blank" rel="noopener noreferrer">Źródło Markdown ↗</a></div>{note}{"".join(rewrite.parts)}</article>')
            nav.append(f'<li><a href="#{chapter_id}">{escape(title)}</a></li>')
        navigation.append('<details open><summary>' + escape(group['title']) + '</summary><ol>' + ''.join(nav) + '</ol></details>')
    dependencies = (ROOT / 'requirements.txt').read_text(encoding='utf-8').strip()
    commands = sorted(p.stem for p in (ROOT / 'characters/management/commands').glob('*.py') if not p.name.startswith('_'))
    command_groups = {
        'Uruchomienie i kontrola': ['run_colony', 'run_worker', 'run_bots', 'check_worker', 'bootstrap_world', 'create_game_admin', 'open_khorinis', 'prepare_convergence', 'barrier_transition'],
        'Dane i utrzymanie': ['backup_world', 'restore_world', 'import_sqlite_world', 'archive_bot_history', 'validate_content', 'economy_report'],
        'Katalogi i grafiki': [c for c in commands if c.startswith('seed_')] + ['import_gothicpedia', 'import_khorinis_assets'],
        'Symulacje i pomiary': [c for c in commands if c.startswith('simulate_') or c.startswith('benchmark_')],
    }
    if set(commands) != {c for values in command_groups.values() for c in values}: raise ValueError('Uncategorized command')
    rows = ''.join(f'<tr><td>{escape(group)}</td><td>' + '<br>'.join('<code>python manage.py ' + escape(c) + ' --help</code>' for c in values) + '</td></tr>' for group, values in command_groups.items())
    articles.append('<article id="dependencies" class="chapter" data-doc-section tabindex="-1"><div class="chapter-meta">Dodatek techniczny · requirements.txt i komendy projektu</div><h2>Zależności i komendy</h2><p>Dokładne deklaracje pakietów bieżącego kodu. Podstawowy interfejs jest renderowany przez Django; Node.js i płatne API nie są wymagane. Listę opcji każdej komendy odczytasz przez <code>--help</code>. Przed wykonaniem komendy sprawdź, czy dotyczy żywego świata czy izolowanego testu.</p><pre><code>' + escape(dependencies) + '</code></pre><div class="table-wrap" role="region" aria-label="Komendy projektu" tabindex="0"><table><thead><tr><th>Grupa</th><th>Dostępna pomoc</th></tr></thead><tbody>' + rows + '</tbody></table></div><h3>Odtworzenie tej księgi</h3><p>Narzędzie dokumentacji jest oddzielne od runtime gry. Z katalogu repozytorium:</p><pre><code>python -m pip install -r requirements-docs.txt\npython scripts/build_public_docs.py\npython scripts/build_public_docs.py --check</code></pre><p>Źródła: publiczne Markdown, manifest i motyw w <code>docs/public/</code>. Generator nie inicjalizuje Django, nie odczytuje prywatnego środowiska, kont, baz ani backupów. Sam gotowy plik HTML nie wymaga Pythona ani instalowania pakietów.</p></article>')
    figures = []
    for row in screen_manifest['files']:
        path = (ROOT / 'docs/screenshots' / row['file']).resolve()
        if not path.is_relative_to(ROOT / 'docs/screenshots'): raise ValueError('Invalid screenshot path')
        if hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']: raise ValueError('Screenshot manifest mismatch: ' + row['file'])
        title = path.stem.replace('-', ' ').replace('_', ' ')
        date = row.get('captured_at_utc', '').split('T')[0]
        fixture = row.get('fixture', screen_manifest.get('fixture', 'Świat testowy'))
        figures.append(f'<figure id="{screenshots[path]}"><button type="button" class="zoom" data-zoom aria-label="Powiększ: {escape(title)}"><img src="{data_uri(path)}" alt="{escape(title)} — ekran demonstracyjny Ore &amp; Empire" loading="lazy" decoding="async"></button><figcaption><strong>{escape(title)}</strong>{escape(date)} · {escape(row["file"])}<br>{escape(fixture)}</figcaption></figure>')
    articles.append('<article id="gallery" class="chapter" data-doc-section tabindex="-1"><div class="chapter-meta">Dodatek wizualny · lokalne zrzuty demonstracyjne</div><h2>Galeria interfejsu</h2><p>Wszystkie zrzuty z publicznego manifestu. Są to światy testowe; daty poszczególnych ekranów mogą się różnić. Zasoby i poziomy postaci demonstracyjnych nie są obietnicą stanu startowego. Kliknij obraz, aby go powiększyć.</p><div class="gallery">' + ''.join(figures) + '</div></article>')
    report_html = []
    for path in report_paths:
        data = json.loads(path.read_text(encoding='utf-8'))
        pretty = json.dumps(data, ensure_ascii=False, indent=2)
        report_html.append(f'<details class="report" id="{reports[path.resolve()]}"><summary>{escape(path.name)}</summary><pre><code>{escape(pretty)}</code></pre><button type="button" class="download" data-report-download="{escape(path.name)}">Pobierz publiczny raport JSON</button></details>')
    articles.append('<article id="reports" class="chapter" data-doc-section tabindex="-1"><div class="chapter-meta">Dodatek źródłowy · docs/reports/</div><h2>Publiczne raporty i wyniki</h2><p>Jawne wyniki testów, kontroli GUI i modeli z repozytorium. Każdy raport zachowuje własną datę, rewizję, założenia i ograniczenia. Dawne wyniki opisują dawną wersję. Nie są to eksporty prywatnych baz ani gwarancja wydajności hostingu. Raporty są osadzone w tym pliku i dostępne offline.</p>' + ''.join(report_html) + '</article>')
    nav_extra = '<details open><summary>Dodatki offline</summary><ol><li><a href="#dependencies">Zależności i wszystkie komendy</a></li><li><a href="#gallery">Galeria ' + str(len(figures)) + ' ekranów</a></li><li><a href="#reports">Publiczne raporty (' + str(len(report_paths)) + ')</a></li></ol></details>'
    total = len(entries) + 3
    doc = f'''<!doctype html>
<html lang="pl" class="no-js"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="theme-color" content="#141619"><meta name="description" content="Pełna publiczna dokumentacja Ore & Empire: instalacja, restart, zarządca, rozgrywka, boty, katalogi i operacje serwera."><meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; font-src data:; style-src 'unsafe-inline'; script-src 'sha256-{script_hash}'; connect-src 'none'; base-uri 'none'; form-action 'none'"><title>{escape(manifest['title'])}</title><style>{styles}</style></head>
<body><a class="skip" href="#main">Przejdź do treści dokumentacji</a><header class="topbar"><a class="brand" href="#top">Ore &amp; Empire<small>Publiczna księga projektu</small></a><div class="bar-actions"><span class="edition">GOTHIC I · EDYCJA PIERWSZA</span><a href="{manifest['repository']}" target="_blank" rel="noopener noreferrer">Repozytorium ↗</a><button type="button" id="menu-toggle" class="menu-button" aria-expanded="false" aria-controls="book-navigation">Spis treści</button><button type="button" id="print-book">Drukuj / PDF</button></div></header>
<div class="layout"><aside class="rail" id="book-navigation" aria-label="Nawigacja dokumentacji"><p class="rail-title">Przewodnik po księdze</p><label for="book-search" class="search-label">Szukaj w dokumentacji</label><input id="book-search" class="search" type="search" placeholder="restart, boty, rzadkość…" autocomplete="off" aria-describedby="search-status"><output id="search-status" class="search-status" aria-live="polite">Liczba rozdziałów i dodatków: {total}.</output><nav aria-label="Spis treści">{''.join(navigation)}{nav_extra}</nav><p class="rail-note">Wersja dokumentacji: {escape(manifest['date'])}<br>Kod gry: {escape(manifest['code_revision'])}<br>Migracja: {escape(manifest['migration'].split('_', 1)[0])}<br>Odczyt offline · bez usług zewnętrznych</p></aside>
<main id="main"><section class="hero" id="top"><span class="eyebrow">Archiwum Górniczej Doliny</span><h1>Kronika projektu.<br>Wszystko o Kolonii.</h1><p class="lead">Od pierwszego uruchomienia do zarządzania żyjącym światem. Kompletna dokumentacja gry, jej reguł, technologii i narzędzi — w jednej publicznej księdze.</p><div class="meta"><span class="tag">Python + Django</span><span class="tag">250 botów · dwa światy</span><span class="tag">7 osobowości</span><span class="tag">SQLite / PostgreSQL</span><span class="tag">Europe/Warsaw</span></div><p class="hero-foot">Stan: {escape(manifest['date'])} · kod {escape(manifest['code_revision'])} · migracja {escape(manifest['migration'].split('_', 1)[0])} · fanowska adaptacja Gothic</p></section>
<div class="quick-grid"><a href="#doc-operator-guide--wymagania-i-instalacja-lokalna"><b>Uruchom grę</b><span>Instalacja, pierwsze konto i zapis świata</span></a><a href="#doc-operator-guide--zatrzymanie-i-restart-bez-kasowania-swiata"><b>Wróć do Kolonii</b><span>Bezpieczny restart bez utraty postępu</span></a><a href="#doc-operator-guide--panel-zarzadcy-krok-po-kroku"><b>Zarządzaj światem</b><span>Przedmioty, rzadkości, boty i administrator</span></a></div>
<p class="book-intro">Dokumenty źródłowe: {len(entries)}. Dalej: pełne zależności i komendy, {len(figures)} zrzutów oraz {len(report_paths)} raportów. Wszystko osadzone w HTML. Zewnętrzne źródła i GitHub otwierają się osobno. Publiczne instrukcje nie zawierają haseł ani prywatnego zapisu świata.</p><noscript><p class="history-note">Czytasz wersję bez JavaScriptu: treść i spis działają. Wyszukiwanie, kopiowanie, powiększanie i pobieranie raportów wymagają JavaScriptu. Drukowanie otworzysz skrótem Ctrl+P.</p></noscript><div id="no-results" class="no-results" hidden>Brak pasujących rozdziałów. Zmień słowa lub wyczyść wyszukiwarkę klawiszem Escape.</div>{''.join(articles)}</main></div>
<footer class="footer">Ore &amp; Empire ◆ Kroniki Kolonii<br>Projekt fanowski, niezwiązany oficjalnie z właścicielami marki Gothic.<br>Ilustracje Gothicpedii i font Gothic II mają wskazane źródła w rozdziale o grafikach. Dokumentacja nie nadaje praw do oryginalnych materiałów gry.</footer><dialog id="screen-dialog" aria-label="Powiększony zrzut ekranu"><div class="dialog-header"><span>Archiwum obrazów Kolonii</span><button type="button">Zamknij</button></div><p></p><img alt="Powiększony ekran gry"></dialog><div id="action-status" class="status" role="status" aria-live="polite"></div><script>{script}</script></body></html>'''
    # Heading slugs follow Python-Markdown's actual output; repair quick links from actual IDs.
    for expected, heading in [
        ('wymagania-i-instalacja-lokalna', 'Wymagania i instalacja lokalna'),
        ('zatrzymanie-i-restart-bez-kasowania-swiata', 'Zatrzymanie i restart — bez kasowania świata'),
        ('panel-zarzadcy-krok-po-kroku', 'Panel zarządcy — krok po kroku'),
    ]:
        from markdown.extensions.toc import slugify
        doc = doc.replace('#doc-operator-guide--' + expected, '#doc-operator-guide--' + slugify(heading, '-'))
    validate = Validate(); validate.feed(doc); validate.finish()
    metadata = {'schema': 1, 'title': manifest['title'], 'date': manifest['date'], 'code_revision': manifest['code_revision'], 'migration': manifest['migration'], 'chapters': len(entries), 'screenshots': len(figures), 'reports': len(report_paths), 'html_bytes': len(doc.encode()), 'sha256': hashlib.sha256(doc.encode()).hexdigest(), 'offline': True, 'source_files': [path for _, path, _ in entries]}
    return doc, metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Verify generated files without overwriting them.')
    args = parser.parse_args()
    html, metadata = build(); metadata_text = json.dumps(metadata, ensure_ascii=False, indent=2) + '\n'
    manifest_path = PUBLIC / 'build.json'
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding='utf-8') != html or not manifest_path.exists() or manifest_path.read_text(encoding='utf-8') != metadata_text:
            raise SystemExit('Public HTML is stale. Run python scripts/build_public_docs.py and commit both generated files.')
        print(f'Public HTML verified: {metadata["chapters"]} chapters, {metadata["screenshots"]} screenshots, {metadata["reports"]} reports; all local targets and embedded assets valid.')
    else:
        OUTPUT.write_text(html,encoding='utf-8',newline='\n'); manifest_path.write_text(metadata_text,encoding='utf-8',newline='\n')
        print(f'Written {OUTPUT}: {metadata["html_bytes"]:,} bytes; standalone offline document.')

if __name__ == '__main__': main()
