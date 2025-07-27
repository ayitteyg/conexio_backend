
# Create your views here.
from django.conf import settings
import requests
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from .models import Vendor, SubscriptionPlan, Feature, PaystackCustomer
from .serializers import FeatureSerializer, SubscriptionPlanSerializer
from django.utils.timezone import now
from .utils import (generate_dummy_customers_and_transactions)
from django.db.models import Sum, Max
from django.utils.timesince import timesince

from django.contrib.auth import get_user_model
User = get_user_model()



@api_view(['POST'])
def signup(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password1 = request.data.get('password1')
    password2 = request.data.get('password2')

    # Check if all fields are provided
    if not all([username, email, password1, password2]):
        return Response({'message': 'All fields are required.', 'status': False},
                        status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({'message': f'{username} already exists', 'status': False},
                        status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({'message': f'{email} already exists', 'status': False},
                        status=status.HTTP_400_BAD_REQUEST)

    if password1 != password2:
        return Response({'message': 'Password mismatch', 'status': False},
                        status=status.HTTP_400_BAD_REQUEST)

    # Create user securely
    user = User.objects.create_user(username=username, email=email, password=password1)
    user.save()

    # Generate JWT token
    refresh = RefreshToken.for_user(user)
    return Response({
        'message': 'Signup Successful, Login to complete registration',
        'status': True,
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }, status=status.HTTP_201_CREATED)








@api_view(['POST'])
def signin(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({'message': 'Username and password are required', 'status': False},
                        status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=username, password=password)
    if user is not None:
        refresh = RefreshToken.for_user(user)

        return Response({
            'message': 'Login successful',
            'status': True,
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }, status=status.HTTP_200_OK)
    
    return Response({'message': 'Invalid credentials', 'status': False},
                    status=status.HTTP_401_UNAUTHORIZED)





@api_view(['POST'])
def signout(request):
    try:
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()

        return Response({"message": "logged out successfully", "status": True},
                        status=status.HTTP_205_RESET_CONTENT)
    except KeyError:
        return Response({"message": "Refresh token is required", "status": False},
                        status=status.HTTP_400_BAD_REQUEST)
    except TokenError:
        return Response({"message": "Invalid or expired token", "status": False},
                        status=status.HTTP_400_BAD_REQUEST)




