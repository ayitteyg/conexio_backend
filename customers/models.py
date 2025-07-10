from django.db import models
from django.contrib.auth.models import AbstractUser

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
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    biz_name = models.CharField(max_length=255, default="")
    biz_location = models.CharField(max_length=255, default="")
    biz_contact = models.CharField(max_length=20, validators=[validate_phone], default="")
    biz_mail = models.CharField(max_length=255, default="")
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name

    def get_features(self):
        if self.subscription_plan:
            return self.subscription_plan.get_feature_list()
        return []


    
class Customer(models.Model):
    """
    STORES CUSTOMER DATA WITH BEHAVIORAL ATTRIBUTES
    """
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    email = models.EmailField(unique=True)
    
    # Store segments as a comma-separated string or JSON string
    segments = models.TextField(default="[]")  # Store JSON list as string

    # Store behavior_data as a JSON string
    behavior_data = models.TextField(default="{}")  # Store JSON dict as string

    created_at = models.DateTimeField(auto_now_add=True)

    def set_segments(self, segments_list):
        self.segments = json.dumps(segments_list)

    def get_segments(self):
        return json.loads(self.segments or "[]")

    def set_behavior_data(self, data_dict):
        self.behavior_data = json.dumps(data_dict)

    def get_behavior_data(self):
        return json.loads(self.behavior_data or "{}")



class Campaign(models.Model):
    """
    AUTOMATED MARKETING CAMPAIGN CONFIG
    
    Trigger Types:
        - purchase: Post-purchase sequence
        - inactive: Re-engagement flow
    """
    TRIGGER_TYPES = [
        ('purchase', 'After Purchase'),
        ('inactive', 'Customer Inactive'),
    ]
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    trigger_type = models.CharField(max_length=50, choices=TRIGGER_TYPES)
    delay_hours = models.PositiveIntegerField()
    message_template = models.TextField()