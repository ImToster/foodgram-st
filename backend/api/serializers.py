from django.db import transaction
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

import const
from food.models import Ingredient, IngredientRecipe, Recipe
from users.models import User


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = (
            "email", "id", "username", "first_name", "last_name", "password"
        )


class CustomUserSerializer(UserSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        return request.user.is_authenticated and (
            request.user.subscriptions.filter(id=obj.id).exists()
        )


class UserWithRecipesSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField(read_only=True)
    recipes_count = serializers.IntegerField(
        source="recipes.count", read_only=True
    )

    class Meta(CustomUserSerializer.Meta):
        fields = (
            *CustomUserSerializer.Meta.fields,
            "recipes",
            "recipes_count",
        )

    def get_recipes(self, obj):
        recipes_limit = int(
            self.context.get("request").GET.get(
                const.RECIPES_LIMIT_QUERY_PARAM, const.RECIPES_LIMIT_DEFAULT
            )
        )
        return RecipeShortSerializer(
            obj.recipes.all()[:recipes_limit], many=True
        ).data


class UserAvatarSerializer(CustomUserSerializer):
    avatar = Base64ImageField(required=True, allow_null=True)

    class Meta:
        model = User
        fields = ("avatar",)


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source="ingredient",
    )
    name = serializers.CharField(source="ingredient.name", read_only=True)
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit", read_only=True
    )

    class Meta:
        model = IngredientRecipe
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeShortSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "image",
            "name",
            "cooking_time",
        )
        read_only_fields = fields


class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField()
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientRecipeSerializer(
        many=True, source="ingredient_recipes", allow_empty=False
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )
        read_only_fields = ("author", "is_favorited", "is_in_shopping_cart")

    def validate_image(self, value):
        if not value:
            raise ValidationError(
                {"image": "Поле 'image' не может быть пустым."}
            )
        return value

    def validate_ingredients(self, ingredient_recipes_data):
        ingredient_ids = [
            item["ingredient"] for item in ingredient_recipes_data
        ]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {"ingredients": "Cannot contain duplicates."}
            )

        return ingredient_recipes_data

    def validate(self, data):
        if self.instance:
            if "ingredient_recipes" not in data:
                raise serializers.ValidationError(
                    {"ingredients": "This field is required."}
                )
            for field_name in ["name", "text", "cooking_time"]:
                if field_name not in data:
                    raise serializers.ValidationError(
                        {field_name: "This field is required."}
                    )
        return data

    def _get_exists_relation_with_user(self, recipe, related_name):
        request = self.context.get("request")
        return request.user.is_authenticated and (
            getattr(request.user, related_name).filter(id=recipe.id).exists()
        )

    def get_is_favorited(self, obj):
        return self._get_exists_relation_with_user(obj, "favorite_recipes")

    def get_is_in_shopping_cart(self, obj):
        return self._get_exists_relation_with_user(obj, "purchased_recipes")

    def _create_ingredient_recipes(self, recipe, ingredient_recipes_data):
        IngredientRecipe.objects.bulk_create(
            [
                IngredientRecipe(recipe=recipe, **ingredient_recipe_data)
                for ingredient_recipe_data in ingredient_recipes_data
            ]
        )

    @transaction.atomic
    def create(self, validated_data):
        ingredient_recipes_data = validated_data.pop("ingredient_recipes")
        recipe = Recipe.objects.create(**validated_data)
        self._create_ingredient_recipes(recipe, ingredient_recipes_data)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredient_recipes_data = validated_data.pop("ingredient_recipes")
        instance.ingredient_recipes.all().delete()
        self._create_ingredient_recipes(instance, ingredient_recipes_data)
        return super().update(instance, validated_data)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = "__all__"
