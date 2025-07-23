from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# Create your models here.
from django.db import models
import json
import re
from django.core.exceptions import ValidationError



""" validate contact number """
def validate_phone(value):
    pattern = re.compile(r'^\+?[\d\s\-]{9,20}$')  # Allows +233, 024, etc.
    if not pattern.match(value):
        raise ValidationError("Invalid phone number format.")


class User(AbstractUser):
    # Add custom fields here if any
    pass

class Feature(models.Model):
    """ represent individual features, ex. email support, advance reports, etc """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    def __str__(self):
        return self.name



class SubscriptionPlan(models.Model):
    
    """  Each plan has a name and is linked to multiple features.  """
    
    PLAN_CHOICES = [
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise'),
    ]
    
    name = models.CharField(max_length=20, choices=PLAN_CHOICES, unique=True)
    features = models.ManyToManyField(Feature, related_name='subscription_plans')

    def __str__(self):
        return self.get_name_display()

    def get_feature_list(self):
        return [f.name for f in self.features.all()]




class Vendor(models.Model):
    """ clients are linked to subscription plan with get_features function
        example:
            biz = Vendor.objects.get(id=1)
            print(biz.get_features())  
            # Output: ['Email Support', 'Advanced Reports']
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fullname = models.CharField(max_length=255)
    biz_name = models.CharField(max_length=255, default="")
    biz_location = models.CharField(max_length=255, default="")
    biz_contact = models.CharField(max_length=20, validators=[validate_phone], default="")
    biz_mail = models.CharField(max_length=255, default="")
    subscription_plan = models.ForeignKey('SubscriptionPlan', on_delete=models.SET_NULL, null=True)

    # Paystack fields
    paystack_secret = models.CharField(max_length=255, blank=True, null=True)
    paystack_connected = models.BooleanField(default=False)
    subscription_active = models.BooleanField(default=False)

    def __str__(self):
        return self.fullname

    def get_features(self):
        if self.subscription_plan:
            return self.subscription_plan.get_feature_list()
        return []

    
class PaystackCustomer(models.Model):
    """ create a paystack customer """
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="customers")
    customer_code = models.CharField(max_length=100, unique=True)
    email = models.EmailField()
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField()

    def __str__(self):
        return self.email



class PaystackTransaction(models.Model):
    customer = models.ForeignKey(PaystackCustomer, on_delete=models.CASCADE, related_name="transactions")
    transaction_code = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default="NGN")
    status = models.CharField(max_length=50)  # e.g. 'success', 'failed'
    paid_at = models.DateTimeField()
    reference = models.CharField(max_length=100, unique=True)
    channel = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.email} - {self.amount} ({self.status})"
