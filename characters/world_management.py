"""Explicit local-world initialization/reset; administrator accounts survive a clean game."""
from pathlib import Path
from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.forms import UsernameField
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import PermissionDenied,ValidationError
from django.core.management import call_command
from django.db import connection,transaction
from django.contrib.sessions.models import Session
from .models import World,CampGuild
from .worlds import current_world,profile_for

class WorldSetupForm(forms.Form):
    name=forms.CharField(label='Nazwa świata / serwera',max_length=80)
    bot_count=forms.IntegerField(label='Liczba botów',min_value=0,max_value=20,initial=6)
    username=UsernameField(label='Login administratora',max_length=150,validators=[UnicodeUsernameValidator()])
    password=forms.CharField(label='Hasło administratora',widget=forms.PasswordInput)
    def clean(self):
        data=super().clean()
        username=data.get('username','')
        if username.startswith('colony-bot-'):self.add_error('username','Ta nazwa jest zarezerwowana dla botów.')
        if data.get('password'):
            try:validate_password(data['password'],User(username=username))
            except ValidationError as exc:self.add_error('password',exc)
        return data

class WorldSettingsForm(forms.Form):
    name=forms.CharField(label='Nazwa świata / serwera',max_length=80)
    bot_count=forms.IntegerField(label='Aktywne boty',min_value=0,max_value=20)


class WorldResetForm(forms.Form):
    name=forms.CharField(label='Nazwa nowego świata / serwera',max_length=80)
    bot_count=forms.IntegerField(label='Liczba botów',min_value=0,max_value=20,initial=6)
    password=forms.CharField(label='Twoje obecne hasło administratora',widget=forms.PasswordInput)
    confirmation=forms.CharField(label='Przepisz obecną nazwę świata')
    expected_world=forms.IntegerField(widget=forms.HiddenInput)
    acknowledge=forms.BooleanField(label='Rozumiem: postacie, konta graczy i postęp zostaną usunięte. Konta administratorów i kopia zapisu pozostaną.')


def seed_clean_world():
    from io import StringIO
    output=StringIO()
    world=current_world()
    for camp in ('OLD_CAMP','NEW_CAMP','SWAMP_CAMP'):CampGuild.objects.get_or_create(world=world,camp=camp)
    for command in ('seed_world','seed_equipment','seed_catalog','seed_crafting','seed_adventures','seed_story'):call_command(command,stdout=output)


@transaction.atomic
def initialize_world(name,bot_count,username,password):
    world=World.objects.select_for_update().get(pk=current_world().pk)
    if world.configured or User.objects.filter(is_superuser=True).exists():raise PermissionDenied('Pierwsza inicjalizacja jest już zamknięta. Zaloguj się jako administrator.')
    form=WorldSetupForm({'name':name,'bot_count':bot_count,'username':username,'password':password})
    if not form.is_valid():raise ValidationError(form.errors)
    name=form.cleaned_data['name'];username=form.cleaned_data['username'];password=form.cleaned_data['password']
    if User.objects.filter(username=username).exists():raise ValidationError('Login jest już zajęty; nie zmieniono uprawnień konta.')
    world.name=name.strip();world.bot_count=bot_count;world.configured=True;world.save()
    admin=User.objects.create_superuser(username=username,password=password)
    seed_clean_world()
    from io import StringIO
    if bot_count:call_command('run_bots',create=bot_count,create_only=True,limit=bot_count,stdout=StringIO())
    return admin


def reset_world(actor,*,name,bot_count,password,confirmation,expected_world):
    from .backups import create_backup
    actor=User.objects.get(pk=actor.pk)
    world=current_world()
    if not actor.is_active or not actor.is_superuser or not actor.check_password(password):raise PermissionDenied('Podaj poprawne hasło administratora.')
    if confirmation!=world.name or expected_world!=world.pk:raise ValidationError('Nazwa potwierdzenia lub wersja świata nie zgadza się. Odśwież formularz.')
    if not name.strip() or len(name)>80 or type(bot_count)is not int or not 0<=bot_count<=20:raise ValidationError('Niepoprawna nazwa lub liczba botów.')
    if connection.vendor!='sqlite':raise ValidationError('Reset dostępny dla lokalnego SQLite; procedura PostgreSQL wymaga osobnego wdrożenia.')
    backup=create_backup(settings.DATABASES['default']['NAME'],settings.BASE_DIR/'backups')
    with transaction.atomic():
        locked=World.objects.select_for_update().get(pk=world.pk)
        if locked.pk!=current_world().pk:raise ValidationError('Świat zmienił się podczas operacji.')
        from django.apps import apps
        # Whole game reset. FK checks remain enabled; Django's deferred constraints
        # validate the complete replacement at commit. Auth/permissions/migrations remain.
        for model in reversed(list(apps.get_app_config('characters').get_models())):
            with connection.cursor() as cursor:cursor.execute('DELETE FROM '+connection.ops.quote_name(model._meta.db_table))
        User.objects.filter(is_superuser=False).delete()
        Session.objects.all().delete()
        fresh=World.objects.create(name=name.strip(),bot_count=bot_count,edition=locked.edition+1,is_current=True,configured=True)
        for admin in User.objects.filter(is_superuser=True):profile_for(admin)
        seed_clean_world()
        from io import StringIO
        if bot_count:call_command('run_bots',create=bot_count,create_only=True,limit=bot_count,stdout=StringIO())
    return fresh,backup.name
