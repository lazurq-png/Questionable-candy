from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as StockUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(StockUserAdmin):
    # The stock fieldsets list only the stock fields, so without this the
    # admin would silently offer no way to see or edit allergies.
    fieldsets = StockUserAdmin.fieldsets + (("Allergies", {"fields": ("allergies",)}),)
