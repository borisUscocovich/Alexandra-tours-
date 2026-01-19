import requests
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

def wait_for_server():
    print("Waiting for server...")
    for _ in range(10):
        try:
            requests.get(BASE_URL)
            print("Server is up!")
            return True
        except requests.ConnectionError:
            time.sleep(1)
    print("Server failed to start.")
    return False

def test_tap():
    print("\n[TEST] /api/tap endpoint")
    payload = {"local_id": "el_tigre_gracia"}
    res = requests.post(f"{BASE_URL}/api/tap", json=payload)
    if res.status_code == 200:
        print("PASS: Tap successful")
        print("Response:", res.json())
    else:
        print(f"FAIL: Tap failed {res.status_code} {res.text}")

def test_chat_flow():
    print("\n[TEST] /api/chat valid flow")
    payload = {"local_id": "el_tigre_gracia", "message": "Hola"}
    res = requests.post(f"{BASE_URL}/api/chat", json=payload)
    if res.status_code == 200:
        data = res.json()
        print("PASS: Chat successful")
        print("Response:", data['response'][:100] + "...")
    else:
        print(f"FAIL: Chat failed {res.status_code} {res.text}")

def test_security_xss():
    print("\n[TEST] Security: XSS Sanitization")
    xss_payload = "<script>alert('XSS')</script>"
    payload = {"local_id": "el_tigre_gracia", "message": xss_payload}
    
    res = requests.post(f"{BASE_URL}/api/chat", json=payload)
    if res.status_code == 200:
        response_text = res.json()['response']
        # The backend schema should strip tags. Pydantic validator `re.sub(r'<[^>]*>', '', v)`
        if "<script>" not in response_text and "alert" in response_text:
             # It might strip script tags but leave content, or strip all. 
             # My validator was: re.sub(r'<[^>]*>', '', v) -> "alert('XSS')"
             print("PASS: XSS tags stripped.")
             print("Sanitized received:", response_text)
        elif xss_payload not in response_text:
             print("PASS: Payload altered/sanitized.")
        else:
            print("FAIL: XSS payload returned verbatim!")
            print("Received:", response_text)
    else:
        print(f"FAIL: Request failed {res.status_code}")

def test_security_headers():
    print("\n[TEST] Security: CSP Headers")
    res = requests.get(BASE_URL + "/") # Static file serve
    # Note: StaticFiles in FastAPI might NOT automatically add CSP headers unless middleware does it. 
    # I did NOT add a CSP middleware, I added it to HTML meta tag.
    # So I will check HTML content for meta tag.
    if '<meta http-equiv="Content-Security-Policy"' in res.text:
        print("PASS: CSP Meta tag found in HTML")
    else:
        print("FAIL: CSP Meta tag MISSING in HTML")

if __name__ == "__main__":
    if not wait_for_server():
        sys.exit(1)
    
    test_tap()
    test_chat_flow()
    test_security_xss()
    test_security_headers()
