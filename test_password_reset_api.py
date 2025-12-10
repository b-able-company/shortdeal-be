#!/usr/bin/env python
"""
Quick script to test password reset API endpoints
Usage: python test_password_reset_api.py
"""
import requests
import json

# Change this to your production URL
BASE_URL = "http://localhost:8000"  # or your Railway URL

def test_password_reset_request():
    """Test password reset request endpoint"""
    url = f"{BASE_URL}/api/v1/auth/password-reset/request/"

    # Test 1: Valid request with JSON
    print("Test 1: Valid JSON request")
    response = requests.post(
        url,
        json={"email": "test@example.com"},  # This sends proper JSON
        headers={"Content-Type": "application/json"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")

    # Test 2: Invalid email format
    print("Test 2: Invalid email format")
    response = requests.post(
        url,
        json={"email": "notanemail"},
        headers={"Content-Type": "application/json"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")

    # Test 3: What happens with form data (wrong way)
    print("Test 3: Form-encoded data (WRONG - should fail)")
    response = requests.post(
        url,
        data={"email": "test@example.com"},  # This sends form-encoded
        headers={"Content-Type": "application/json"}
    )
    print(f"Status: {response.status_code}")
    try:
        print(f"Response: {response.json()}\n")
    except:
        print(f"Response: {response.text}\n")

if __name__ == "__main__":
    print("Testing Password Reset API")
    print("=" * 50)
    test_password_reset_request()
