from django.urls import path
from . import views


from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .vendor_views import VendorRegisterView

urlpatterns = [
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth-signup/', views.signup, name='user-signup'),
    path('api/auth-signin/', views.signin, name='user-signin'),
    path('api/auth-signout/', views.signout, name='user-signout'),
    
    #vendor api
    path('api/create-vendor/', views.create_vendor, name='create-vendor'),
    
    
    # paystack api
    path('api/connect-paystack/', views.connect_paystack, name='connect-paystack'),
    path('api/initiate-subscription/', views.initiate_subscription, name='initiate-subscription'),
    path('api/verify-transaction/<str:reference>/', views.verify_transaction, name='verify-transaction'),
]   