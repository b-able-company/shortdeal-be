#!/usr/bin/env python
"""
Script to create a superuser from environment variables.
Usage: python create_superuser.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shortdeal.settings.production')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@shortdeal.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if not password:
    print("ERROR: DJANGO_SUPERUSER_PASSWORD environment variable is required")
    exit(1)

if User.objects.filter(username=username).exists():
    print(f"Superuser '{username}' already exists")
else:
    User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )
    print(f"Superuser '{username}' created successfully")
