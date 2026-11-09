"""Account-owned slots and per-browser selection, with no policy access to accounts."""
import re,unicodedata
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction,IntegrityError
from django.middleware.csrf import rotate_token
from django.shortcuts import redirect
from .models import PlayerProfile,World
from .worlds import current_world

class CharacterForm(forms.Form):
    name=forms.CharField(label='Imię postaci',min_length=2,max_length=32)
    world=forms.ModelChoiceField(label='Świat / serwer',queryset=World.objects.none(),empty_label=None)
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['world'].queryset=World.objects.filter(is_current=True,status='active',universe='GOTHIC_I')
        self.fields['world'].label_from_instance=lambda world: f'{world.name} · Kolonia (Gothic I)'
    def clean_name(self):
        value=unicodedata.normalize('NFKC',' '.join(self.cleaned_data['name'].split()))
        if not re.fullmatch(r"[\w][\w .'-]{1,31}",value):raise ValidationError('Użyj 2–32 liter, cyfr, spacji lub znaków _ . - i apostrofu.')
        return value

@transaction.atomic
def create_character(user,name,world_id):
    owner=User.objects.select_for_update().get(pk=user.pk)
    if not owner.is_active or owner.characters.filter(is_bot=True).exists():raise ValidationError('Konto nie może tworzyć postaci gracza.')
    form=CharacterForm({'name':name,'world':world_id})
    if not form.is_valid():raise ValidationError(' '.join(str(error) for errors in form.errors.values() for error in errors))
    world=form.cleaned_data['world'];name=form.cleaned_data['name']
    name_key=unicodedata.normalize('NFKC',name).casefold()
    if PlayerProfile.objects.filter(world=world,name_key=name_key).exists():raise ValidationError('To imię jest już zajęte na tym świecie.')
    draft=owner.characters.filter(is_draft=True).order_by('slot').first()
    if draft:
        draft.name=name;draft.world=world;draft.is_draft=False;draft.save(update_fields=['name','world','is_draft'])
        return draft
    used=set(owner.characters.values_list('slot',flat=True))
    slot=next((n for n in range(1,6) if n not in used),None)
    if slot is None:raise ValidationError('Na koncie możesz mieć najwyżej pięć postaci.')
    profile=PlayerProfile.objects.create(user=owner,world=world,slot=slot,name=name)
    from .economic_ledger import record_opening
    record_opening(profile)
    return profile


def select_character(request,profile):
    if profile.user_id!=request.user.pk or profile.is_draft or not profile.world.is_current or profile.world.status!='active':raise ValidationError('Ta postać nie jest dostępna na tym koncie i świecie.')
    request.session['active_character']=profile.pk
    request.user._server_profile=profile
    # Forms from another open character tab must not act on the newly selected one.
    rotate_token(request)

class CharacterSelectionMiddleware:
    def __init__(self,get_response):self.get_response=get_response
    def __call__(self,request):return self.get_response(request)
    def process_view(self,request,view,args,kwargs):
        if not request.user.is_authenticated:return None
        world=current_world()
        ready=request.user.characters.filter(world=world,is_draft=False).select_related('world')
        selected=ready.filter(pk=request.session.get('active_character')).first() or ready.order_by('slot').first()
        if selected:
            request.user._server_profile=selected
            if request.session.get('active_character')!=selected.pk:request.session['active_character']=selected.pk
        name=request.resolver_match.url_name if request.resolver_match else None
        if not selected and not request.path.startswith('/admin/') and name not in {'characters_page','register','login','logout','world_setup','health_live','health_ready','credits_page'}:
            return redirect('characters_page')
        return None
