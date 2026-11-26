from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Create a superuser automatically'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        
        # We are now using EMAIL instead of username
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if not email or not password:
            self.stdout.write(self.style.WARNING('Skipping superuser creation: missing environment variables'))
            return

        if not User.objects.filter(email=email).exists():
            # Create the user using the email field
            User.objects.create_superuser(
                email=email,
                password=password
            )
            self.stdout.write(self.style.SUCCESS(f'Superuser {email} created successfully'))
        else:
            self.stdout.write(self.style.WARNING(f'Superuser {email} already exists'))