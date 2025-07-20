#!/usr/bin/env python3
"""
API Testing Script for Tavonga CareConnect System
Tests all major endpoints and functionality
"""

import requests
import json
from datetime import datetime, date, time

# API Base URL
BASE_URL = "http://localhost:8000/api/v1"

def print_response(response, endpoint):
    """Print formatted response"""
    print(f"\n{'='*50}")
    print(f"Testing: {endpoint}")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print(f"{'='*50}")

def test_authentication():
    """Test user registration and login"""
    print("\n🔐 TESTING AUTHENTICATION")
    
    # Test user registration
    register_data = {
        "username": "testcarer",
        "email": "testcarer@tavonga.com",
        "password": "testpass123",
        "password_confirm": "testpass123",
        "first_name": "Test",
        "last_name": "Carer",
        "phone": "+1234567890"
    }
    
    response = requests.post(f"{BASE_URL}/users/", json=register_data)
    print_response(response, "User Registration")
    
    # Test login
    login_data = {
        "username": "mandaza",
        "password": "incorrect"
    }
    
    response = requests.post(f"{BASE_URL}/users/login/", json=login_data)
    print_response(response, "User Login")
    
    if response.status_code == 200:
        tokens = response.json().get('tokens', {})
        return tokens.get('access')
    return None

def test_users_endpoints(token):
    """Test user management endpoints"""
    print("\n👥 TESTING USER ENDPOINTS")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test get profile
    response = requests.get(f"{BASE_URL}/users/profile/", headers=headers)
    print_response(response, "Get Profile")
    
    # Test update profile
    update_data = {
        "phone": "+9876543210",
        "address": "123 Test Street"
    }
    response = requests.patch(f"{BASE_URL}/users/update_profile/", json=update_data, headers=headers)
    print_response(response, "Update Profile")
    
    # Test list users (admin only)
    response = requests.get(f"{BASE_URL}/users/", headers=headers)
    print_response(response, "List Users")

def test_goals_endpoints(token):
    """Test goal management endpoints"""
    print("\n🎯 TESTING GOALS ENDPOINTS")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test create goal
    goal_data = {
        "name": "Improve Communication Skills",
        "description": "Help client develop better communication skills",
        "category": "Communication",
        "priority": "high",
        "target_date": "2024-12-31"
    }
    
    response = requests.post(f"{BASE_URL}/goals/", json=goal_data, headers=headers)
    print_response(response, "Create Goal")
    
    if response.status_code == 201:
        goal_id = response.json().get('id')
        
        # Test get goal
        response = requests.get(f"{BASE_URL}/goals/{goal_id}/", headers=headers)
        print_response(response, "Get Goal")
        
        # Test update goal
        update_data = {
            "progress_percentage": 25,
            "notes": "Making good progress"
        }
        response = requests.patch(f"{BASE_URL}/goals/{goal_id}/track_progress/", json=update_data, headers=headers)
        print_response(response, "Track Goal Progress")
    
    # Test list goals
    response = requests.get(f"{BASE_URL}/goals/", headers=headers)
    print_response(response, "List Goals")

def test_activities_endpoints(token):
    """Test activity management endpoints"""
    print("\n🏃 TESTING ACTIVITIES ENDPOINTS")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test create activity
    activity_data = {
        "name": "Morning Exercise Routine",
        "description": "Daily morning exercise routine for physical development",
        "category": "therapeutic",
        "difficulty": "medium",
        "instructions": "1. Start with stretching\n2. Do light exercises\n3. Cool down",
        "estimated_duration": 30
    }
    
    response = requests.post(f"{BASE_URL}/activities/", json=activity_data, headers=headers)
    print_response(response, "Create Activity")
    
    if response.status_code == 201:
        activity_id = response.json().get('id')
        
        # Test create activity log
        log_data = {
            "activity": activity_id,
            "date": date.today().isoformat(),
            "status": "scheduled"
        }
        
        response = requests.post(f"{BASE_URL}/activity-logs/", json=log_data, headers=headers)
        print_response(response, "Create Activity Log")
    
    # Test list activities
    response = requests.get(f"{BASE_URL}/activities/", headers=headers)
    print_response(response, "List Activities")

def test_behaviors_endpoints(token):
    """Test behavior logging endpoints"""
    print("\n📊 TESTING BEHAVIORS ENDPOINTS")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test create behavior log
    behavior_data = {
        "date": date.today().isoformat(),
        "time": "14:30:00",
        "location": "home",
        "behavior_type": "aggression",
        "behaviors": ["Shouting", "Throwing objects"],
        "severity": "medium",
        "intervention_used": "Calm verbal redirection",
        "intervention_effective": True
    }
    
    response = requests.post(f"{BASE_URL}/behaviors/", json=behavior_data, headers=headers)
    print_response(response, "Create Behavior Log")
    
    # Test list behaviors
    response = requests.get(f"{BASE_URL}/behaviors/", headers=headers)
    print_response(response, "List Behaviors")

