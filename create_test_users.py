#!/usr/bin/env python3
"""
Script to create test users for API testing
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_test_users():
    """Create test users for API testing"""
    
    # Create admin user if it doesn't exist
    admin_user, created = User.objects.get_or_create(
        username='admin@tavonga.com',
        defaults={
            'email': 'admin@tavonga.com',
            'first_name': 'Admin',
            'last_name': 'User',
            'is_admin': True,
            'is_staff': True,
            'is_superuser': True,
        }
    )
    
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print(f"✅ Created admin user: {admin_user.username}")
    else:
        print(f"ℹ️ Admin user already exists: {admin_user.username}")
    
    # Create carer user if it doesn't exist
    carer_user, created = User.objects.get_or_create(
        username='carer@tavonga.com',
        defaults={
            'email': 'carer@tavonga.com',
            'first_name': 'Carer',
            'last_name': 'User',
            'is_admin': False,
            'is_staff': False,
            'is_superuser': False,
        }
    )
    
    if created:
        carer_user.set_password('carer123')
        carer_user.save()
        print(f"✅ Created carer user: {carer_user.username}")
    else:
        print(f"ℹ️ Carer user already exists: {carer_user.username}")
    
    # Create another carer for testing
    carer2_user, created = User.objects.get_or_create(
        username='carer2@tavonga.com',
        defaults={
            'email': 'carer2@tavonga.com',
            'first_name': 'Carer',
            'last_name': 'Two',
            'is_admin': False,
            'is_staff': False,
            'is_superuser': False,
        }
    )
    
    if created:
        carer2_user.set_password('carer123')
        carer2_user.save()
        print(f"✅ Created carer2 user: {carer2_user.username}")
    else:
        print(f"ℹ️ Carer2 user already exists: {carer2_user.username}")

if __name__ == "__main__":
    print("👥 Creating Test Users")
    print("=" * 30)
    
    create_test_users()
    
    print("\n✅ Test users created successfully!") 