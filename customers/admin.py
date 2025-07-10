from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Feature, SubscriptionPlan, Vendor

admin.site.register(Feature)

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name']
    filter_horizontal = ['features']  # improves the M2M UI

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['name', 'subscription_plan']
