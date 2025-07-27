from rest_framework import generics
from .models import Vendor
from .serializers import VendorSerializer, VendorListSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Vendor, SubscriptionPlan, Feature, PaystackCustomer
from .serializers import FeatureSerializer, SubscriptionPlanSerializer
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Prefetch
from django.core.cache import cache





class VendorRegisterView(generics.CreateAPIView):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer



@api_view(["GET"])
@permission_classes([IsAuthenticated])  # Optional: You can remove if public
def list_vendors(request):
    """
    Returns a list of all vendors and their basic details.
    """
    vendors = Vendor.objects.all()
    serializer = VendorListSerializer(vendors, many=True)
    return Response(serializer.data)




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
@permission_classes([IsAuthenticated])
def create_vendor(request):
    """ create a vendor for the signup user: if a separate form for vendor creation is needed """
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

    #using dummy data to test creation
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


 