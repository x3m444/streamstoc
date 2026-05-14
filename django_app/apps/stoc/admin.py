from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import StocUser


@admin.register(StocUser)
class StocUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_readonly', 'is_staff', 'is_active')
    list_filter = ('is_readonly', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Permisiuni stoc', {'fields': ('is_readonly',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Permisiuni stoc', {'fields': ('is_readonly',)}),
    )
