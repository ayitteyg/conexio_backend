from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import PaystackCustomer, PaystackTransaction, Vendor
import requests
from django.utils import timezone
from datetime import timedelta, datetime
import pytz 
from django.db.models import Sum, Prefetch
from django.core.cache import cache




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def vendor_dashboard(request):
    """
    Returns dashboard metrics for the authenticated vendor:
    - Total customers
    - Total orders
    - Average order value
    - Customer segmentation:
        - Loyal customers: ≥3 orders in last 90 days
        - High-value customers: spent > ₦500
        - At-risk customers: no order in ≥30 days
        - Dormant customers: no order or inactive ≥90 days

    Optimization:
    - Uses prefetch_related to minimize DB hits
    - Uses aggregate to compute totals in the database
    - Optional: caches the response for 5 minutes
    """
    user = request.user

    # Get associated vendor
    try:
        vendor = Vendor.objects.get(user=user)
    except Vendor.DoesNotExist:
        return Response({"error": "Vendor not found"}, status=404)

    # Optional: Check cache
    cache_key = f"vendor_dashboard_{vendor.id}"
    cached = cache.get(cache_key)
    if cached:
        return Response(cached)

    # Prefetch successful transactions per customer
    transactions_qs = PaystackTransaction.objects.filter(status="success")
    customers = PaystackCustomer.objects.filter(vendor=vendor).prefetch_related(
        Prefetch("transactions", queryset=transactions_qs)
    )

    # All transactions
    transactions = transactions_qs.filter(customer__vendor=vendor)

    # Total metrics
    total_customers = customers.count()
    total_orders = transactions.count()
    total_value = transactions.aggregate(total=Sum("amount"))["total"] or 0
    total_value /= 100  # Convert kobo to naira
    avg_order_value = round(total_value / total_orders, 2) if total_orders else 0

    # Segment customers
    now = timezone.now()
    loyal = high_value = at_risk = dormant = 0

    for customer in customers:
        txs = customer.paystacktransaction_set.all()
        order_count = txs.count()
        total_spent = sum(tx.amount for tx in txs) / 100  # Convert to naira
        last_tx_date = max((tx.paid_at for tx in txs), default=None)

        # Loyal: ≥3 orders in last 90 days
        recent_order_count = sum(
            1 for tx in txs if tx.paid_at and tx.paid_at >= now - timezone.timedelta(days=90)
        )
        if order_count >= 3 and recent_order_count >= 3:
            loyal += 1

        # High-value: total spend > ₦500
        if total_spent > 500:
            high_value += 1

        # At-risk: last order ≥ 30 days ago
        if last_tx_date and (now - last_tx_date).days >= 30:
            at_risk += 1

        # Dormant: no tx or inactive ≥ 90 days
        if not txs or (last_tx_date and (now - last_tx_date).days >= 90):
            dormant += 1

    data = {
        "total_customers": total_customers,
        "total_orders": total_orders,
        "average_order_value": avg_order_value,
        "segments": {
            "loyal_customers": loyal,
            "high_value_customers": high_value,
            "at_risk_customers": at_risk,
            "dormant_customers": dormant,
        }
    }

    # Optional cache
    cache.set(cache_key, data, timeout=300)  # 5 minutes

    return Response(data)




