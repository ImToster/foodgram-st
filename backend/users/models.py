from django.contrib.auth.models import AbstractUser
from django.db import models

import const


class User(AbstractUser):
    email = models.EmailField(
        unique=True,
        max_length=const.MAX_LENGTH_EMAIL,
        verbose_name="Адрес электронной почты",
    )
    first_name = models.CharField(
        max_length=const.MAX_LENGTH_FIRSTNAME,
        verbose_name="Имя",
    )
    last_name = models.CharField(
        max_length=const.MAX_LENGTH_LASTNAME,
        verbose_name="Фамилия",
    )
    avatar = models.ImageField(
        upload_to="avatars", verbose_name="Аватар", null=True, default=None
    )
    subscriptions = models.ManyToManyField(
        "self", through="Subscription", verbose_name="Подписки"
    )
    REQUIRED_FIELDS = ["first_name", "last_name", "username"]
    USERNAME_FIELD = "email"

    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Подписчик"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="subscribers",
        verbose_name="Автор"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("author", "subscriber"),
                name="unique_author_subscriber"
            )
        ]
        verbose_name = "подписка"
        verbose_name_plural = "Подписки"

    def __str__(self):
        return f"Подписка {self.subscriber} на {self.author}"
