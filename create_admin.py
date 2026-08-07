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

if User.objects.filter(username=USERNAME).exists():
    print(f"[OK] Admin user '{USERNAME}' already exists.")
else:
    User.objects.create_superuser(username=USERNAME, password=PASSWORD, email=EMAIL)
    print(f"[OK] Admin user created!")
    print(f"   Username : {USERNAME}")
    print(f"   Password : {PASSWORD}")
    print(f"   Portal   : http://127.0.0.1:8000/sv-cd6n-lugl/")
