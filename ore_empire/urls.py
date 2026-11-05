"""
URL configuration for ore_empire project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from characters.views import (
    register_view,
    item_catalog_view, economy_balance_view, world_monitor_view, magic_view, camp_guild_view,world_setup_view,world_control_view,characters_view,challenges_view,crafting_view,
    tavern_view, colony_life_view, story_view,
    bestiary_view,
    camp_view,
    adventures_view, itemshop_view, events_view, rankings_view, game_master_view,
    credits_view,
    locations_view,
    market_monitor_view,
    boss_view,
)
from characters.views import (
    hunt_view,
    inventory_view,
    market_view,
    mine_view,
    shop_view,
    train_view,
)


from characters.views import journal_view, battle_detail_view, hall_view

urlpatterns = [
    path("sala-chwaly/", hall_view, name="hall_page"),
    path("dziennik/", journal_view, name="journal_page"),
    path("dziennik/walka/<int:battle_id>/", battle_detail_view, name="battle_detail"),
    path("rzemioslo/",crafting_view,name="crafting_page"),
    path("wyzwania/",challenges_view,name="challenges_page"),
    path("inicjalizacja/",world_setup_view,name="world_setup"),
    path("zarzadca/swiat/reset/",world_control_view,name="world_control"),
    path("postacie/",characters_view,name="characters_page"),
    path("wspolnota/", camp_guild_view, name="camp_guild"),
    path("magia/", magic_view, name="magic_page"),
    path("zarzadca/swiat/", world_monitor_view, name="world_monitor"),
    path("zarzadca/gospodarka/", economy_balance_view, name="economy_balance"),
    path("przedmioty/", item_catalog_view, name="item_catalog"),
    path("fabula/", story_view, name="story_page"),
    path("karczma/", tavern_view, name="tavern_page"),
    path("zycie-kolonii/", colony_life_view, name="colony_life"),
    path("zarzadca/", game_master_view, name="game_master"),
    path("zadania/", adventures_view, name="adventures_page"),
    path("sklep-odlamkow/", itemshop_view, name="itemshop_page"),
    path("wydarzenia/", events_view, name="events_page"),
    path("rankingi/", rankings_view, name="rankings_page"),
    path("oboz/", camp_view, name="camp_page"),
    path("bestiariusz/", bestiary_view, name="bestiary_page"),
    path("zrodla/", credits_view, name="credits_page"),
    path("", locations_view, name="locations_page"),
    path("konto/rejestracja/", register_view, name="register"),
    path("konto/logowanie/", auth_views.LoginView.as_view(), name="login"),
    path("konto/wylogowanie/", auth_views.LogoutView.as_view(), name="logout"),
    path("rynek/monitor/", market_monitor_view, name="market_monitor"),
    path("wyprawa/", boss_view, name="boss_page"),
    path("admin/", admin.site.urls),
    path("kopalnia/", mine_view, name="mine_page"),
    path("polowanie/", hunt_view, name="hunt_page"),
    path("plac_targowy/", market_view, name="market_page"),
    path("ekwipunek/", inventory_view, name="inventory_page"),
    path("sklep/", shop_view, name="shop_page"),
    path("trening/", train_view, name="train_page"),
]
