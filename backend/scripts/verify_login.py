
import requests
import sys

BASE_URL = "http://localhost:8000/api"

def test_login():
    print(f"Testing login against {BASE_URL}...")
    
    login_payload = {
        "username": "admin",
        "password": "admin123" 
    }
    
    # Simulate frontend sending a bad token from previous session
    headers = {
        "Authorization": "Bearer invalid_token_garbage"
    }
    
    try:
        print("Sending login request with invalid Authorization header...")
        response = requests.post(f"{BASE_URL}/auth/login", json=login_payload, headers=headers)
        
        if response.status_code == 200:
            print("SUCCESS: Login successful!")
            print(f"Token: {response.json().get('access_token')[:20]}...")
        else:
            print(f"FAIL: Login failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"ERROR: Connection failed: {e}")

if __name__ == "__main__":
    test_login()
