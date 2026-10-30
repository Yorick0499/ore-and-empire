from django.contrib import admin
from .models import PlayerProfile
from .models import ItemBluePrint, OwnedItem


admin.site.register(PlayerProfile)
admin.site.register(ItemBluePrint)
admin.site.register(OwnedItem)


from .models import MarketTrade


@admin.register(MarketTrade)
class MarketTradeAdmin(admin.ModelAdmin):
    list_display = ("created_at", "blueprint", "seller", "buyer", "price")
    readonly_fields = ("created_at", "blueprint", "seller", "buyer", "price")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


from .models import BossAttempt


@admin.register(BossAttempt)
class BossAttemptAdmin(admin.ModelAdmin):
    list_display = ("created_at", "profile", "boss_key", "won", "ore_reward")
    readonly_fields = (
        "profile",
        "boss_key",
        "created_at",
        "won",
        "experience_reward",
        "ore_reward",
        "combat_log",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
