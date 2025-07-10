from django.urls import path
from . import views


from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .vendor_views import VendorRegisterView

urlpatterns = [
    path('api/register/', VendorRegisterView.as_view(), name='vendor-register'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth-signup/', views.signup, name='user-signup'),
    path('api/auth-signin/', views.signin, name='user-signin'),
    path('api/auth-signout/', views.signout, name='user-signout'),
]   