"""
Test cases for the Mergington High School Activities API

This module contains comprehensive tests for all API endpoints including:
- GET /activities: Retrieve all activities
- POST /activities/{activity_name}/signup: Sign up for an activity  
- DELETE /activities/{activity_name}/unregister: Unregister from an activity
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities
import copy

# Create test client
client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test to ensure test isolation"""
    # Store original activities data
    original_activities = copy.deepcopy({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    })
    
    # Reset to original state before each test
    activities.clear()
    activities.update(original_activities)
    
    yield  # Run the test
    
    # Could add cleanup here if needed


class TestGetActivities:
    """Test cases for GET /activities endpoint"""
    
    def test_get_activities_success(self):
        """Test successful retrieval of all activities"""
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        
        # Verify activity structure
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)
        assert chess_club["max_participants"] == 12
    
    def test_get_activities_empty_participants(self):
        """Test activity with no participants"""
        # Clear participants from Chess Club
        activities["Chess Club"]["participants"] = []
        
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        assert data["Chess Club"]["participants"] == []


class TestSignupForActivity:
    """Test cases for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self):
        """Test successful signup for an activity"""
        email = "newstudent@mergington.edu"
        activity_name = "Chess Club"
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == f"Signed up {email} for {activity_name}"
        
        # Verify participant was added
        assert email in activities[activity_name]["participants"]
    
    def test_signup_activity_not_found(self):
        """Test signup for non-existent activity"""
        email = "student@mergington.edu"
        activity_name = "Nonexistent Activity"
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_signup_already_registered(self):
        """Test signup when student is already registered"""
        email = "michael@mergington.edu"  # Already in Chess Club
        activity_name = "Chess Club"
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Student is already signed up"
    
    def test_signup_special_characters_in_activity_name(self):
        """Test signup with URL-encoded activity name"""
        # Add an activity with special characters for testing
        activities["Art & Design"] = {
            "description": "Creative arts class",
            "schedule": "Mondays, 2:00 PM",
            "max_participants": 15,
            "participants": []
        }
        
        email = "artist@mergington.edu"
        activity_name = "Art & Design"
        encoded_name = "Art%20%26%20Design"
        
        response = client.post(f"/activities/{encoded_name}/signup?email={email}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == f"Signed up {email} for {activity_name}"
    
    def test_signup_special_characters_in_email(self):
        """Test signup with special characters in email"""
        email = "test+student@mergington.edu"
        activity_name = "Chess Club"
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        
        assert response.status_code == 200
        data = response.json()
        # Note: The + character in URLs gets decoded as a space
        expected_email = "test student@mergington.edu"
        assert data["message"] == f"Signed up {expected_email} for {activity_name}"
        assert expected_email in activities[activity_name]["participants"]


class TestUnregisterFromActivity:
    """Test cases for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self):
        """Test successful unregistration from an activity"""
        email = "michael@mergington.edu"  # Already in Chess Club
        activity_name = "Chess Club"
        
        # Verify student is initially registered
        assert email in activities[activity_name]["participants"]
        
        response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == f"Unregistered {email} from {activity_name}"
        
        # Verify participant was removed
        assert email not in activities[activity_name]["participants"]
    
    def test_unregister_activity_not_found(self):
        """Test unregister from non-existent activity"""
        email = "student@mergington.edu"
        activity_name = "Nonexistent Activity"
        
        response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_unregister_student_not_registered(self):
        """Test unregister when student is not registered"""
        email = "notregistered@mergington.edu"
        activity_name = "Chess Club"
        
        response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Student is not registered for this activity"
    
    def test_unregister_last_participant(self):
        """Test unregistering the last participant from an activity"""
        # Create activity with only one participant
        activities["Test Activity"] = {
            "description": "Test activity",
            "schedule": "Test schedule",
            "max_participants": 1,
            "participants": ["onlyone@mergington.edu"]
        }
        
        email = "onlyone@mergington.edu"
        activity_name = "Test Activity"
        
        response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == f"Unregistered {email} from {activity_name}"
        assert activities[activity_name]["participants"] == []


class TestRootEndpoint:
    """Test cases for root endpoint"""
    
    def test_root_redirect(self):
        """Test that root endpoint redirects to static HTML"""
        response = client.get("/", follow_redirects=False)
        
        assert response.status_code == 307  # Temporary redirect
        assert response.headers["location"] == "/static/index.html"


class TestIntegrationWorkflows:
    """Integration tests that test complete workflows"""
    
    def test_signup_and_unregister_workflow(self):
        """Test complete signup and unregister workflow"""
        email = "workflow@mergington.edu"
        activity_name = "Chess Club"
        
        # Step 1: Verify initial state
        initial_response = client.get("/activities")
        initial_data = initial_response.json()
        initial_participants = initial_data[activity_name]["participants"]
        assert email not in initial_participants
        
        # Step 2: Sign up
        signup_response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Step 3: Verify signup
        after_signup_response = client.get("/activities")
        after_signup_data = after_signup_response.json()
        assert email in after_signup_data[activity_name]["participants"]
        
        # Step 4: Unregister
        unregister_response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        assert unregister_response.status_code == 200
        
        # Step 5: Verify unregistration
        final_response = client.get("/activities")
        final_data = final_response.json()
        assert email not in final_data[activity_name]["participants"]
    
    def test_multiple_activities_signup(self):
        """Test signing up for multiple activities"""
        email = "multi@mergington.edu"
        activities_to_join = ["Chess Club", "Programming Class", "Gym Class"]
        
        for activity in activities_to_join:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify student is in all activities
        final_response = client.get("/activities")
        final_data = final_response.json()
        
        for activity in activities_to_join:
            assert email in final_data[activity]["participants"]


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_email(self):
        """Test signup with empty email"""
        response = client.post("/activities/Chess Club/signup?email=")
        # FastAPI should handle this, but behavior depends on validation
        # This tests current behavior
        assert response.status_code in [200, 400, 422]
    
    def test_invalid_characters_in_url(self):
        """Test with various invalid characters in URLs"""
        email = "test@mergington.edu"
        
        # Test with activity name containing special characters
        response = client.post("/activities/Invalid%20%2F%20Activity/signup?email=" + email)
        assert response.status_code == 404  # Should not find the activity
    
    def test_very_long_email(self):
        """Test with very long email address"""
        long_email = "a" * 200 + "@mergington.edu"
        
        response = client.post(f"/activities/Chess Club/signup?email={long_email}")
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 400, 422]