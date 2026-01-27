
import requests

def test_cors():
    url = "http://localhost:8000/api/auth/login"
    origin = "http://localhost:3000"
    
    print(f"Testing CORS for {url} with Origin: {origin}")
    
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type"
    }
    
    try:
        response = requests.options(url, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print("Headers:")
        for k, v in response.headers.items():
            if "access-control" in k.lower():
                print(f"  {k}: {v}")
                
        if response.status_code == 200 and 'access-control-allow-origin' in response.headers:
             print("SUCCESS: CORS Preflight looks accepted.")
        else:
             print("FAIL: CORS Preflight failed or missing headers.")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_cors()
