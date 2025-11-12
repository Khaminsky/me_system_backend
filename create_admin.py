#!/usr/bin/env python
"""
Script to create the default admin user if it doesn't exist.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from users.models import CustomUser

def create_admin():
    """Create admin user if it doesn't exist"""
    username = 'admin'
    email = 'admin@example.com'
    password = 'AdminPass@2025'
    
    if CustomUser.objects.filter(username=username).exists():
        print(f"✓ Admin user '{username}' already exists")
        user = CustomUser.objects.get(username=username)
        print(f"  - Email: {user.email}")
        print(f"  - Active: {user.is_active}")
        print(f"  - Role: {user.role}")
    else:
        print(f"Creating admin user '{username}'...")
        admin = CustomUser.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            role='admin'
        )
        print(f"✓ Admin user created successfully!")
        print(f"  - Username: {admin.username}")
        print(f"  - Email: {admin.email}")
        print(f"  - Password: {password}")

if __name__ == '__main__':
    create_admin()

