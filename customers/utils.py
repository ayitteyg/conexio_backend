import requests
from django.utils.dateparse import parse_datetime
from .models import Vendor, PaystackCustomer, PaystackTransaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime
import random
import uuid
from django.utils.timezone import now, timedelta




def sync_paystack_data(vendor):
    """ To periodically fetch Paystack data and store it, create a management command or
    API to sync customer and transaction data. 
    """
    
    headers = {
        "Authorization": f"Bearer {vendor.paystack_secret}"
    }

    # Customers
    customer_url = "https://api.paystack.co/customer"
    customer_res = requests.get(customer_url, headers=headers).json()
    for cust in customer_res.get("data", []):
        obj, _ = PaystackCustomer.objects.update_or_create(
            customer_code=cust["customer_code"],
            vendor=vendor,
            defaults={
                "email": cust["email"],
                "first_name": cust.get("first_name", ""),
                "last_name": cust.get("last_name", ""),
                "phone": cust.get("phone", ""),
                "created_at": parse_datetime(cust["createdAt"]),
            }
        )

    # Transactions
    tx_url = "https://api.paystack.co/transaction"
    tx_res = requests.get(tx_url, headers=headers, params={"perPage": 100}).json()
    for tx in tx_res.get("data", []):
        if tx["status"] != "success":
            continue
        cust_code = tx["customer"]["customer_code"]
        try:
            customer = PaystackCustomer.objects.get(customer_code=cust_code, vendor=vendor)
        except PaystackCustomer.DoesNotExist:
            continue
        PaystackTransaction.objects.update_or_create(
            reference=tx["reference"],
            vendor=vendor,
            customer=customer,
            defaults={
                "amount": tx["amount"],
                "status": tx["status"],
                "paid_at": parse_datetime(tx["paid_at"]),
            }
        )






def generate_dummy_transactions_for_customer(customer):
    """
    Generates 30 dummy PaystackTransaction records for the given customer.
    Intended for testing analytics, dashboard views, etc.
    """
    for i in range(30):
        paid_at = now() - timedelta(days=random.randint(1, 180))
        amount = round(random.uniform(500, 20000), 2)  # amount between ₦500.00 and ₦20000.00
        status = random.choice(["success"])
        reference = f"ref_{uuid.uuid4().hex[:12]}"
        transaction_code = f"txn_{uuid.uuid4().hex[:10]}"

        PaystackTransaction.objects.create(
            customer=customer,
            transaction_code=transaction_code,
            amount=amount,
            currency="NGN",
            status=status,
            paid_at=paid_at,
            reference=reference,
            channel=random.choice(["card", "bank", "ussd", "mobile_money"]),
        )



