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
    tavern_view, colony_life_view,
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


urlpatterns = [
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
