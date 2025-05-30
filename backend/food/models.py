from django.core.validators import MinValueValidator
from django.db import models

import const
from users.models import User


class Ingredient(models.Model):
    name = models.CharField(
        max_length=const.MAX_LENGTH_INGREDIENT_NAME,
        unique=True,
        db_index=True,
        verbose_name="Название",
    )
    measurement_unit = models.CharField(
        max_length=const.MAX_LENGTH_MEASUREMENT_UNIT,
        verbose_name="Единица измерения"
    )

    class Meta:
        verbose_name = "ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор"
    )
    ingredients = models.ManyToManyField(
        Ingredient, through="IngredientRecipe", verbose_name="Ингредиенты"
    )
    name = models.CharField(
        max_length=const.MAX_LENGTH_RECIPE_NAME, verbose_name="Название"
    )
    image = models.ImageField(upload_to="recipes/", verbose_name="Картинка")
    text = models.TextField(verbose_name="Текстовое описание")
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Время приготовления в минутах"
    )
    lovers = models.ManyToManyField(
        User,
        related_name="favorite_recipes",
        through="FavoriteRecipe",
        verbose_name="Добавившие в изобранное",
    )
    shoppers = models.ManyToManyField(
        User,
        related_name="purchased_recipes",
        through="Purchase",
        verbose_name="Добавившие в корзину",
    )

    class Meta:
        ordering = ("-id",)
        verbose_name = "рецепт"
        verbose_name_plural = "Рецепты"

    def __str__(self):
        return self.name


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, verbose_name="Ингредиент"
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="ingredient_recipes",
        verbose_name="Рецепт",
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Количество ингредиента в рецепте",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("ingredient", "recipe"),
                name="unique_ingredient_recipe"
            )
        ]
        verbose_name = "ингредиент в рецепте"
        verbose_name_plural = "Ингридиенты в рецептах"

    def __str__(self):
        return f"{self.ingredient} - {self.recipe}"


class UserRecipe(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Пользователь"
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт"
    )

    class Meta:
        abstract = True
        constraints = [models.UniqueConstraint(
            fields=("user", "recipe"),
            name="unique_%(class)s"
        )]
        verbose_name = "рецепт пользователя"
        verbose_name_plural = "Рецепты пользователей"

    def __str__(self):
        return f"{self.user} - {self.recipe}"


class FavoriteRecipe(UserRecipe):
    class Meta(UserRecipe.Meta):
        verbose_name = "избранный рецепт"
        verbose_name_plural = "Избранные рецепты"


class Purchase(UserRecipe):
    class Meta(UserRecipe.Meta):
        verbose_name = "рецепт в корзине"
        verbose_name_plural = "Рецепты в корзине"
