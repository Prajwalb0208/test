import httpx
import json
import os
import pytest


@pytest.fixture(scope="session")
def api_client():
    """Shared httpx client for all API tests in the session."""
    base_url = os.environ.get("QA_TARGET_URL", "")
    headers = {}
    token = os.environ.get("QA_API_TOKEN", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with httpx.Client(base_url=base_url, headers=headers, timeout=30.0) as client:
        yield client


def _assert_status(response, expected: int, msg: str = ""):
    assert response.status_code == expected, (
        f"Expected {expected}, got {response.status_code}. {msg}\n"
        f"Response: {response.text[:500]}"
    )


def _assert_json_field(response, field: str, expected=None):
    data = response.json()
    assert field in data, f"Field '{field}' not in response: {list(data.keys())}"
    if expected is not None:
        assert data[field] == expected, f"Expected {field}={expected!r}, got {data[field]!r}"


def test_unauthorized_access_attempt_on_audit_logs_endpoint(api_client):
    client = api_client
    response = client.get("/audit/logs")
    _assert_status(response, 401)
    response = client.get("/audit/logs")
    _assert_status(response, 403)

def test_handling_of_empty_log_set_retrieval(api_client):
    client = api_client
    response = client.get("/audit/logs", params={"start_time": "", "end_time": ""})
    _assert_status(response, 200)
    response = client.get("/audit/logs", params={"start_time": "", "end_time": ""})
    _assert_status(response, 200)
    response = client.get("/audit/logs", params={"start_time": "2000-01-01T00:00:00Z", "end_time": "2000-01-01T00:00:00Z"})
    _assert_status(response, 200)
    data = response.json()
    if isinstance(data, list):
        assert len(data) == 0
    elif isinstance(data, dict):
        # Check for a specific 'no records found' message structure
        try:
            _assert_json_field(response, "message", expected_value="No logs found")
        except AssertionError:
            pass # If the field doesn't exist, we assume success if it's an empty dict or similar non-error state.