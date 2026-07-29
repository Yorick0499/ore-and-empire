from django.contrib import admin
from .models import PlayerProfile
from .models import ItemBluePrint, OwnedItem


admin.site.register(PlayerProfile)
admin.site.register(ItemBluePrint)
admin.site.register(OwnedItem)
