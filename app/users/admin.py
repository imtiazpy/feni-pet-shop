from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .forms import CustomUserCreationForm, CustomUserChangeForm

User = get_user_model()

class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User

    list_display = ('username', 'email', 'role', 'is_active', 'is_superuser')
    list_filter = ('role', 'is_active', 'is_superuser')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'avatar')}),
        ('Role & Permissions', {'fields': ('role', 'is_active', 'is_staff')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'phone_number', 'avatar', 'is_active')}
        ),
    )
    search_fields = ('username', 'email')
    ordering = ('username',)


admin.site.register(User, CustomUserAdmin)