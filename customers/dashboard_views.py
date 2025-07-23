from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import PaystackCustomer, PaystackTransaction, Vendor
import requests
from django.utils import timezone
from datetime import timedelta, datetime
import pytz 




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def vendor_dashboard(request):
    user = request.user
    try:
        vendor = Vendor.objects.get(user=user)
    except Vendor.DoesNotExist:
        return Response({"error": "Vendor not found"}, status=404)

    customers = PaystackCustomer.objects.filter(vendor=vendor)
    transactions = PaystackTransaction.objects.filter(customer__vendor=vendor, status="success")

    total_customers = customers.count()
    total_orders = transactions.count()
    total_value = sum(tx.amount for tx in transactions) / 100
    avg_order_value = round(total_value / total_orders, 2) if total_orders else 0

    from datetime import datetime, timedelta

    tx_map = {}
    for tx in transactions:
        tx_map.setdefault(tx.customer.customer_code, []).append(tx)

    
    
    now = timezone.now()
    loyal = high_value = at_risk = dormant = 0

    for customer in customers:
        txs = tx_map.get(customer.customer_code, [])
        total_spent = sum(tx.amount for tx in txs) / 100
        order_count = len(txs)
        last_tx_date = max((tx.paid_at for tx in txs), default=None)

        # Convert transaction dates to timezone-aware datetimes
        txs_with_dates = []
        for tx in txs:
            tx_date = tx.paid_at 
            txs_with_dates.append((tx, tx_date))

        last_tx_date = max((tx_date for _, tx_date in txs_with_dates), default=None)

        # Loyal: ≥3 orders in last 90 days
        recent_order_count = sum(
            1 for _, tx_date in txs_with_dates
            if tx_date >= now - timedelta(days=90)
        )
        if order_count >= 3 and recent_order_count >= 3:
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
        
        
        return Response({
            "total_customers": total_customers,
            "total_orders": total_orders,
            "average_order_value": avg_order_value,
            "segments": {
                "loyal_customers": loyal,
                "high_value_customers": high_value,
                "at_risk_customers": at_risk,
                "dormant_customers": dormant,
            }
        })






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
