from django_filters.rest_framework import FilterSet, filters
from food.models import Recipe, Ingredient


class IngredientFilter(FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="istartswith")

    class Meta:
        model = Ingredient
        fields = ("name", )


class RecipeFilter(FilterSet):
    author = filters.NumberFilter(field_name="author")
    is_favorited = filters.BooleanFilter(method="filter_is_favorited")
    is_in_shopping_cart = filters.BooleanFilter(
        method="filter_is_in_shopping_cart"
    )

    class Meta:
        model = Recipe
        fields = ("author", "is_favorited", "is_in_shopping_cart")

    def filter_is_favorited(self, queryset, name, value):
        current_user = self.request.user
        if current_user.is_authenticated and value:
            return queryset.filter(lovers=current_user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        current_user = self.request.user
        if current_user.is_authenticated and value:
            return queryset.filter(shoppers=current_user)
        return queryset
