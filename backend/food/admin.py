from django.contrib import admin

from .models import (
    Ingredient,
    Recipe,
    IngredientRecipe,
    FavoriteRecipe,
    Purchase,
)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "author",
    )
    search_fields = (
        "author__username",
        "author__first_name",
        "author__last_name",
        "name"
    )
    readonly_fields = ('lovers_count', )

    @admin.display(description="Добавления в изобранное")
    def lovers_count(self, obj):
        return obj.lovers.count()


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "measurement_unit",
    )
    search_fields = ("name",)


@admin.register(IngredientRecipe)
class IngredientRecipeAdmin(admin.ModelAdmin):
    list_display = (
        "ingredient",
        "recipe",
        "amount"
    )


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "recipe",
    )


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "recipe",
    )
