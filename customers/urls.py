from django.urls import path

from . import onboarding_views
from . import onboarding_views, dashboard_views, vendor_views, campaigns, auth_views


from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth-signup/', auth_views.signup, name='user-signup'),
    path('api/auth-signin/', auth_views.signin, name='user-signin'),
    path('api/auth-signout/', auth_views.signout, name='user-signout'),
    
    
    path('api/features/', vendor_views.list_create_features, name='feature-list'),
    path('api/subscription-plans/', vendor_views.list_create_subscription_plans, name='subscription-plan-list'),
    
    #vendor api
    path('api/create-vendor/', vendor_views.create_vendor, name='create-vendor'),
    path("api/vendors/", vendor_views.list_vendors, name="list-vendors"),
    
    
    # paystack api
    #path('api/connect-paystack/', onboarding_views.connect_paystack, name='connect-paystack'),
    path('api/initiate-subscription/', onboarding_views.initiate_subscription, name='initiate-subscription'),
    path('api/verify-transaction/<str:reference>/', onboarding_views.verify_transaction, name='verify-transaction'),
    path("api/paystack-customers/", onboarding_views.get_paystack_customers, name="paystack-customers"),
    
    #fullpaystack onboard
    path('api/connect-paystack/', onboarding_views.full_paystack_onboard, name='connect-paystack'),
    
    
    #customer dashboard / segmentations
    path("api/customers-segment-filter/", dashboard_views.dynamic_segment_filter, name="dynamic-segment-filter"),
    path("api/vendor-dashboard/", dashboard_views.vendor_dashboard, name="vendor-dashboard"),
    path("api/customer-segments/", dashboard_views.get_customer_segments, name="get_customer_segments"),

    
    #campaigns
    path("api/email-campaigns/", campaigns.TestSendEmailsView.as_view(), name="email-campaigns")
]   