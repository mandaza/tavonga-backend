#!/usr/bin/env python3
"""
Simple authentication test script
"""

import requests
import json

def test_auth():
    """Test the authentication endpoint"""
    
    # Test data
    auth_data = {
        "email": "admin@tavonga.com",
        "password": "admin123"
    }
    
    try:
        # Test login endpoint
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login/",
            json=auth_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Authentication successful!")
            print(f"Access token: {data.get('access', 'Not found')[:50]}...")
            return data.get('access')
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    print("🔐 Testing Authentication Endpoint")
    print("=" * 40)
    
    token = test_auth()
    
    if token:
        print("\n🎉 Authentication is working!")
    else:
        print("\n💥 Authentication failed!") 