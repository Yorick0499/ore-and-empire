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
from characters.views import register_view, locations_view, market_monitor_view
from characters.views import (
    hunt_view,
    inventory_view,
    market_view,
    mine_view,
    shop_view,
    train_view,
)


urlpatterns = [
    path("", locations_view, name="locations_page"),
    path("konto/rejestracja/", register_view, name="register"),
    path("konto/logowanie/", auth_views.LoginView.as_view(), name="login"),
    path("konto/wylogowanie/", auth_views.LogoutView.as_view(), name="logout"),
    path("rynek/monitor/", market_monitor_view, name="market_monitor"),
    path("admin/", admin.site.urls),
    path("kopalnia/", mine_view, name="mine_page"),
    path("polowanie/", hunt_view, name="hunt_page"),
    path("plac_targowy/", market_view, name="market_page"),
    path("ekwipunek/", inventory_view, name="inventory_page"),
    path("sklep/", shop_view, name="shop_page"),
    path("trening/", train_view, name="train_page"),
]
