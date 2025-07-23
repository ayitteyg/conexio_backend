from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Vendor, PaystackCustomer
import requests
from django.utils.timezone import now

@receiver(post_save, sender=Vendor)
def create_paystack_customer(sender, instance, created, **kwargs):
    if created:
        print(f"Signal triggered for Vendor: {instance}")  # Debug line

        # Optional: skip if already has customer
        if PaystackCustomer.objects.filter(vendor=instance).exists():
            return

        if not instance.paystack_secret:
            return  # Don't call Paystack if no secret

        headers = {
            "Authorization": f"Bearer {instance.paystack_secret}",
            "Content-Type": "application/json",
        }
        data = {
            "email": instance.biz_mail,
            "first_name": instance.fullname.split()[0],
        }

        response = requests.post("https://api.paystack.co/customer", headers=headers, json=data)
        res = response.json()

        if res.get("status"):
            customer_data = res["data"]
            PaystackCustomer.objects.create(
                vendor=instance,
                customer_code=customer_data["customer_code"],
                email=customer_data["email"],
                first_name=customer_data.get("first_name", ""),
                last_name=customer_data.get("last_name", ""),
                phone=customer_data.get("phone", ""),
                created_at=now()
            )
