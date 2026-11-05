from django import forms
from django.contrib import admin
from django.utils import timezone
from .models import (PlayerProfile, ItemBluePrint, OwnedItem, MarketTrade, BossAttempt,
                     BotDecision, CampQuest, AdventureTemplate, AdventureRun,
                     WorldEvent, StoreProduct, StorePurchase, PremiumEntry, AdminAction)
from .admin_tools import ProfileStatsForm

admin.site.site_header = "Ore & Empire — Zarządca Kolonii"
admin.site.site_title = "Zarządca Kolonii"
admin.site.index_title = "Postacie, ekonomia i wydarzenia"


class ProfileAdminForm(ProfileStatsForm):
    class Meta(ProfileStatsForm.Meta):
        fields = "__all__"


@admin.register(PlayerProfile)
class ProfileAdmin(admin.ModelAdmin):
    form = ProfileAdminForm
    list_display = ("user", "is_bot", "camp", "guild", "level", "current_health", "current_energy", "ore_balance", "premium_balance")
    list_filter = ("is_bot", "camp", "bot_role")
    search_fields = ("user__username",)
    readonly_fields = ("premium_balance", "energy_updated_at", "health_updated_at", "bot_turn")

    def save_model(self, request, obj, form, change):
        if "current_energy" in form.changed_data:
            obj.energy_updated_at = timezone.now()
        if "current_health" in form.changed_data:
            obj.health_updated_at = timezone.now()
        super().save_model(request, obj, form, change)
        AdminAction.objects.create(actor=request.user, profile=obj, action="django_stats", details={"fields": form.changed_data})


@admin.register(ItemBluePrint)
class BlueprintAdmin(admin.ModelAdmin):
    list_display = ("name", "damage", "required_strength", "base_value")
    search_fields = ("name",)


@admin.register(OwnedItem)
class OwnedItemAdmin(admin.ModelAdmin):
    list_display = ("owner", "blueprint", "is_equipped", "is_market_listed", "market_price")
    list_filter = ("is_equipped", "is_market_listed")
    search_fields = ("owner__user__username", "blueprint__name")
    autocomplete_fields = ("blueprint", "owner")


class ReadOnlyAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        return [field.name for field in self.model._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MarketTrade)
class MarketTradeAdmin(ReadOnlyAdmin):
    list_display = ("created_at", "blueprint", "seller", "buyer", "price")


@admin.register(BossAttempt)
class BossAttemptAdmin(ReadOnlyAdmin):
    list_display = ("created_at", "profile", "boss_key", "won", "ore_reward")


@admin.register(PremiumEntry)
class PremiumAdmin(ReadOnlyAdmin):
    list_display = ("created_at", "profile", "amount", "balance_after", "reason")
    search_fields = ("profile__user__username",)


@admin.register(AdminAction)
class AdminActionAdmin(ReadOnlyAdmin):
    list_display = ("created_at", "actor", "profile", "action")


@admin.register(StorePurchase)
class PurchaseAdmin(ReadOnlyAdmin):
    list_display = ("created_at", "profile", "product", "price", "effect")


@admin.register(AdventureRun)
class AdventureRunAdmin(ReadOnlyAdmin):
    list_display = ("profile", "template", "ends_at", "claimed_at", "premium_reward")


@admin.register(BotDecision)
class BotDecisionAdmin(ReadOnlyAdmin):
    list_display = ("created_at", "profile", "role", "action", "success")
    list_filter = ("role", "action", "success")


@admin.register(CampQuest)
class CampQuestAdmin(ReadOnlyAdmin):
    list_display = ("profile", "rank_key", "accepted_at", "promoted_at")


class BoundedRewardsForm(forms.ModelForm):
    def clean(self):
        data = super().clean()
        for field, value in data.items():
            if type(value) is int and not 0 <= value <= 1_000_000:
                self.add_error(field, "Wartość poza zakresem 0–1000000.")
        return data


class AdventureForm(BoundedRewardsForm):
    class Meta:
        model = AdventureTemplate
        fields = "__all__"

    def clean(self):
        data = super().clean()
        if not 1 <= data.get("duration_seconds", 0) <= 86400:
            self.add_error("duration_seconds", "Czas wyprawy: 1–86400 sekund.")
        return data


@admin.register(AdventureTemplate)
class AdventureAdmin(admin.ModelAdmin):
    form = AdventureForm
    list_display = ("name", "level", "duration_seconds", "energy_cost", "premium_reward", "enabled")
    list_filter = ("enabled",)


class EventForm(BoundedRewardsForm):
    class Meta:
        model = WorldEvent
        fields = "__all__"

    def clean(self):
        data = super().clean()
        for field in ("ore_percent", "experience_percent"):
            if not 100 <= data.get(field, 100) <= 500:
                self.add_error(field, "Premia: 100–500 procent.")
        return data


@admin.register(WorldEvent)
class WorldEventAdmin(admin.ModelAdmin):
    form = EventForm
    list_display = ("name", "kind", "starts_at", "ends_at", "enabled", "ore_percent", "experience_percent", "premium_bonus")
    list_filter = ("kind", "enabled")
    actions = ("disable_events",)

    @admin.action(description="Wyłącz wybrane wydarzenia")
    def disable_events(self, request, queryset):
        queryset.update(enabled=False)


class ProductForm(BoundedRewardsForm):
    class Meta:
        model = StoreProduct
        fields = "__all__"

    def clean(self):
        data = super().clean()
        if data.get("kind") == "weapon" and not data.get("blueprint"):
            self.add_error("blueprint", "Oręż wymaga wzorca przedmiotu.")
        if data.get("kind") in ("energy", "health") and data.get("effect", 0) < 1:
            self.add_error("effect", "Napój musi odnawiać dodatnią liczbę punktów.")
        return data


@admin.register(StoreProduct)
class StoreProductAdmin(admin.ModelAdmin):
    form = ProductForm
    list_display = ("name", "kind", "price", "level", "enabled")
    list_filter = ("kind", "enabled")


from .models import TavernTopic, TavernMessage


@admin.register(TavernTopic)
class TavernTopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'updated_at', 'locked')
    list_filter = ('locked',)
    readonly_fields = ('author', 'title', 'created_at', 'updated_at')

    def has_add_permission(self, request):
        return False


@admin.register(TavernMessage)
class TavernMessageAdmin(ReadOnlyAdmin):
    list_display = ('created_at', 'author', 'topic')

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


from .models import StoryQuest, StoryRun


@admin.register(StoryQuest)
class StoryQuestAdmin(admin.ModelAdmin):
    list_display = ('key', 'title', 'version', 'chapter', 'level', 'camp', 'enabled')
    list_filter = ('chapter', 'camp', 'enabled', 'universe')
    search_fields = ('key', 'title')

    def get_readonly_fields(self, request, obj=None):
        return ('key',) if obj else ()


@admin.register(StoryRun)
class StoryRunAdmin(ReadOnlyAdmin):
    list_display = ('profile', 'quest', 'status', 'accepted_at', 'claimed_at')
    list_filter = ('status',)


from .models import BattleRecord, LootTable


@admin.register(BattleRecord)
class BattleRecordAdmin(ReadOnlyAdmin):
    list_display = ('created_at','profile','monster_key','won','loot_version')


@admin.register(LootTable)
class LootTableAdmin(admin.ModelAdmin):
    list_display = ('key','version','enabled')


from .models import ContentPack
admin.site.register(ContentPack, ReadOnlyAdmin)
