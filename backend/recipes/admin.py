from django.contrib import admin

from recipes.models import (Ingredient, IngredientSpecification, Recipe, Tag,
                            TagRecipe, UserFavoritedRecipe, UserShoppingCart)


class IngredientInline(admin.TabularInline):
    model = Ingredient
    min_num = 1


class TagRecipeInline(admin.TabularInline):
    model = TagRecipe
    min_num = 1


class RecipeAdmin(admin.ModelAdmin):
    inlines = [IngredientInline, TagRecipeInline]
    search_fields = ['author__username', 'name', 'tags__name']
    list_display = ['name', 'author', 'favorites_counter', 'ingredients_names']
    readonly_fields = ['favorites_counter']


class IngredientAdmin(admin.ModelAdmin):
    list_display = ['specification', 'recipe', 'amount']
    search_fields = ['specification__name']


class IngredientSpecificationAdmin(admin.ModelAdmin):
    list_display = ['name', 'measurement_unit']
    search_fields = ['name']


admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Tag)
admin.site.register(TagRecipe)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(IngredientSpecification, IngredientSpecificationAdmin)
admin.site.register(UserFavoritedRecipe)
admin.site.register(UserShoppingCart)
