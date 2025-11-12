"""
Management command to create or update the admin user with proper role.
"""
from django.core.management.base import BaseCommand
from users.models import CustomUser


class Command(BaseCommand):
    help = 'Create or update admin user with proper role'

    def handle(self, *args, **options):
        username = 'admin'
        email = 'admin@example.com'
        password = 'AdminPass@2025'
        
        try:
            user = CustomUser.objects.get(username=username)
            self.stdout.write(f'Admin user "{username}" already exists')
            
            # Update role if needed
            if user.role != 'admin':
                user.role = 'admin'
                user.save()
                self.stdout.write(self.style.SUCCESS(f'✓ Updated role to "admin"'))
            else:
                self.stdout.write(f'  Role is already "admin"')
            
            # Ensure superuser status
            if not user.is_superuser or not user.is_staff:
                user.is_superuser = True
                user.is_staff = True
                user.save()
                self.stdout.write(self.style.SUCCESS(f'✓ Updated superuser status'))
            
            self.stdout.write(f'  Email: {user.email}')
            self.stdout.write(f'  Active: {user.is_active}')
            self.stdout.write(f'  Role: {user.role}')
            self.stdout.write(f'  Superuser: {user.is_superuser}')
            
        except CustomUser.DoesNotExist:
            self.stdout.write(f'Creating admin user "{username}"...')
            user = CustomUser.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                role='admin'
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Admin user created successfully!'))
            self.stdout.write(f'  Username: {user.username}')
            self.stdout.write(f'  Email: {user.email}')
            self.stdout.write(f'  Password: {password}')
            self.stdout.write(f'  Role: {user.role}')

