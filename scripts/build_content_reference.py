#!/usr/bin/env python3
"""Rebuild the public default-content tables using only a disposable database."""
import argparse
from collections import Counter
from io import StringIO
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent


def table(lines, headers, rows):
    def cell(value):
        return str(value).replace('|', '&#124;').replace('\n', ' ')
    lines.append('| ' + ' | '.join(headers) + ' |')
    lines.append('|' + '|'.join('---' for _ in headers) + '|')
    lines.extend('| ' + ' | '.join(cell(value) for value in row) + ' |' for row in rows)
    lines.append('')


def build():
    from django.core.management import call_command
    from characters.world_management import seed_clean_world
    seed_clean_world()
    call_command('seed_khorinis', stdout=StringIO())
    from characters.post_barrier import seed as seed_post_barrier
    seed_post_barrier()
    from characters.locations import LOCATIONS
    from characters.bestiary import BESTIARY
    from characters.bosses import BOSSES
    from characters.camp_progression import RANKS, BY_RANK, ATTRIBUTE_NAMES
    from characters.faction_advancement import RANKS as ADVANCED
    from characters.factions import FACTIONS, RANK_NAMES
    from characters.magic import ALL_SPELLS
    from characters.models import AdventureTemplate, StoryQuest, CraftRecipe, StoreProduct, ItemBluePrint
    lines = ['# Katalog domyślnej zawartości bieżącej gry', '',
             '[Instrukcja](GAME_GUIDE.md) · [Frakcje](CAMPS.md) · [NK](GOTHIC_II_CONTENT.md) · [Indeks](INDEX.md)', '',
             'Tabele obejmują także definicje instalowane przy aktywacji Bariery. Pochodzą z bieżących katalogów kodu i seederów uruchomionych w nowej, tymczasowej bazie SQLite. '
             'Nie odczytują zapisu gracza. Odświeżanie: `python scripts/build_content_reference.py`; '
             'kontrola bez zmiany pliku: `python scripts/build_content_reference.py --check`. '
             'Wartości są bazowym balansem adaptacji; operator może zmienić definicje w swojej instalacji. '
             'Sam wpis w katalogu nie otwiera bramki poziomu, regionu, fabuły ani frakcji.', '',
             '## Zestawienie', '']
    counts = Counter(l.universe for l in LOCATIONS)
    table(lines, ['Zakres', 'Liczba'], [
        ('Lokacje łącznie', len(LOCATIONS)), *[(f'Lokacje {key}', value) for key,value in sorted(counts.items())],
        ('Populacje przeciwników do polowań', len(BESTIARY)), ('Bossowie solo', len(BOSSES)),
        ('Rodzime tożsamości rang (gałęzie)', len(RANKS)), ('Wyższe awanse pięciu frakcji', len(ADVANCED)),
        ('Zaklęcia działające (nie liczba modeli run/zwojów)', len(ALL_SPELLS)),
        ('Zlecenia czasowe', AdventureTemplate.objects.count()), ('Definicje zadań jednorazowych', StoryQuest.objects.count()),
        ('Receptury', CraftRecipe.objects.count()), ('Oferty sklepu odłamków', StoreProduct.objects.count())])
    lines += ['41 definicji G1 i 29 przedbarierowego Khorinis zawiera alternatywne gałęzie: '
              'jedna postać wykonuje odpowiednio 27 lub 17 przydziałów do głównego celu. '
              'Po Barierze dochodzą 2 pierwsze wspólne zadania, 8 Jarkendaru i 15 NK. '
              'Katalog źródłowy: 522 tożsamości G1 i 877 NK; nie każda ma aktywną mechanikę. '
              '[Wersje paczek](ITEM_PACKS.md).', '', '## Lokacje', '',
              'Poziom lokacji jest warunkiem wejścia. Kolumna bramek uzupełnia poziom i region; '
              'w przypadku walki serwer sprawdza także rzeczywistą populację terenu. '
              'Jarkendar i Irdorath korzystają z regionu podróży Khorinis, a nie osobnych serwerów.', '']
    table(lines, ['Klucz / miejsce', 'Region', 'Poziom', 'Bramki', 'Aktywność', 'Przeciwnicy'], (
        (f'{l.key} — {l.name}', l.universe, l.level,
         '; '.join(filter(None, [', '.join(l.camps), f'szczebel {l.min_tier}' if l.min_tier else '',
                                'po Barierze' if l.post_barrier else '', 'portal' if l.requires_portal else '', l.required_story])) or '—',
         l.route, ', '.join(BESTIARY[k]['nazwa'] for k in l.monsters)) for l in LOCATIONS))
    lines += ['## Przeciwnicy polowań', '', 'Poziom przeciwnika jest zaleceniem. Warianty populacji mogą współdzielić gatunek lub ilustrację. Ochrony i nagrody są balansem przeglądarkowym.', '']
    table(lines, ['Klucz / przeciwnik', 'Poziom', 'HP', 'Siła', 'Ochrona broni', 'Bazowe PD'], (
        (f'{key} — {m["nazwa"]}', m.get('level',0), m['life'], m['strength'], m['weapon_prot'], m['exp_reward']) for key,m in BESTIARY.items()))
    lines += ['## Bossowie solo', '', 'Dodatkowe bramki połączenia, portalu i odebranej fabuły wynikają z lokacji powyżej. Koszt i cooldown obowiązują również po porażce. Wspólny Śniący i wyprawy wspólnoty są osobnymi systemami: [połączenie](CHARACTERS_AND_WORLDS.md), [wyprawy](CAMP_RAIDS.md).', '']
    table(lines, ['Klucz / boss', 'Poziom', 'HP', 'Atak', 'Ochrona', 'Energia', 'Cooldown min', 'Ruda / PD'], (
        (f'{b.key} — {b.name}', b.level,b.life,b.strength,b.protection,b.energy_cost,b.cooldown_minutes,f'{b.ore} / {b.experience}') for b in BOSSES.values()))
    lines += ['## Podstawowe rangi', '', 'Cztery szczeble w każdej gałęzi. Brak rangi nie jest piątym szczeblem. Tabela zawiera warunki liczbowe i cele; dodatkowo obowiązuje [odebrana fabuła](CHARACTERS_AND_WORLDS.md). Dawna dłuższa droga Wody jest wyjątkiem zgodności istniejących zapisów.', '']
    table(lines, ['Obóz', 'Ranga', 'Poprzednia', 'Poziom', 'Bazowy atrybut', 'Ruda', 'Cele próby'], (
        (r.camp,r.name,', '.join(BY_RANK[k].name if k in BY_RANK else 'brak rangi' for k in r.parents),r.level,
         f'{ATTRIBUTE_NAMES.get(r.attribute,r.attribute)} {r.attribute_value}',r.cost,'; '.join(f'{o.label} ×{o.count}' for o in r.objectives)) for r in RANKS))
    lines += ['## Frakcje i osiem rang po Barierze', '']
    table(lines, ['Frakcja', 'Rangi 1–4', 'Nowe rangi 5–8'], ((label,' → '.join(RANK_NAMES[key][:4]),' → '.join(RANK_NAMES[key][4:])) for key,label in FACTIONS))
    lines += ['[Sukcesja i skarbce](CAMP_GUILDS.md). Wyższe awanse wymagają kolejno poziomów 30/35/40/45, opłat 500/1000/1500/2500 rudy oraz własnych prób; [pełne warunki](CAMPS.md).', '',
              '## Zlecenia czasowe', '', 'Widzisz pulę aktualnie odwiedzanego regionu: 44 G1 lub 10 Khorinis. Nagroda z premiami zapisuje się przy starcie; [zasady i wspólny odczyt podglądu](ADVENTURES.md).', '']
    table(lines, ['Klucz / zlecenie', 'Region', 'Kategoria / miejsce', 'Poziom', 'Sekundy', 'Energia', 'Ruda / PD / odłamki'], (
        (f'{q.key} — {q.name}',q.universe,f'{q.get_category_display()} / {q.place}',q.level,q.duration_seconds,q.energy_cost,f'{q.ore_reward} / {q.experience_reward} / {q.premium_reward}') for q in AdventureTemplate.objects.order_by('universe','level','key')))
    lines += ['<a id="fabula-jednorazowa"></a>', '', '## Fabuła jednorazowa', '', 'Przyjęcie → rozpoczęcie → wykonanie → odbiór. Część gałęzi wymaga konkretnej odpowiedzi lub frakcji; warunki są sprawdzane przez grę. Cele nie zaliczają wcześniejszych działań. [Opis mechaniki](STORY.md).', '']
    names = dict(ItemBluePrint.objects.values_list('pk','name'))
    for universe in ('GOTHIC_I','GOTHIC_II','JOINED'):
        lines += [f'### Fabuła {dict(GOTHIC_I="Kolonii",GOTHIC_II="Khorinis",JOINED="po Barierze")[universe]}', '']
        quests=StoryQuest.objects.filter(universe=universe).order_by('chapter','level','key')
        table(lines, ['Klucz / zadanie', 'Rozdział / poziom', 'Obóz', 'Poprzednicy', 'Cele', 'Ruda / PD / odłamki'], (
            (f'{q.key} — {q.title}',f'{q.chapter} / {q.level}',q.camp or 'wspólne',
             ', '.join(q.prerequisites)+('; jeden z: '+', '.join(q.any_prerequisites) if q.any_prerequisites else ''),
             '; '.join(f'{o.get("label",o["kind"])} ×{o.get("count",1)}' for o in q.objectives),
             f'{q.rewards.get("ore",0)} / {q.rewards.get("experience",0)} / {q.rewards.get("premium",0)}') for q in quests))
    lines += ['## Receptury', '']
    table(lines, ['Produkt', 'Umiejętność', 'Poziom', 'Opłata', 'Składniki'], (
        (r.name,f'{r.discipline} {r.skill}',r.level,r.fee,', '.join(f'{names[i["blueprint"]]} ×{i["count"]}' for i in r.ingredients)) for r in CraftRecipe.objects.order_by('key')))
    lines += ['## Zaklęcia', '', 'Runa wymaga szkoły i kręgu, zwój zużywa jedną sztukę i 1 many za rzut. Dwa czary VI kręgu należą do etapu po Barierze. [Nauka, zapasy i odporności](MAGIC.md).', '']
    table(lines, ['Klucz / zaklęcie', 'Szkoła', 'Krąg', 'Mana runy', 'Obrażenia / typ', 'Redukcja %', 'Przerwanie co N rzutów'], (
        (f'{s.key} — {s.name}',s.school_name,s.circle,s.cost,f'{s.damage} / {s.damage_name}',s.mitigation,s.stagger_every or '—') for s in ALL_SPELLS))
    lines += ['## Sklep odłamków', '', '17 definicji ofert; region i wymagania ograniczają widoczną ofertę. [Pełne limity i statystyki wyposażenia](BOT_PERSONALITIES.md). Cena dotyczy odłamków, nie pieniędzy ani konta premium.', '']
    table(lines, ['Oferta', 'Rodzaj', 'Odłamki', 'Poziom', 'Efekt / przedmiot'], (
        (p.name,p.get_kind_display(),p.price,p.level,p.blueprint.name if p.blueprint_id else p.effect) for p in StoreProduct.objects.select_related('blueprint').order_by('key')))
    lines += ['## Przedmioty, grafiki i endgame', '',
              'Pełne źródłowe rekordy i aktywne ograniczenia: [G1](../characters/data/gothic1-items.json), [NK](../characters/data/gothic2-items.json), [paczki](ITEM_PACKS.md), [grafiki i atrybucja](ASSETS.md). '
              'W grze katalog `/przedmioty/` jest stronicowany. Katalog referencyjny nie oznacza dostępności u kupca ani obsługi wszystkich oryginalnych efektów.', '',
              '[Stała rzadkość, kuźnia +3 i stare 100 wart](LOOT_AND_ENDGAME.md); [cztery regionalne ścieżki po 100 i cel tygodniowy](REGIONAL_ENDGAME.md); [wydarzenia i siedem odsłon](WORLD_UPDATES.md). '
              'Te systemy nie kasują postaci po finale ani na początku miesiąca.', '']
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    sys.path.insert(0,str(ROOT))
    from ore_empire.database import sqlite_environment
    with tempfile.TemporaryDirectory(prefix='ore-content-docs-') as temporary:
        database=Path(temporary)/'reference.sqlite3'
        os.environ.update(sqlite_environment(database))
        os.environ.update(SECRET_KEY='public-doc-build-only',DJANGO_SETTINGS_MODULE='ore_empire.settings')
        import django
        django.setup()
        from django.db import connection,connections
        if connection.vendor!='sqlite' or Path(connection.settings_dict['NAME']).resolve()!=database:
            raise SystemExit('Refusing to use a non-disposable database')
        from django.core.management import call_command
        try:
            call_command('migrate',interactive=False,stdout=StringIO())
            result=build()
        finally:
            connections.close_all()
    target=ROOT/'docs/GAME_CONTENT.md'
    if args.check:
        if target.read_text()!=result:raise SystemExit('GAME_CONTENT.md is stale; run scripts/build_content_reference.py')
        print('GAME_CONTENT.md matches the current catalogs and seeders')
    else:
        target.write_text(result)
        print('Updated docs/GAME_CONTENT.md from a disposable database')


if __name__=='__main__':main()
