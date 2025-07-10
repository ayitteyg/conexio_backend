from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Feature, SubscriptionPlan, Vendor
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User  # your custom user model


admin.site.register(Feature)

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name']
    filter_horizontal = ['features']  # improves the M2M UI


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'biz_name', 'biz_location', 'biz_contact', 'biz_mail', 'subscription_plan')
    search_fields = ('name', 'biz_name', 'biz_mail')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email')