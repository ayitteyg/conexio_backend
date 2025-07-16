

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
from .models import Vendor, SubscriptionPlan, Feature
from .serializers import FeatureSerializer, SubscriptionPlanSerializer

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



@api_view(['GET', 'POST'])
def list_create_features(request):
    """GET: List all features; POST: Create a new feature."""
    if request.method == 'GET':
        features = Feature.objects.all()
        serializer = FeatureSerializer(features, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = FeatureSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET', 'POST'])
def list_create_subscription_plans(request):
    """GET: List all subscription plans; POST: Create a new plan with features."""
    if request.method == 'GET':
        plans = SubscriptionPlan.objects.all()
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = SubscriptionPlanSerializer(data=request.data)
        if serializer.is_valid():
            plan = serializer.save()
            plan.features.set(serializer.validated_data['features'])  # link features
            return Response(SubscriptionPlanSerializer(plan).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_vendor(request):
    user = request.user
    data = request.data

    if Vendor.objects.filter(user=user).exists():
        return Response({"error": "Vendor already exists for this user"}, status=400)

    # Step 1: Ensure default features exist
    default_features = [
        {"name": "Email Support", "description": "Get support via email"},
        {"name": "Basic Reports", "description": "Access to basic analytics"},
    ]

    feature_objs = []
    for feat in default_features:
        feature, _ = Feature.objects.get_or_create(name=feat["name"], defaults={"description": feat["description"]})
        feature_objs.append(feature)

    # Step 2: Create or get the 'basic' plan and assign default features
    basic_plan, created = SubscriptionPlan.objects.get_or_create(name='basic')
    if created:
        basic_plan.features.set(feature_objs)  # Assign only if newly created

    # Step 3: Create the vendor : request.post.data
    # vendor = Vendor.objects.create(
    #     user=user,
    #     fullname=data.get("fullname"),
    #     biz_name=data.get("biz_name", ""),
    #     biz_location=data.get("biz_location", ""),
    #     biz_contact=data.get("biz_contact", ""),
    #     biz_mail=data.get("biz_mail", ""),
    #     subscription_plan=basic_plan
    # )

    vendor = Vendor.objects.get_or_create(
        user=user,
        fullname="vendor1",
        biz_name="Kwame Foods",
        biz_location="Accra",
        biz_contact="0244000000",
        biz_mail="kwame@example.com",
        subscription_plan=basic_plan
    )

    return Response({"message": "Vendor created successfully", "vendor_id": vendor.id}, status=201)


 
 
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def connect_paystack(request):
    user = request.user
    print("Authenticated user:", user)

    try:
        vendor = Vendor.objects.get(user=user)
        print("Found vendor:", vendor)
    except Vendor.DoesNotExist:
        return Response({"error": "Vendor not found"}, status=404)

    paystack_key = request.data.get("paystack_secret")
    if not paystack_key or not paystack_key.startswith("sk_"):
        return Response({"error": "Invalid Paystack secret key"}, status=400)

    vendor.paystack_secret = paystack_key
    vendor.paystack_connected = True
    vendor.save()

    print("Vendor updated:", vendor.paystack_connected, vendor.paystack_secret)

    return Response({"message": "Paystack connected successfully"})




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_subscription(request):
    try:
        vendor = Vendor.objects.get(user=request.user)
    except Vendor.DoesNotExist:
        return Response({"error": "Vendor not found"}, status=404)

    if not vendor.paystack_secret:
        return Response({"error": "Vendor has not connected Paystack"}, status=400)

    #email = request.data.get("email")
    #amount = request.data.get("amount")
    
    email = vendor.user.email
    amount = 100

    if not email or not amount:
        return Response({"error": "Email and amount are required"}, status=400)

    headers = {
        "Authorization": f"Bearer {vendor.paystack_secret}",
        "Content-Type": "application/json"
    }

    payload = {
        "email": email,
        "amount": amount,
        "callback_url": settings.PAYSTACK_CALLBACK_URL
    }

    response = requests.post(
        "https://api.paystack.co/transaction/initialize",
        headers=headers,
        json=payload
    )

    if response.status_code == 200 and response.json().get("status"):
        data = response.json()["data"]
        return Response({
            "authorization_url": data["authorization_url"],
            "reference": data["reference"]
        })
    else:
        return Response({
            "error": "Failed to initiate payment",
            "details": response.json()
        }, status=400)







# verify vendor subscription transactions
@api_view(['GET'])
def verify_transaction(request, reference):
    vendor = Vendor.objects.get(user=request.user)

    headers = {
        "Authorization": f"Bearer {vendor.paystack_secret}",
    }
    response = requests.get(
        f"https://api.paystack.co/transaction/verify/{reference}",
        headers=headers
    )
    res_data = response.json()

    if res_data["status"] and res_data["data"]["status"] == "success":
        # Mark vendor as subscribed
        vendor.subscription_active = True
        vendor.save()
        return Response({"message": "Subscription verified and activated"})
    return Response({"error": "Verification failed"}, status=400)



#getting client customers
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_paystack_customers(request):
    """
    Retrieve all customers from the Paystack account linked to the authenticated vendor.

    Requirements:
    - User must be authenticated
    - Vendor must exist and have connected a Paystack secret key

    Returns:
    - 200 OK with list of customers from Paystack
    - 400 Bad Request if Paystack is not connected or Paystack API fails
    - 404 if Vendor is not found
    - 500 Internal Server Error for connection issues
    """
    user = request.user

    try:
        vendor = Vendor.objects.get(user=user)
        print("Found vendor:", vendor)
    except Vendor.DoesNotExist:
        return Response({"error": "Vendor not found"}, status=404)

    if not vendor.paystack_secret:
        return Response({"error": "Vendor has not connected Paystack"}, status=400)

    headers = {
        "Authorization": f"Bearer {vendor.paystack_secret}",
        "Content-Type": "application/json"
    }

    url = "https://api.paystack.co/customer"

    try:
        res = requests.get(url, headers=headers)
        data = res.json()

        if res.status_code == 200 and data.get("status") is True:
            return Response(data.get("data", []), status=200)
        else:
            return Response({"error": data.get("message", "Failed to fetch customers")}, status=400)

    except requests.exceptions.RequestException as e:
        print("Paystack request error:", e)
        return Response({"error": "Failed to connect to Paystack"}, status=500)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def full_paystack_onboard(request):
    user = request.user
    paystack_secret = request.data.get("paystack_secret")

    if not paystack_secret or not paystack_secret.startswith("sk_"):
        return Response({"error": "Invalid Paystack secret key"}, status=400)

    # Step 1: Ensure default features exist
    default_features = [
        {"name": "Email Support", "description": "Get support via email"},
        {"name": "Basic Reports", "description": "Access to basic analytics"},
    ]
    feature_objs = []
    for feat in default_features:
        feature, _ = Feature.objects.get_or_create(
            name=feat["name"],
            defaults={"description": feat["description"]}
        )
        feature_objs.append(feature)

    # Step 2: Create or get the 'basic' plan and assign default features if new
    basic_plan, created = SubscriptionPlan.objects.get_or_create(name='basic')
    if created:
        basic_plan.features.set(feature_objs)  # Only assign features if newly created


    # Step 3: Create or get Vendor
    vendor, created = Vendor.objects.get_or_create(
        user=user,
        defaults={
            "fullname": "vendor 1",
            "subscription_plan": basic_plan,
            "biz_name": "Inovation labs",
            "biz_location": "Accra - Ghana",
            "biz_contact": "0000000000",
            "biz_mail": user.email,
        }
    )

    # Step 4: Save Paystack secret
    vendor.paystack_secret = paystack_secret
    vendor.paystack_connected = True
    vendor.subscription_plan = basic_plan  # ensure even existing ones get it
    vendor.save()

    # Step 5: Initiate Paystack Transaction
    headers = {
        "Authorization": f"Bearer {paystack_secret}",
        "Content-Type": "application/json"
    }
    payload = {
        "email": user.email,
        "amount": 100 * 100,  # Paystack uses Kobo
        "callback_url": settings.PAYSTACK_CALLBACK_URL
    }

    response = requests.post("https://api.paystack.co/transaction/initialize", headers=headers, json=payload)

    if response.status_code == 200 and response.json().get("status"):
        data = response.json()["data"]
        return Response({
            "message": "Onboarding complete. Redirect to payment page.",
            "authorization_url": data["authorization_url"],
            "reference": data["reference"]
        })

    return Response({
        "error": "Failed to initiate payment",
        "details": response.json()
    }, status=400)
