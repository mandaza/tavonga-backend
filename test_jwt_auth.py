#!/usr/bin/env python3
"""
Test JWT Authentication with Email
"""

import requests
import json

def test_jwt_auth():
    """Test the JWT authentication endpoint with email"""
    
    # Test data
    auth_data = {
        "email": "admin@tavonga.com",
        "password": "admin123"
    }
    
    try:
        # Test JWT login endpoint
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login/",
            json=auth_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ JWT Authentication successful!")
            print(f"Access token: {data.get('access', 'Not found')[:50]}...")
            print(f"Refresh token: {data.get('refresh', 'Not found')[:50]}...")
            return data.get('access')
        else:
            print(f"❌ JWT Authentication failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Raw response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_protected_endpoint(token):
    """Test a protected endpoint with the JWT token"""
    if not token:
        return
        
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            "http://localhost:8000/api/v1/users/profile/",
            headers=headers
        )
        
        print(f"\n--- Testing Protected Endpoint ---")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Protected endpoint access successful!")
            print(f"User: {data.get('email', 'Unknown')}")
        else:
            print(f"❌ Protected endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing protected endpoint: {e}")

if __name__ == "__main__":
    print("🔐 Testing JWT Authentication with Email")
    print("=" * 50)
    
    token = test_jwt_auth()
    
    if token:
        print("\n🎉 JWT Authentication is working!")
        test_protected_endpoint(token)
    else:
        print("\n💥 JWT Authentication failed!") 