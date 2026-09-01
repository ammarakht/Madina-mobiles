"""
Run this script once to create the admin user for the Madina Mobile Shop portal.
Usage: python create_admin.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sveston_watches.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

USERNAME = 'admin'
PASSWORD = 'sveston2024'
EMAIL = 'admin@sveston.pk'

user, created = User.objects.get_or_create(username=USERNAME, defaults={'email': EMAIL})
user.set_password(PASSWORD)
user.email = EMAIL
user.is_staff = True
user.is_superuser = True
user.is_active = True
user.save()

if created:
    print(f"[OK] Admin user '{USERNAME}' created successfully!")
else:
    print(f"[OK] Admin user '{USERNAME}' password and permissions updated successfully!")

print(f"   Username : {USERNAME}")
print(f"   Password : {PASSWORD}")