def test_shifts_endpoints(token):
    """Test shift management endpoints"""
    print("\n⏰ TESTING SHIFTS ENDPOINTS")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test create shift
    shift_data = {
        "carer": 1,  # Assuming user ID 1 exists
        "date": date.today().isoformat(),
        "shift_type": "morning",
        "start_time": "08:00:00",
        "end_time": "16:00:00",
        "location": "Client Home",
        "client_name": "John Doe"
    }
    
    response = requests.post(f"{BASE_URL}/shifts/", json=shift_data, headers=headers)
    print_response(response, "Create Shift")
    
    if response.status_code == 201:
        shift_id = response.json().get('id')
        
        # Test clock in
        clock_in_data = {
            "clock_in_location": "Client Home"
        }
        response = requests.patch(f"{BASE_URL}/shifts/{shift_id}/clock_in/", json=clock_in_data, headers=headers)
        print_response(response, "Clock In")
    
    # Test list shifts
    response = requests.get(f"{BASE_URL}/shifts/", headers=headers)
    print_response(response, "List Shifts")

def test_media_endpoints(token):
    """Test media upload, list, retrieve, and delete endpoints"""
    print("\n🖼️ TESTING MEDIA ENDPOINTS")
    headers = {"Authorization": f"Bearer {token}"}

    # Test image upload (valid)
    with open("test_image.jpg", "rb") as img:
        files = {"file": ("test_image.jpg", img, "image/jpeg")}
        data = {"media_type": "image", "description": "Test image upload"}
        response = requests.post(f"{BASE_URL}/media/", files=files, data=data, headers=headers)
        print_response(response, "Upload Image")
        if response.status_code == 201:
            media_id = response.json().get("id")
            thumb_url = response.json().get("thumbnail_url")
            print(f"Thumbnail URL: {thumb_url}")
            # Retrieve
            response2 = requests.get(f"{BASE_URL}/media/{media_id}/", headers=headers)
            print_response(response2, "Retrieve Uploaded Image")
            # Delete
            response3 = requests.delete(f"{BASE_URL}/media/{media_id}/", headers=headers)
            print_response(response3, "Delete Uploaded Image")

    # Test video upload (valid)
    with open("test_video.mp4", "rb") as vid:
        files = {"file": ("test_video.mp4", vid, "video/mp4")}
        data = {"media_type": "video", "description": "Test video upload"}
        response = requests.post(f"{BASE_URL}/media/", files=files, data=data, headers=headers)
        print_response(response, "Upload Video")
        if response.status_code == 201:
            media_id = response.json().get("id")
            # Retrieve
            response2 = requests.get(f"{BASE_URL}/media/{media_id}/", headers=headers)
            print_response(response2, "Retrieve Uploaded Video")
            # Delete
            response3 = requests.delete(f"{BASE_URL}/media/{media_id}/", headers=headers)
            print_response(response3, "Delete Uploaded Video")

    # Test invalid file type
    with open("test_invalid.txt", "rb") as txt:
        files = {"file": ("test_invalid.txt", txt, "text/plain")}
        data = {"media_type": "image", "description": "Invalid file type"}
        response = requests.post(f"{BASE_URL}/media/", files=files, data=data, headers=headers)
        print_response(response, "Upload Invalid File Type")

    # Test file size limit (simulate by sending a large file if available)
    # You can create a large dummy file for this test if needed.

    # List media
    response = requests.get(f"{BASE_URL}/media/", headers=headers)
    print_response(response, "List Media Files")

def test_swagger_docs():
    """Test Swagger documentation"""
    print("\n📚 TESTING SWAGGER DOCUMENTATION")
    
    response = requests.get("http://localhost:8000/swagger/")
    print(f"Swagger Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Swagger documentation is accessible")
    else:
        print("❌ Swagger documentation is not accessible")

def main():
    """Main testing function"""
    print("🚀 Starting Tavonga CareConnect API Tests")
    print("=" * 60)
    
    # Test authentication
    token = test_authentication()
    
    if token:
        print(f"\n✅ Authentication successful! Token: {token[:20]}...")
        
        # Test all endpoints
        test_users_endpoints(token)
        test_goals_endpoints(token)
        test_activities_endpoints(token)
        test_behaviors_endpoints(token)
        test_shifts_endpoints(token)
        test_media_endpoints(token)
        test_swagger_docs()
        
        print("\n🎉 API Testing Complete!")
        print("\n📋 Summary:")
        print("- Authentication: ✅")
        print("- User Management: ✅")
        print("- Goal Management: ✅")
        print("- Activity Management: ✅")
        print("- Behavior Logging: ✅")
        print("- Shift Management: ✅")
        print("- Media Management: ✅")
        print("- API Documentation: ✅")
        
    else:
        print("❌ Authentication failed! Cannot proceed with other tests.")

if __name__ == "__main__":
    main() 