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
    start_region=forms.ModelChoiceField(label='Region startowy',queryset=World.objects.none(),required=False,empty_label=None,widget=forms.HiddenInput)
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        from .barrier import creation_worlds
        self.fields['world'].queryset=creation_worlds().order_by('edition','pk')
        self.fields['world'].label_from_instance=lambda world: ('Połączony świat — Kolonia i Khorinis' if world.union_key else f'{world.name} · '+('Khorinis (Gothic II)' if world.universe=='GOTHIC_II' else 'Kolonia (Gothic I)'))
        raw=self.data.get('world') if self.is_bound else self.initial.get('world')
        chosen=self.fields['world'].queryset.filter(pk=int(raw)).first() if raw and str(raw).isdigit() and len(str(raw))<19 else self.fields['world'].queryset.first()
        if chosen and chosen.union_key:
            from .barrier import region_ids
            self.fields['start_region'].widget=forms.Select()
            self.fields['start_region'].queryset=World.objects.filter(pk__in=region_ids(chosen),status='active')
            self.fields['start_region'].initial=chosen.pk
            self.fields['start_region'].label_from_instance=lambda region: 'Khorinis' if region.universe=='GOTHIC_II' else 'Górnicza Dolina (Kolonia)'

    def clean_name(self):
        value=unicodedata.normalize('NFKC',' '.join(self.cleaned_data['name'].split()))
        if not re.fullmatch(r"[\w][\w .'-]{1,31}",value):raise ValidationError('Użyj 2–32 liter, cyfr, spacji lub znaków _ . - i apostrofu.')
        return value

@transaction.atomic
def create_character(user,name,world_id,*,start_region=None):
    owner=User.objects.select_for_update().get(pk=user.pk)
    if not owner.is_active or owner.characters.filter(is_bot=True).exists():raise ValidationError('Konto nie może tworzyć postaci gracza.')
    form=CharacterForm({'name':name,'world':world_id,'start_region':start_region})
    if not form.is_valid():raise ValidationError(' '.join(str(error) for errors in form.errors.values() for error in errors))
    world=form.cleaned_data['world'];name=form.cleaned_data['name']
    if world.union_key:
        from .models import SleeperRace
        # All starting regions share a name reservation after the global event.
        # Lock its joined record; activation never writes it again.
        SleeperRace.objects.select_for_update().filter(colony=world,state='joined').first()
    name_key=unicodedata.normalize('NFKC',name).casefold()
    from .barrier import region_ids
    worlds=region_ids(world)
    world=form.cleaned_data.get('start_region') or world
    legacy_names=PlayerProfile.objects.filter(world_id__in=worlds,name='',is_bot=False,is_draft=False).values_list('user__username',flat=True)
    reserved=any(unicodedata.normalize('NFKC',legacy).casefold()==name_key for legacy in legacy_names)
    if reserved or PlayerProfile.objects.filter(world_id__in=worlds,name_key=name_key).exists():raise ValidationError('To imię jest już zajęte na tym świecie.')
    draft=owner.characters.filter(is_draft=True).order_by('slot').first()
    if draft:
        draft.name=name;draft.world=world;draft.origin_world=world;draft.is_draft=False;draft.save(update_fields=['name','world','origin_world','is_draft'])
        return draft
    used=set(owner.characters.values_list('slot',flat=True))
    slot=next((n for n in range(1,6) if n not in used),None)
    if slot is None:raise ValidationError('Na koncie możesz mieć najwyżej pięć postaci.')
    profile=PlayerProfile.objects.create(user=owner,world=world,slot=slot,name=name)
    from .economic_ledger import record_opening
    record_opening(profile)
    return profile


def select_character(request,profile):
    from .realms import is_open
    if profile.user_id!=request.user.pk or profile.is_draft or not is_open(profile.world):raise ValidationError('Ta postać nie jest dostępna na tym koncie i świecie.')
    request.session['active_character']=profile.pk
    request.user._server_profile=profile
    # Forms from another open character tab must not act on the newly selected one.
    rotate_token(request)

class CharacterSelectionMiddleware:
    def __init__(self,get_response):self.get_response=get_response
    def __call__(self,request):
        from .realms import world_scope
        from .models import SleeperRace
        from django.utils import timezone
        from django.http import HttpResponse
        operator_read=request.path=='/zarzadca/bariera/' and request.method=='GET' and request.user.is_authenticated and request.user.is_active and request.user.is_superuser
        if not operator_read and not request.path.startswith('/health/') and SleeperRace.objects.filter(state='merging',lease_expires_at__gt=timezone.now()).exists():
            response=HttpResponse('Trwa zabezpieczanie zapisu i upadek Bariery. Spróbuj ponownie za chwilę.',status=503)
            response['Retry-After']='5';return response
        # Bind before view dispatch and template context processing; reset on every response/exception.
        with world_scope(None):
            if request.path.startswith('/health/'):return self.get_response(request)
            if request.user.is_authenticated:
                from .realms import open_worlds
                ready=request.user.characters.filter(world__in=open_worlds(),is_draft=False).select_related('world')
                selected=ready.filter(pk=request.session.get('active_character')).first() or ready.order_by('slot').first()
                if selected:
                    request.user._server_profile=selected
                    from .realms import _scope
                    _scope.set(selected.world_id)
            if request.user.is_authenticated and request.user.is_superuser and request.path.startswith('/zarzadca/'):
                from .realms import open_worlds,_scope
                server=request.GET.get('server')
                if server is not None:
                    from django.http import Http404
                    if not server or len(server)>18 or not server.isdecimal():raise Http404('Nieznany serwer.')
                    selected_world=open_worlds().filter(pk=int(server)).first()
                    if selected_world is None:raise Http404('Serwer jest zamknięty lub nie istnieje.')
                    _scope.set(selected_world.pk)
            return self.get_response(request)
    def process_view(self,request,view,args,kwargs):
        if request.path.startswith('/health/') or request.path=='/zarzadca/bariera/' or not request.user.is_authenticated:return None
        world=current_world()
        from .realms import open_worlds
        ready=request.user.characters.filter(world__in=open_worlds(),is_draft=False).select_related('world')
        selected=ready.filter(pk=request.session.get('active_character')).first() or ready.order_by('slot').first()
        if selected:
            request.user._server_profile=selected
            if request.session.get('active_character')!=selected.pk:request.session['active_character']=selected.pk
        name=request.resolver_match.url_name if request.resolver_match else None
        if not selected and not request.path.startswith('/admin/') and name not in {'barrier_admin','characters_page','register','login','logout','world_setup','health_live','health_ready','credits_page'}:
            return redirect('characters_page')
        return None
