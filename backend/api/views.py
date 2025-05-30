import io

from django.conf import settings
from django.db import models
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics, ttfonts
from reportlab.pdfgen import canvas
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from food.models import FavoriteRecipe, Ingredient, Purchase, Recipe
from users.models import Subscription, User

from .filters import IngredientFilter, RecipeFilter
from .pagination import CustomPagination
from .permissions import AuthorOrReadOnly
from .serializers import (IngredientSerializer, RecipeSerializer,
                          RecipeShortSerializer, UserAvatarSerializer,
                          UserWithRecipesSerializer)

font_object = ttfonts.TTFont("Arial", settings.BASE_DIR / "fonts/arialmt.ttf")
pdfmetrics.registerFont(font_object)


def create_or_delete_object(
    viewset_object,
    request,
    model_class,
    return_object,
    already_exists_message=None,
    non_exists_message=None,
    **field_values,
):
    if request.method == "POST":
        _, created = model_class.objects.get_or_create(**field_values)

        if not created:
            raise ValidationError(already_exists_message)

        return Response(
            viewset_object.get_serializer(return_object).data,
            status=status.HTTP_201_CREATED,
        )

    try:
        model_class.objects.get(**field_values).delete()
    except model_class.DoesNotExist:
        raise ValidationError(non_exists_message)
    return Response(status=status.HTTP_204_NO_CONTENT)


class CustomUserViewSet(UserViewSet):
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action == "me":
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    @action(
        methods=["put", "delete"],
        detail=False,
        url_path="me/avatar",
        permission_classes=(IsAuthenticated,),
        serializer_class=UserAvatarSerializer,
    )
    def avatar(self, request):
        current_user = request.user
        if request.method == "PUT":
            serializer = self.get_serializer(current_user, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        current_user.avatar = None
        current_user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=["get"],
        detail=False,
        permission_classes=(IsAuthenticated,),
        serializer_class=UserWithRecipesSerializer,
    )
    def subscriptions(self, request):
        subscriptions = request.user.subscriptions.all()
        paginated_subscriptions = self.paginate_queryset(subscriptions)
        serializer = self.get_serializer(paginated_subscriptions, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        methods=["post", "delete"],
        detail=True,
        permission_classes=(IsAuthenticated,),
        serializer_class=UserWithRecipesSerializer,
    )
    def subscribe(self, request, id=None):
        author = get_object_or_404(User, pk=id)
        current_user = request.user
        if current_user == author:
            raise ValidationError("Cannot subscribe to yourself.")
        return create_or_delete_object(
            self,
            request,
            Subscription,
            author,
            "You are already subscribed to this user.",
            "You are not subscribed to this user.",
            author=author,
            subscriber=current_user,
        )


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (AuthorOrReadOnly,)
    serializer_class = RecipeSerializer
    pagination_class = CustomPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _create_or_delete_relation(
        self, request, recipe_id, model_class, already_exists_message
    ):
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        current_user = request.user

        if request.method == "POST":
            _, created = model_class.objects.get_or_create(
                user=current_user, recipe=recipe
            )

            if not created:
                raise ValidationError(already_exists_message)

            return Response(
                self.get_serializer(
                    recipe).data, status=status.HTTP_201_CREATED
            )

        get_object_or_404(model_class, user=current_user,
                          recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
        serializer_class=RecipeShortSerializer,
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        current_user = request.user
        return create_or_delete_object(
            self,
            request,
            FavoriteRecipe,
            recipe,
            "Recipe already is favorited.",
            "Recipe is not favorited.",
            user=current_user,
            recipe=recipe,
        )

    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[IsAuthenticated],
        serializer_class=RecipeShortSerializer,
    )
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        current_user = request.user
        return create_or_delete_object(
            self,
            request,
            Purchase,
            recipe,
            "Recipe already in shopping cart.",
            "Recipe is not in shopping cart.",
            user=current_user,
            recipe=recipe,
        )

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_link_to_recipe(self, request, pk=None):
        if not Recipe.objects.filter(pk=pk).exists():
            raise Http404

        return Response(
            {
                "short-link": request.build_absolute_uri(
                    reverse("food:short-link-to-recipe", args=[pk])
                )
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, permission_classes=[IsAuthenticated], methods=["get"])
    def download_shopping_cart(self, request):
        recipes = request.user.purchased_recipes
        if not recipes.exists():
            raise ValidationError("Shopping list empty")

        ingredients = recipes.values(
            "ingredients__name", "ingredients__measurement_unit"
        ).annotate(total_amount=models.Sum("ingredient_recipes__amount"))

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, bottomup=0, pagesize=A4)
        height = A4[1]
        p.setFont("Arial", 14)
        y = 50
        p.drawString(50, y, "Список ингредиентов:")
        y += 20
        for i, ingredient in enumerate(ingredients, 1):
            p.drawString(
                70,
                y,
                f"{i}. {ingredient['ingredients__name']}"
                f" ({ingredient['ingredients__measurement_unit']})"
                f" - {ingredient['total_amount']}",
            )
            y += 20
            if y > height - 50:
                p.showPage()
                p.setFont("Arial", 14)
                y = 50

        p.showPage()
        p.save()

        buffer.seek(0)
        return FileResponse(
            buffer,
            as_attachment=True,
            filename="shopping_cart.pdf",
        )


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
