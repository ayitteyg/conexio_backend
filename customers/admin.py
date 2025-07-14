from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Feature, SubscriptionPlan, Vendor
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
User = get_user_model()

admin.site.register(Feature)

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name']
    filter_horizontal = ['features']  # improves the M2M UI


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('fullname', 'biz_name', 'biz_location', 'biz_contact', 'biz_mail', 'subscription_plan', 'paystack_connected', 'subscription_active')
    search_fields = ('fullname', 'biz_name', 'biz_mail', 'subscription_active')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email')
    
    
        
