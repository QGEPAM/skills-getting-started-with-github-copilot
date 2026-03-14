import copy

from fastapi.testclient import TestClient

from src.app import app, activities as activities_storage

client = TestClient(app)

INITIAL_ACTIVITIES = copy.deepcopy(activities_storage)


def setup_function():
    # Reset in-memory activity state before each test to avoid cross-test pollution
    activities_storage.clear()
    activities_storage.update(copy.deepcopy(INITIAL_ACTIVITIES))


def test_get_activities():
    response = client.get("/activities")
    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert "Programming Class" in payload


def test_signup_new_participant():
    response = client.post("/activities/Chess Club/signup?email=test@example.com")
    assert response.status_code == 200
    assert response.json()["message"] == "Signed up test@example.com for Chess Club"

    # Confirm in-memory state update
    assert "test@example.com" in activities_storage["Chess Club"]["participants"]


def test_signup_duplicate_participant_returns_400():
    client.post("/activities/Chess Club/signup?email=test-dup@example.com")
    response = client.post("/activities/Chess Club/signup?email=test-dup@example.com")

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up"


def test_signup_nonexistent_activity_returns_404():
    response = client.post("/activities/Unknown/signup?email=someone@example.com")
    assert response.status_code == 404


def test_remove_participant_success():
    # Start from seeded participant
    response = client.delete("/activities/Chess Club/participants?email=michael@mergington.edu")
    assert response.status_code == 200
    assert response.json()["message"] == "Removed michael@mergington.edu from Chess Club"

    assert "michael@mergington.edu" not in activities_storage["Chess Club"]["participants"]


def test_remove_participant_not_found_returns_404():
    response = client.delete("/activities/Chess Club/participants?email=missing@example.com")
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"


def test_signup_full_activity_returns_400():
    # Make Chess Club full sleep test
    activities_storage["Chess Club"]["participants"] = [f"user{i}@mergington.edu" for i in range(12)]
    response = client.post("/activities/Chess Club/signup?email=full@example.com")
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"
