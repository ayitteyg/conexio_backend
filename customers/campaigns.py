from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.timezone import now
from datetime import timedelta
from .models import PaystackCustomer, PaystackTransaction, Vendor
from .utils import send_email_to_customers, send_sms_to_customers, send_email_to_customers_using_sendgrid  # You'll define this utility
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_campaign(request):
    user = request.user
    segment = request.data.get("segment")
    channel = request.data.get("channel")
    subject = request.data.get("subject", "")
    message = request.data.get("message")

    if not segment or not channel or not message:
        return Response({"error": "Missing fields"}, status=400)

    try:
        vendor = Vendor.objects.get(user=user)
    except Vendor.DoesNotExist:
        return Response({"error": "Vendor not found"}, status=404)

    customers = PaystackCustomer.objects.filter(vendor=vendor)
    transactions = PaystackTransaction.objects.filter(customer__vendor=vendor, status="success")

    now_dt = now()
    tx_map = {tx.customer_id: [] for tx in customers}
    for tx in transactions:
        tx_map.setdefault(tx.customer_id, []).append(tx)

    # Filter customers by segment
    matched_customers = []
    for customer in customers:
        txs = tx_map.get(customer.id, [])
        total_spent = sum(tx.amount for tx in txs) / 100
        order_count = len(txs)
        last_tx_date = max((tx.paid_at for tx in txs), default=None)

        if segment == "Loyal Customers":
            recent_order_count = sum(1 for tx in txs if tx.paid_at >= now_dt - timedelta(days=90))
            if order_count >= 3 and recent_order_count >= 3:
                matched_customers.append(customer)

        elif segment == "High Value Customers" and total_spent > 500:
            matched_customers.append(customer)

        elif segment == "At-Risk Customers" and last_tx_date and (now_dt - last_tx_date).days >= 30:
            matched_customers.append(customer)

        elif segment == "Dormant Customers" and (not txs or (last_tx_date and (now_dt - last_tx_date).days >= 90)):
            matched_customers.append(customer)

    # Send messages
    if channel == "email":
        send_email_to_customers_using_sendgrid(matched_customers, subject, message)
    elif channel == "sms":
        pass
       

    return Response({
        "message": f"Campaign sent to {len(matched_customers)} {segment} customers via {channel}."
    })



class TestSendEmailsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        subject = "Test Campaign"
        message = "Hello {name}, this is a test email from Conexio."

        class DummyCustomer:
            def __init__(self, email, first_name):
                self.email = email
                self.first_name = first_name

        customers = [
            DummyCustomer("ayitteyg@yahoo.com", "Test1"),
            DummyCustomer("ayittey.og@gmail.com", "Test2"),
        ]

        send_email_to_customers_using_sendgrid(customers, subject, message)
        return Response({"detail": "Dummy emails sent successfully."})



