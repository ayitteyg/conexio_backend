from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Feature, SubscriptionPlan, Vendor, PaystackCustomer, PaystackTransaction
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
    
    

@admin.register(PaystackCustomer)
class PaystackCustomerAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'email', 'first_name', 'phone', 'created_at')
    search_fields = ('email', 'first_name', 'phone', 'vendor__fullname')
    list_filter = ('vendor', 'created_at')
    
    

@admin.register(PaystackTransaction)
class PaystackTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'customer', 
        'amount', 
        'currency', 
        'status', 
        'paid_at', 
        'reference', 
        'channel', 
        'created_at'
    )
    list_filter = ('status', 'currency', 'channel', 'paid_at')
    search_fields = ('customer__email', 'transaction_code', 'reference')
    ordering = ('-paid_at',)