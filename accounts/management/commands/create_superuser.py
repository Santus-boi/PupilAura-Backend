from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Create a superuser automatically'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if not username or not password:
            self.stdout.write(self.style.WARNING('Skipping superuser creation: missing environment variables'))
            return

        # ▼ CHANGE THIS to your actual USERNAME_FIELD (e.g., 'email' or 'phone_number')
        username_field_name = 'username'  # <-- UPDATE THIS LINE

        # Use kwargs to dynamically build the lookup
        lookup_kwargs = {username_field_name: username}
        
        if not User.objects.filter(**lookup_kwargs).exists():
            # The create_superuser method may need email passed differently depending on your model
            User.objects.create_superuser(
                **{username_field_name: username},
                email=email,
                password=password
            )
            self.stdout.write(self.style.SUCCESS(f'Superuser {username} created successfully'))
        else:
            self.stdout.write(self.style.WARNING(f'Superuser {username} already exists'))