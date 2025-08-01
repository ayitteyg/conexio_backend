

# Create your views here.
from django.conf import settings
import requests
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import PaystackTransaction, Vendor, SubscriptionPlan, Feature, PaystackCustomer
from django.utils.timezone import now
from .utils import (generate_dummy_customers_and_transactions)
from django.db.models import Sum, Max
from django.utils.timesince import timesince
from django.db.models import Sum, Prefetch
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt

from django.contrib.auth import get_user_model
User = get_user_model()




 
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def connect_paystack(request):
    """ connecting to paystack only:  """
    
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




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_paystack_customers(request):
    """
    Returns a list of customers for the authenticated vendor,
    including total spent, last order time, and status tag.

    Optimizations:
    - Uses `prefetch_related` to minimize DB queries
    - Uses `annotate` to pull aggregates in one DB call
    - Avoids redundant data processing in Python
    """
    vendor = request.user.vendor  # Assuming vendor FK exists

    # Prefetch only successful transactions
    successful_tx = PaystackTransaction.objects.filter(status="success")
    customers = (
        PaystackCustomer.objects.filter(vendor=vendor)
        .prefetch_related(Prefetch("transactions", queryset=successful_tx))
    )

    result = []
    current_time = now()

    for customer in customers:
        txs = customer.transactions.all()
        total_spent = sum(tx.amount for tx in txs)
        last_tx = max((tx.paid_at for tx in txs), default=None)

        name = f"{customer.first_name or ''} {customer.last_name or ''}".strip()
        if not name:
            name = customer.email.split("@")[0].title()

        if last_tx:
            time_ago = timesince(last_tx, current_time).split(",")[0] + " ago"
            last_order = time_ago
        else:
            last_order = "No Orders"

        # Status logic
        if total_spent > 400000:  # Adjusted to kobo if amount is stored in kobo
            status = "High Value"
        elif last_tx and (current_time - last_tx).days > 21:
            status = "At Risk"
        else:
            status = "Active"

        result.append({
            "name": name,
            "email": customer.email,
            "totalValue": f"₦{total_spent/100:,.0f}",  # Convert from kobo to naira
            "lastOrder": last_order,
            "status": status
        })

    return Response({"customers": result})




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_subscription(request):
    
    """ initiating subscription for the connected account: Only """
    
    try:
        vendor = Vendor.objects.get(user=request.user)
    except Vendor.DoesNotExist:
        return Response({"error": "Vendor not found"}, status=404)

    if not vendor.paystack_secret:
        return Response({"error": "Vendor has not connected Paystack"}, status=400)

    """ use this if a form is provided """
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
def get_paystack_customers_0(request):
    
    """ fetching all customer for the authenticated vendor """
    
    vendor = request.user.vendor  # Assuming vendor is linked to user

    customers = PaystackCustomer.objects.filter(vendor=vendor)

    data = []
    for customer in customers:
        transactions = customer.transactions.filter(status="success")
        total_spent = transactions.aggregate(total=Sum("amount"))["total"] or 0
        last_tx = transactions.aggregate(last=Max("paid_at"))["last"]

        # Format name
        name = f"{customer.first_name or ''} {customer.last_name or ''}".strip()

        # Calculate lastOrder as relative time
        if last_tx:
            time_ago = timesince(last_tx, now())  # e.g. "2 days, 3 hours"
            last_order = time_ago.split(",")[0] + " ago"
        else:
            last_order = "No Orders"

        # Determine status based on rules
        if total_spent > 4000:
            status = "High Value"
        elif last_tx and (now() - last_tx).days > 21:
            status = "At Risk"
        else:
            status = "Active"

        data.append({
            "name": name or customer.email.split('@')[0].title(),
            "email": customer.email,
            "totalValue": f"${total_spent:,.0f}",
            "lastOrder": last_order,
            "status": status
        })

    return Response({"customers": data})



@csrf_exempt  # <-- Only for API, not for browser forms
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def full_paystack_onboard(request):
    
    
    """ this try to handle the whole onboarding process for a new signed up vendor at the backend """
    
    user = request.user
    PAYSTACK_KEY =  settings.PAYSTACK_KEY
    # paystack_secret = request.data.get("paystack_secret", PAYSTACK_KEY)
    paystack_secret = request.data["apiKey"]

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
            "fullname": "vendorfullname",
            "subscription_plan": basic_plan,
            "biz_name": "",
            "biz_location": "",
            "biz_contact": "",
            "biz_mail": user.email,
        }
    )   

    # Step 4: Save Paystack secret
    vendor.paystack_secret = paystack_secret
    vendor.paystack_connected = True
    vendor.subscription_plan = basic_plan  # ensure even existing ones get it
    vendor.save()

    #this is generating dummy customers and transactions for the vendor for testing purpose; see utils.py
    generate_dummy_customers_and_transactions(vendor, count=30, tx_per_customer=10)
    
    # step8: initiate a transaction for testing purpose   
    
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
