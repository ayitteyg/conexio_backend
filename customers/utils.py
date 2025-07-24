import requests
from django.utils.dateparse import parse_datetime
from .models import Vendor, PaystackCustomer, PaystackTransaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime
import random
import uuid
from django.utils.timezone import now, timedelta
import faker





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





fake = faker.Faker()

def generate_dummy_customers_for_vendor(vendor):
    """
    Generate 30 dummy PaystackCustomer entries for the given Vendor.
    Useful for testing frontend customer dashboard.
    """
    for i in range(30):
        name = fake.name()
        email = fake.unique.email()
        customer_code = f"DUMMY-CUST-{vendor.id}-{i}-{random.randint(1000, 9999)}"
        created_at = now() - timedelta(days=random.randint(1, 180))

        PaystackCustomer.objects.create(
            vendor=vendor,
            name=name,
            email=email,
            customer_code=customer_code,
            created_at=created_at,
        )



def generate_dummy_customers_and_transactions(vendor):
    for i in range(30):
        name = fake.name()
        email = fake.unique.email()
        customer_code = f"DUMMY-CUST-{vendor.id}-{i}-{random.randint(1000, 9999)}"
        created_at = now() - timedelta(days=random.randint(1, 180))

        customer = PaystackCustomer.objects.create(
            vendor=vendor,
            name=name,
            email=email,
            customer_code=customer_code,
            created_at=created_at,
        )

        generate_dummy_transactions_for_customer(customer)




import string
def generate_dummy_customers_and_transactions(vendor, count=30, tx_per_customer=10):
    for _ in range(count):
        email = f"{''.join(random.choices(string.ascii_lowercase, k=6))}@example.com"
        customer = PaystackCustomer.objects.create(
            vendor=vendor,
            customer_code='DUMMY_' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10)),
            email=email,
            first_name="Test",
            last_name="Customer",
            phone="0550000000",
            created_at=now()
        )

        for _ in range(tx_per_customer):
            amount = round(random.uniform(1000, 10000), 2)  # 10.00 to 100.00 NGN in Kobo
            PaystackTransaction.objects.create(
                customer=customer,
                transaction_code="TXC-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10)),
                amount=amount,
                status="success",
                paid_at=now(),
                reference="TXR-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=12)),
                channel="card"
            )
