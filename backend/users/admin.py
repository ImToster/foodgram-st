from django.contrib import admin
from .models import User, Subscription
from django.contrib.auth.admin import UserAdmin


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    search_fields = (
        "email",
        "username",
        "first_name",
        "last_name"
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "subscriber",
        "author",
    )
