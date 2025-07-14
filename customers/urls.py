from django.urls import path
from . import onboarding_views, dashboard_views, vendor_views


from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth-signup/', onboarding_views.signup, name='user-signup'),
    path('api/auth-signin/', onboarding_views.signin, name='user-signin'),
    path('api/auth-signout/', onboarding_views.signout, name='user-signout'),
    
    #vendor api
    path('api/create-vendor/', onboarding_views.create_vendor, name='create-vendor'),
    path("api/vendors/", vendor_views.list_vendors, name="list-vendors"),
    
    
    # paystack api
    path('api/connect-paystack/', onboarding_views.connect_paystack, name='connect-paystack'),
    path('api/initiate-subscription/', onboarding_views.initiate_subscription, name='initiate-subscription'),
    path('api/verify-transaction/<str:reference>/', onboarding_views.verify_transaction, name='verify-transaction'),
    path("api/paystack-customers/", onboarding_views.get_paystack_customers, name="paystack-customers"),
    
    
    #customer dashboard / segmentations
    path("api/customers-segment-filter/", dashboard_views.dynamic_segment_filter, name="dynamic-segment-filter"),
    path("api/vendor-dashboard/", dashboard_views.vendor_dashboard, name="vendor-dashboard"),
]   