from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Create superuser with custom fields'

    def handle(self, *args, **options):
        User = get_user_model()
        
        try:
            user = User.objects.create_superuser(
                username='admin',
                password='my-mtn-0549',
                email='sdaachimotadistrict@gmail.com'
            )
            self.stdout.write(self.style.SUCCESS(f'Created superuser: {user.username}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))