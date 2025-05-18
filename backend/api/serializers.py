from djoser.serializers import UserCreateSerializer, UserSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers
import base64
from django.core.files.base import ContentFile
from food.models import Recipe, Ingredient, IngredientRecipe


User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'password')


class CustomUserSerializer(UserSerializer):
    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request.user.is_authenticated:
            return request.user.subscriptions.filter(id=obj.id).exists()
        return False


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
        recipes_limit = int(self.context.get("request").GET.get(
            "recipes_limit", 100
        ))
        return RecipeShortSerializer(
            obj.recipes.all()[:recipes_limit],
            many=True
        ).data


class UserAvatarSerializer(CustomUserSerializer):
    avatar = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = User
        fields = ('avatar', )


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source="ingredient",
    )
    name = serializers.CharField(source="ingredient.name", read_only=True)
    measurement_unit = serializers.CharField(
        source="ingredient.measurement_unit",
        read_only=True
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeShortSerializer(serializers.ModelSerializer):
    image = Base64ImageField(allow_null=False)

    class Meta:
        model = Recipe
        fields = (
            'id', 'image', 'name', 'cooking_time',
        )
        read_only_fields = fields


class RecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(allow_null=False)
    author = CustomUserSerializer(read_only=True)
    ingredients = IngredientRecipeSerializer(
        many=True,
        source='ingredient_recipes',
        allow_empty=False
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text',
            'cooking_time'
        )
        read_only_fields = (
            'author', 'is_favorited', 'is_in_shopping_cart'
        )

    def validate_ingredients(self, ingredient_recipes_data):
        ingredient_ids = [
            item["ingredient"]
            for item in ingredient_recipes_data
        ]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {"ingredients": "Cannot contain duplicates."}
            )

        return ingredient_recipes_data

    def validate(self, data):
        if self.instance:
            if 'ingredient_recipes' not in data:
                raise serializers.ValidationError(
                    {"ingredients": "This field is required."}
                )
            for field_name in [
                'name',
                'text',
                'cooking_time'
            ]:
                if field_name not in data:
                    raise serializers.ValidationError(
                        {field_name: "This field is required."}
                    )
        return data

    def _get_exists_relation_with_user(self, recipe, related_name):
        request = self.context.get('request')
        if request.user.is_authenticated:
            return getattr(request.user, related_name).filter(id=recipe.id).exists()
        return False

    def get_is_favorited(self, obj):
        return self._get_exists_relation_with_user(obj, 'favorite_recipes')

    def get_is_in_shopping_cart(self, obj):
        return self._get_exists_relation_with_user(obj, 'purchased_recipes')

    def _create_ingredient_recipes(self, recipe, ingredient_recipes_data):
        IngredientRecipe.objects.bulk_create(
            [
                IngredientRecipe(
                    recipe=recipe,
                    **ingredient_recipe_data
                )
                for ingredient_recipe_data in ingredient_recipes_data
            ]
        )

    def create(self, validated_data):
        ingredient_recipes_data = validated_data.pop('ingredient_recipes')
        recipe = Recipe.objects.create(**validated_data)
        self._create_ingredient_recipes(recipe, ingredient_recipes_data)
        return recipe

    def update(self, instance, validated_data):
        ingredient_recipes_data = validated_data.pop('ingredient_recipes')
        instance.ingredient_recipes.all().delete()
        self._create_ingredient_recipes(instance, ingredient_recipes_data)
        return super().update(instance, validated_data)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'
