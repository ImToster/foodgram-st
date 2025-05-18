from django.urls import path
from .views import short_link_to_recipe

app_name = "food"

urlpatterns = [
    path(
        "s/<int:recipe_id>/", short_link_to_recipe, name="short-link-to-recipe"
    ),
]
