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

