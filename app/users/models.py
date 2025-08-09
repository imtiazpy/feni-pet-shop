from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext as _



class User(AbstractUser):
    """
    Custom user model that extends the default Django user model.
    """
    class Roles(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        CASHIER = 'cashier', 'Cashier'
        INVENTORY_MANAGER = 'inventory_manager', 'Inventory Manager'
        VETERINARIAN = 'veterinarian', 'Veterinarian'

    role = models.CharField(
        _('Role'),
        max_length=20,
        choices=Roles.choices,
        default=Roles.ADMIN,
        help_text='Role of the user in the system'
    )
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    phone_number = models.CharField(_('Phone Number'), max_length=255, null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_admin(self):
        return self.role == self.Roles.ADMIN
    
    @property
    def is_cashier(self):
        return self.role == self.Roles.CASHIER
    
    @property
    def is_inventory_manager(self):
        return self.role == self.Roles.INVENTORY_MANAGER
    
    @property
    def is_veterinarian(self):
        return self.role == self.Roles.VETERINARIAN

    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
   
    def __str__(self):
        return self.username