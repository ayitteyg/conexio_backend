from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Vendor
from datetime import datetime, timedelta
import requests


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def vendor_dashboard(request):
    """
    Returns vendor dashboard analytics:
    - Total customers
    - Total successful orders
    - Average order value
    - Segment counts: loyal, high-value, at-risk, dormant
    """

    user = request.user

    try:
        vendor = Vendor.objects.get(user=user)
    except Vendor.DoesNotExist:
        return Response({"error": "Vendor not found"}, status=404)

    if not vendor.paystack_secret:
        return Response({"error": "Paystack not connected"}, status=400)

    headers = {
        "Authorization": f"Bearer {vendor.paystack_secret}"
    }

    # Customers
    customers_res = requests.get("https://api.paystack.co/customer", headers=headers).json()
    customers = customers_res.get("data", [])

    # Transactions
    tx_res = requests.get("https://api.paystack.co/transaction", headers=headers, params={"perPage": 100}).json()
    transactions = [tx for tx in tx_res.get("data", []) if tx.get("status") == "success"]

    # Calculate totals
    total_customers = len(customers)
    total_orders = len(transactions)
    total_value = sum(tx.get("amount", 0) / 100 for tx in transactions)
    avg_order_value = round(total_value / total_orders, 2) if total_orders else 0

    # Build customer transaction map
    tx_map = {}
    for tx in transactions:
        cust_code = tx.get("customer", {}).get("customer_code")
        if cust_code:
            tx_map.setdefault(cust_code, []).append(tx)

    now = datetime.utcnow()
    loyal, high_value, at_risk, dormant = [], [], [], []

    for customer in customers:
        code = customer.get("customer_code")
        txs = tx_map.get(code, [])
        total_spent = sum(tx["amount"] / 100 for tx in txs)
        order_count = len(txs)

        last_tx_date = max(
            (datetime.strptime(tx["paid_at"], "%Y-%m-%dT%H:%M:%S.%fZ") for tx in txs),
            default=None
        )

        # Loyal: ≥3 orders in last 90 days
        if order_count >= 3:
            recent = [
                tx for tx in txs
                if datetime.strptime(tx["paid_at"], "%Y-%m-%dT%H:%M:%S.%fZ") >= now - timedelta(days=90)
            ]
            if len(recent) >= 3:
                loyal.append(customer)

        # High value: spent > 500
        if total_spent > 500:
            high_value.append(customer)

        # At-risk: last order ≥ 30 days ago
        if last_tx_date and (now - last_tx_date).days >= 30:
            at_risk.append(customer)

        # Dormant: no tx or inactive ≥ 90 days
        if not txs or (last_tx_date and (now - last_tx_date).days >= 90):
            dormant.append(customer)

    return Response({
        "total_customers": total_customers,
        "total_orders": total_orders,
        "average_order_value": avg_order_value,
        "segments": {
            "loyal_customers": len(loyal),
            "high_value_customers": len(high_value),
            "at_risk_customers": len(at_risk),
            "dormant_customers": len(dormant),
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
