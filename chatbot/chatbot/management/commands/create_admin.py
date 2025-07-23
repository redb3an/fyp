from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from chatbot.models import UserProfile

class Command(BaseCommand):
    help = 'Create admin superuser account'

    def handle(self, *args, **options):
        email = 'admin.test@gmail.com'
        password = '123'
        full_name = 'System Administrator'

        try:
            # Check if user already exists
            if User.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.WARNING(f'User {email} already exists.')
                )
                return

            # Create the superuser
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name='System',
                last_name='Administrator',
                is_staff=True,
                is_superuser=True,
                is_active=True
            )

            # Create or update the user profile
            UserProfile.objects.get_or_create(
                user=user,
                defaults={'full_name': full_name}
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created admin user: {email}\n'
                    f'Password: {password}\n'
                    f'Name: {full_name}'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating admin user: {str(e)}')
            ) 