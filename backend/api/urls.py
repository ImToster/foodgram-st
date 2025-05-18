from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import CustomUserViewSet, RecipeViewSet, IngredientViewSet

app_name = 'api'
router = DefaultRouter()
router.register('users', CustomUserViewSet, basename='users')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