@api_view(["POST"])
@permission_classes([IsAuthenticated])
def dynamic_segment_filter(request):
    """
    Filters vendor's Paystack customers dynamically based on provided criteria:
    - spend_more_than
    - ordered_in_last
    - last_visited
    """

    user = request.user
    data = request.data
    filter_type = data.get("filter_type")
    value = float(data.get("value", 0))
    days = int(data.get("days", 0))

    try:
        vendor = Vendor.objects.get(user=user)
    except Vendor.DoesNotExist:
        return Response({"error": "Vendor not found"}, status=404)

    if not vendor.paystack_secret:
        return Response({"error": "Vendor has not connected Paystack"}, status=400)

    headers = {
        "Authorization": f"Bearer {vendor.paystack_secret}"
    }

    customer_res = requests.get("https://api.paystack.co/customer", headers=headers).json()
    customers = customer_res.get("data", [])

    tx_res = requests.get("https://api.paystack.co/transaction", headers=headers, params={"perPage": 100}).json()
    transactions = [tx for tx in tx_res.get("data", []) if tx.get("status") == "success"]

    now = datetime.utcnow()
    tx_map = {}
    for tx in transactions:
        customer_code = tx.get("customer", {}).get("customer_code")
        if customer_code:
            tx_map.setdefault(customer_code, []).append(tx)

    matching_customers = []

    for customer in customers:
        code = customer.get("customer_code")
        txs = tx_map.get(code, [])

        total_spent = sum(tx["amount"] / 100 for tx in txs)
        num_orders = len(txs)
        last_tx_date = max(
            (datetime.strptime(tx["paid_at"], "%Y-%m-%dT%H:%M:%S.%fZ") for tx in txs),
            default=None
        )

        # Apply filter
        if filter_type == "spend_more_than" and total_spent > value:
            matching_customers.append(customer)

        elif filter_type == "ordered_in_last":
            period_start = now - timedelta(days=days)
            recent_orders = [tx for tx in txs if datetime.strptime(tx["paid_at"], "%Y-%m-%dT%H:%M:%S.%fZ") >= period_start]
            if len(recent_orders) >= value:
                matching_customers.append(customer)

        elif filter_type == "last_visited":
            if last_tx_date and (now - last_tx_date).days <= days:
                matching_customers.append(customer)

    return Response({
        "count": len(matching_customers),
        "customers": matching_customers
    })




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_customer_segments(request):
    """
    Return customer segmentation data for the authenticated vendor.
    Segments include:
    - Loyal Customers: >=3 orders in the last 90 days
    - High Value Customers: spent > ₦500
    - At-Risk Customers: last transaction >= 30 days ago
    - Dormant Customers: no transaction or inactive for >= 90 days

    Results are cached per vendor for 1 day.
    """
    user = request.user
    try:
        vendor = Vendor.objects.get(user=user)
    except Vendor.DoesNotExist:
        return Response({"error": "Vendor not found"}, status=404)

    cache_key = f"segments_{vendor.id}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return Response(cached_data)

    # Fetch vendor's customers and their transactions
    customers = PaystackCustomer.objects.filter(vendor=vendor)
    transactions = PaystackTransaction.objects.filter(
        customer__vendor=vendor,
        status="success"
    )

    # Organize transactions per customer code
    tx_map = {}
    for tx in transactions:
        tx_map.setdefault(tx.customer.customer_code, []).append(tx)

    now = timezone.now()
    loyal = high_value = at_risk = dormant = 0

    for customer in customers:
        txs = tx_map.get(customer.customer_code, [])
        total_spent = sum(tx.amount for tx in txs) / 100  # kobo to naira
        last_tx_date = max((tx.paid_at for tx in txs), default=None)

        # Loyal: ≥3 orders in last 90 days
        recent_order_count = sum(
            1 for tx in txs if tx.paid_at >= now - timedelta(days=90)
        )
        if len(txs) >= 3 and recent_order_count >= 3:
            loyal += 1

        # High value: spent > 500
        if total_spent > 500:
            high_value += 1

        # At-risk: last order ≥ 30 days ago
        if last_tx_date and (now - last_tx_date).days >= 30:
            at_risk += 1

        # Dormant: no tx or inactive ≥ 90 days
        if not txs or (last_tx_date and (now - last_tx_date).days >= 90):
            dormant += 1

    data = {
        "loyal_customers": loyal,
        "high_value_customers": high_value,
        "at_risk_customers": at_risk,
        "dormant_customers": dormant,
    }

    # Cache the result for 1 day (86400 seconds)
    cache.set(cache_key, data, timeout=86400)

    return Response(data)
