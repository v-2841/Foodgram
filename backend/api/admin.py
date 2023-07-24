from django.contrib import admin

from .models import (
    Tag, Ingredient, IngredientSpecification, Recipe, TagRecipe,
    UserFavoritedRecipe, UserShoppingCart,
)


class IngredientInline(admin.TabularInline):
    model = Ingredient


class TagRecipeInline(admin.TabularInline):
    model = TagRecipe


class RecipeAdmin(admin.ModelAdmin):
    inlines = [IngredientInline, TagRecipeInline]


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag)
admin.site.register(TagRecipe)
admin.site.register(Ingredient)
admin.site.register(IngredientSpecification)
admin.site.register(UserFavoritedRecipe)
admin.site.register(UserShoppingCart)
