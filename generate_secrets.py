#!/usr/bin/env python3
"""
GitHub Secrets Generator for ME System CI/CD

This script helps you generate secure values for GitHub secrets.
Run this script and copy the generated values to your GitHub repository secrets.

Usage:
    python generate_secrets.py
"""

import secrets
import string
from django.core.management.utils import get_random_secret_key


def generate_django_secret_key():
    """Generate a secure Django SECRET_KEY"""
    return get_random_secret_key()


def generate_db_password(length=32):
    """Generate a secure database password"""
    # Use URL-safe characters (no special chars that might cause issues)
    return secrets.token_urlsafe(length)


def generate_strong_password(length=24):
    """Generate a strong password with mixed characters"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def print_separator():
    """Print a visual separator"""
    print("\n" + "=" * 80 + "\n")


def main():
    print("=" * 80)
    print("🔐 ME System - GitHub Secrets Generator")
    print("=" * 80)
    print("\nThis script will generate secure values for your GitHub secrets.")
    print("Copy these values to: GitHub → Settings → Secrets and variables → Actions")
    
    print_separator()
    
    # Django SECRET_KEY
    print("📌 DJANGO SECRET_KEY")
    print("-" * 80)
    django_secret = generate_django_secret_key()
    print(f"Value: {django_secret}")
    print("\nGitHub Secret Name: SECRET_KEY")
    print("⚠️  Keep this secret! Never commit to Git!")
    
    print_separator()
    
    # Database Password
    print("📌 DATABASE PASSWORD")
    print("-" * 80)
    db_password = generate_db_password(32)
    print(f"Value: {db_password}")
    print("\nGitHub Secret Name: DB_PASSWORD")
    print("💾 Save this password securely! You'll need it for database access.")
    
    print_separator()
    
    # Alternative strong password
    print("📌 ALTERNATIVE DATABASE PASSWORD (with special characters)")
    print("-" * 80)
    strong_password = generate_strong_password(24)
    print(f"Value: {strong_password}")
    print("\nUse this if you prefer passwords with special characters.")
    
    print_separator()
    
    # Summary
    print("📋 SUMMARY - Copy these to GitHub Secrets:")
    print("-" * 80)
    print(f"\nSECRET_KEY={django_secret}")
    print(f"DB_PASSWORD={db_password}")
    
    print_separator()
    
    # Other secrets reminder
    print("📝 OTHER REQUIRED SECRETS (set manually):")
    print("-" * 80)
    print("""
Server Access:
  DROPLET_IP=<your-droplet-ip>          # e.g., 165.227.81.39
  DROPLET_USER=root                      # or your SSH username
  SSH_PRIVATE_KEY=<your-private-key>     # Full private key content

Django Config:
  DEBUG=False                            # Always False in production
  ALLOWED_HOSTS=<domain,ip>              # e.g., example.com,165.227.81.39

Database Config:
  DB_NAME=me_system_db                   # Database name
  DB_USER=postgres                       # Database username
    """)
    
    print_separator()
    
    # Instructions
    print("🚀 NEXT STEPS:")
    print("-" * 80)
    print("""
1. Go to your GitHub repository
2. Click Settings → Secrets and variables → Actions
3. Click 'New repository secret'
4. Add each secret one by one:
   - Name: SECRET_KEY
   - Value: (copy from above)
   - Click 'Add secret'
5. Repeat for all 9 secrets
6. See GITHUB_SECRETS_SETUP.md for detailed instructions

📚 Documentation:
   - GITHUB_SECRETS_SETUP.md - Complete setup guide
   - README_CICD.md - CI/CD overview
   - DEPLOYMENT_QUICK_START.md - Quick deployment guide
    """)
    
    print("=" * 80)
    print("✅ Secrets generated successfully!")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except ImportError as e:
        if "django" in str(e).lower():
            print("\n⚠️  Django not found. Using alternative method...\n")
            print("=" * 80)
            print("🔐 ME System - GitHub Secrets Generator (Standalone)")
            print("=" * 80)
            
            # Alternative SECRET_KEY generation without Django
            print("\n📌 DJANGO SECRET_KEY")
            print("-" * 80)
            # Generate 50 random characters
            chars = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
            django_secret = ''.join(secrets.choice(chars) for _ in range(50))
            print(f"Value: django-insecure-{django_secret}")
            print("\nGitHub Secret Name: SECRET_KEY")
            
            print("\n" + "=" * 80 + "\n")
            
            print("📌 DATABASE PASSWORD")
            print("-" * 80)
            db_password = secrets.token_urlsafe(32)
            print(f"Value: {db_password}")
            print("\nGitHub Secret Name: DB_PASSWORD")
            
            print("\n" + "=" * 80)
            print("✅ Secrets generated successfully!")
            print("=" * 80)
        else:
            raise

