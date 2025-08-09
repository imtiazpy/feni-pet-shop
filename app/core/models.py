from django.db import models




class AbstractBaseModel(models.Model):
    """
    Abstract base model that provides common fields for all models.
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        abstract = True


class AbstractNameDescriptionModel(AbstractBaseModel):
    """
    Abstract model that includes name and description fields.
    """
    name = models.CharField(max_length=255, verbose_name="Name")
    description = models.TextField(blank=True, null=True, verbose_name="Description")

    class Meta:
        abstract = True

    def __str__(self):
        return self.name
    
class AbstractStatusModel(models.Model):
    """
    Abstract model that includes status field.
    """
    class StatusChoices(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        ARCHIVED = 'archived', 'Archived'
    
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default='active', verbose_name="Status")

    class Meta:
        abstract = True


class AbstractAddressModel(models.Model):
    """
    Abstract model that includes address fields.
    """
    address_line1 = models.CharField(max_length=255, verbose_name="Address Line 1")
    address_line2 = models.CharField(max_length=255, blank=True, null=True, verbose_name="Address Line 2")
    city = models.CharField(max_length=100, verbose_name="City")
    state = models.CharField(max_length=100, verbose_name="State")
    postal_code = models.CharField(max_length=20, verbose_name="Postal Code")
    country = models.CharField(max_length=100, verbose_name="Country")

    class Meta:
        abstract = True