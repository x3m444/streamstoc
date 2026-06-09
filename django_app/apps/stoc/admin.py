from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import StocUser, UserPreferences


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


@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = ('user', 'default_nava', 'default_tragator', 'default_data')
    list_filter = ('default_nava',)
    search_fields = ('user__username',)
    readonly_fields = ('default_data',)
    fieldsets = (
        ('Utilizator', {'fields': ('user',)}),
        ('Preferințe', {'fields': ('default_nava', 'default_tragator')}),
        ('Info', {'fields': ('default_data',), 'classes': ('collapse',)}),
    )
