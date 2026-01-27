#!/usr/bin/env python3
"""
Test script to verify all security fixes
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint (unauthenticated)"""
    print("\n1. Testing health endpoint (should work without auth)...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
            print("   [PASS]")
            return True
        else:
            print(f"   [FAIL]: Expected 200, got {response.status_code}")
            return False
    except Exception as e:
        print(f"   [X] FAIL: {e}")
        return False


def test_incidents_without_auth():
    """Test that incidents endpoint requires authentication"""
    print("\n2. Testing incidents endpoint WITHOUT auth (should fail)...")
    try:
        response = requests.get(f"{BASE_URL}/api/incidents/")
        print(f"   Status: {response.status_code}")
        if response.status_code == 401 or response.status_code == 403:
            print(f"   Response: {response.json()}")
            print("   [OK] PASS - Authentication required as expected")
            return True
        else:
            print(f"   [X] FAIL: Expected 401/403, got {response.status_code}")
            print(f"   This means authentication is NOT enforced!")
            return False
    except Exception as e:
        print(f"   [X] FAIL: {e}")
        return False


def test_login():
    """Test login endpoint"""
    print("\n3. Testing login endpoint...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"   Token: {token[:30]}...")
            print("   [OK] PASS")
            return token
        else:
            print(f"   Response: {response.text}")
            print(f"   [X] FAIL: Login failed")
            return None
    except Exception as e:
        print(f"   [X] FAIL: {e}")
        return None


def test_incidents_with_auth(token):
    """Test incidents endpoint with authentication"""
    print("\n4. Testing incidents endpoint WITH auth (should work)...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/incidents/", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            incident_count = len(data.get("incidents", []))
            print(f"   Found {incident_count} incidents")
            print("   [OK] PASS - Authentication working")
            return data.get("incidents", [])
        else:
            print(f"   Response: {response.text}")
            print(f"   [X] FAIL: Expected 200, got {response.status_code}")
            return []
    except Exception as e:
        print(f"   [X] FAIL: {e}")
        return []


def test_incident_detail_with_auth(token, incident_id):
    """Test incident detail endpoint with authentication"""
    print(f"\n5. Testing incident detail endpoint for {incident_id}...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/incidents/{incident_id}",
            headers=headers
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Title: {data.get('summary', {}).get('title', 'N/A')}")
            print("   [OK] PASS")
            return True
        else:
            print(f"   Response: {response.text}")
            print(f"   [X] FAIL")
            return False
    except Exception as e:
        print(f"   [X] FAIL: {e}")
        return False


def test_path_traversal(token):
    """Test that path traversal is blocked"""
    print("\n6. Testing path traversal protection...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        # Try to access parent directory
        response = requests.get(
            f"{BASE_URL}/api/incidents/../../../etc/passwd",
            headers=headers
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 404 or response.status_code == 400:
            print("   [OK] PASS - Path traversal blocked")
            return True
        else:
            print(f"   [X] FAIL: Path traversal not properly blocked")
            return False
    except Exception as e:
        print(f"   [X] FAIL: {e}")
        return False


def test_status_endpoint_auth(token):
    """Test that status endpoints require authentication"""
    print("\n7. Testing status endpoint authentication...")
    try:
        # Try without auth first
        response = requests.get(f"{BASE_URL}/api/status/INC-2024-001")
        print(f"   Without auth - Status: {response.status_code}")

        if response.status_code in [401, 403]:
            print("   [OK] No auth rejected")

            # Now try with auth
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                f"{BASE_URL}/api/status/INC-2024-001",
                headers=headers
            )
            print(f"   With auth - Status: {response.status_code}")

            if response.status_code in [200, 404]:
                print("   [OK] PASS - Status endpoint authentication working")
                return True

        print(f"   [X] FAIL: Status endpoint authentication not working")
        return False
    except Exception as e:
        print(f"   [X] FAIL: {e}")
        return False


def main():
    print("=" * 60)
    print("WardenXT Security Fixes - Test Suite")
    print("=" * 60)

    results = []

    # Test 1: Health check
    results.append(("Health Check", test_health()))

    # Test 2: Authentication required
    results.append(("Auth Required", test_incidents_without_auth()))

    # Test 3: Login
    token = test_login()
    results.append(("Login", token is not None))

    if token:
        # Test 4: Authenticated access
        incidents = test_incidents_with_auth(token)
        results.append(("Authenticated Access", len(incidents) > 0))

        # Test 5: Incident detail
        if incidents:
            incident_id = incidents[0].get("incident_id", "INC-2024-001")
            results.append(("Incident Detail", test_incident_detail_with_auth(token, incident_id)))

        # Test 6: Path traversal protection
        results.append(("Path Traversal Block", test_path_traversal(token)))

        # Test 7: Status endpoint auth
        results.append(("Status Endpoint Auth", test_status_endpoint_auth(token)))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[OK] PASS" if result else "[X] FAIL"
        print(f"{status} - {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n[SUCCESS] All tests passed! Security fixes are working.")
        return 0
    else:
        print(f"\n[WARN]  {total - passed} test(s) failed. Please review.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
