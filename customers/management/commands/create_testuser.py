from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Create user with custom fields'

    def handle(self, *args, **options):
        User = get_user_model()
        
        try:
            user = User.objects.create_user(
                username='0549053295',
                password='password123'
            )
            self.stdout.write(self.style.SUCCESS(f'Created user: {user.username}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))