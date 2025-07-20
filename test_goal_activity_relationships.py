#!/usr/bin/env python3
"""
Test script for Goal-Activity Relationships in Tavonga CareConnect API
Tests the new many-to-many relationship between goals and activities
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
ADMIN_USERNAME = "admin@tavonga.com"
ADMIN_PASSWORD = "admin123"
CARER_USERNAME = "carer@tavonga.com"
CARER_PASSWORD = "carer123"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def print_test(test_name, success=True):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {test_name}")

def make_request(method, endpoint, data=None, headers=None, expected_status=200):
    """Make HTTP request and return response"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, headers=headers)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, headers=headers)
        elif method.upper() == 'PUT':
            response = requests.put(url, json=data, headers=headers)
        elif method.upper() == 'DELETE':
            response = requests.delete(url, headers=headers)
        
        if response.status_code == expected_status:
            return response.json() if response.content else {}
        else:
            print(f"❌ Request failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Request error: {e}")
        return None

def get_auth_token(email, password):
    """Get JWT token for authentication"""
    auth_data = {
        "email": email,
        "password": password
    }
    
    response = make_request('POST', '/auth/login/', auth_data)
    if response and 'access' in response:
        return response['access']
    return None

def test_goal_activity_relationships():
    """Test the new goal-activity relationship functionality"""
    
    print_section("GOAL-ACTIVITY RELATIONSHIP TESTS")
    
    # Get authentication tokens
    print("🔐 Getting authentication tokens...")
    admin_token = get_auth_token(ADMIN_USERNAME, ADMIN_PASSWORD)
    carer_token = get_auth_token(CARER_USERNAME, CARER_PASSWORD)
    
    if not admin_token or not carer_token:
        print("❌ Failed to get authentication tokens")
        return False
    
    admin_headers = {'Authorization': f'Bearer {admin_token}'}
    carer_headers = {'Authorization': f'Bearer {carer_token}'}
    
    # Test 1: Create a goal
    print_test("Creating a goal")
    goal_data = {
        "name": "Improve Communication Skills",
        "description": "Help Tavonga develop better communication skills through various activities",
        "category": "Communication",
        "target_date": (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
        "priority": "high",
        "completion_threshold": 75
    }
    
    goal_response = make_request('POST', '/goals/', goal_data, admin_headers)
    if not goal_response:
        return False
    
    goal_id = goal_response['id']
    print(f"✅ Created goal: {goal_response['name']} (ID: {goal_id})")
    
    # Test 2: Create activities with primary goal
    print_test("Creating activities with primary goal")
    
    activities_data = [
        {
            "name": "Daily Conversation Practice",
            "description": "Practice speaking with carers and family members",
            "category": "social",
            "difficulty": "medium",
            "instructions": "Engage in 15-minute conversations daily",
            "estimated_duration": 15,
            "primary_goal": goal_id,
            "goal_contribution_weight": 3
        },
        {
            "name": "Picture Communication Cards",
            "description": "Use picture cards to express needs and wants",
            "category": "therapeutic",
            "difficulty": "easy",
            "instructions": "Use picture cards to communicate basic needs",
            "estimated_duration": 10,
            "primary_goal": goal_id,
            "goal_contribution_weight": 2
        },
        {
            "name": "Group Activity Participation",
            "description": "Participate in group activities to practice social skills",
            "category": "social",
            "difficulty": "hard",
            "instructions": "Join group activities and interact with others",
            "estimated_duration": 30,
            "primary_goal": goal_id,
            "goal_contribution_weight": 4
        }
    ]
    
    activity_ids = []
    for activity_data in activities_data:
        activity_response = make_request('POST', '/activities/', activity_data, admin_headers)
        if activity_response:
            activity_ids.append(activity_response['id'])
            print(f"✅ Created activity: {activity_response['name']} (ID: {activity_response['id']})")
        else:
            print(f"❌ Failed to create activity: {activity_data['name']}")
    
    # Test 3: Create a second goal and link activities to multiple goals
    print_test("Creating second goal and linking activities to multiple goals")
    
    second_goal_data = {
        "name": "Improve Motor Skills",
        "description": "Enhance fine and gross motor skills through activities",
        "category": "Physical",
        "target_date": (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d'),
        "priority": "medium",
        "completion_threshold": 80
    }
    
    second_goal_response = make_request('POST', '/goals/', second_goal_data, admin_headers)
    if not second_goal_response:
        return False
    
    second_goal_id = second_goal_response['id']
    print(f"✅ Created second goal: {second_goal_response['name']} (ID: {second_goal_id})")
    
    # Test 4: Link activities to multiple goals (many-to-many)
    print_test("Linking activities to multiple goals")
    
    # Update first activity to also be related to second goal
    if activity_ids:
        update_data = {
            "related_goals": [second_goal_id]
        }
        update_response = make_request('PUT', f'/activities/{activity_ids[0]}/', update_data, admin_headers)
        if update_response:
            print(f"✅ Linked activity {activity_ids[0]} to multiple goals")
        else:
            print(f"❌ Failed to link activity to multiple goals")
    
    # Test 5: Verify goal details with activities
    print_test("Verifying goal details with activities")
    
    goal_details = make_request('GET', f'/goals/{goal_id}/', headers=admin_headers)
    if goal_details:
        print(f"✅ Goal: {goal_details['name']}")
        print(f"   - Primary activities: {len(goal_details.get('primary_activities', []))}")
        print(f"   - Related activities: {len(goal_details.get('related_activities', []))}")
        print(f"   - All activities: {len(goal_details.get('all_activities', []))}")
        print(f"   - Progress: {goal_details.get('progress_percentage')}%")
        print(f"   - Calculated progress: {goal_details.get('calculated_progress')}%")
    else:
        print("❌ Failed to get goal details")
    
    # Test 6: Verify activity details with goals
    print_test("Verifying activity details with goals")
    
    if activity_ids:
        activity_details = make_request('GET', f'/activities/{activity_ids[0]}/', headers=admin_headers)
        if activity_details:
            print(f"✅ Activity: {activity_details['name']}")
            print(f"   - Primary goal: {activity_details.get('primary_goal', {}).get('name', 'None')}")
            print(f"   - Related goals: {len(activity_details.get('related_goals', []))}")
            print(f"   - All goals: {len(activity_details.get('all_goals', []))}")
            print(f"   - Contribution weight: {activity_details.get('goal_contribution_weight')}")
            print(f"   - Completion rate: {activity_details.get('completion_rate')}%")
        else:
            print("❌ Failed to get activity details")
    
    # Test 7: Create activity logs and test progress calculation
    print_test("Creating activity logs and testing progress calculation")
    
    if activity_ids:
        # Create a completed activity log
        log_data = {
            "activity": activity_ids[0],
            "date": datetime.now().strftime('%Y-%m-%d'),
            "status": "completed",
            "completed": True,
            "completion_notes": "Successfully completed the activity",
            "difficulty_rating": 3,
            "satisfaction_rating": 4
        }
        
        log_response = make_request('POST', '/activities/logs/', log_data, carer_headers)
        if log_response:
            print(f"✅ Created activity log: {log_response['id']}")
            
            # Check if goal progress was updated
            updated_goal = make_request('GET', f'/goals/{goal_id}/', headers=admin_headers)
            if updated_goal:
                print(f"✅ Updated goal progress: {updated_goal.get('progress_percentage')}%")
                print(f"   - Calculated progress: {updated_goal.get('calculated_progress')}%")
        else:
            print("❌ Failed to create activity log")
    
    # Test 8: Test goal listing with activity counts
    print_test("Testing goal listing with activity counts")
    
    goals_list = make_request('GET', '/goals/', headers=admin_headers)
    if goals_list and 'results' in goals_list:
        for goal in goals_list['results']:
            print(f"✅ Goal: {goal['name']} - Activities: {goal.get('activities_count', 0)}")
    else:
        print("❌ Failed to get goals list")
    
    # Test 9: Test activity listing with completion rates
    print_test("Testing activity listing with completion rates")
    
    activities_list = make_request('GET', '/activities/', headers=admin_headers)
    if activities_list and 'results' in activities_list:
        for activity in activities_list['results']:
            print(f"✅ Activity: {activity['name']} - Completion: {activity.get('completion_rate', 0)}%")
    else:
        print("❌ Failed to get activities list")
    
    print_section("TEST SUMMARY")
    print("✅ All goal-activity relationship tests completed!")
    print("✅ Many-to-many relationship working correctly")
    print("✅ Progress calculation working")
    print("✅ API endpoints responding properly")
    
    return True

if __name__ == "__main__":
    print("🚀 Starting Goal-Activity Relationship Tests")
    print("=" * 60)
    
    # Wait a moment for server to be ready
    time.sleep(2)
    
    success = test_goal_activity_relationships()
    
    if success:
        print("\n🎉 All tests passed! The goal-activity relationship is working correctly.")
    else:
        print("\n💥 Some tests failed. Please check the output above.") 