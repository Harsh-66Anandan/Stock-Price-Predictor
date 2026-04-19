# debug_save.py
import requests

API_BASE = "http://localhost:8000"

payload = {
    "email": "debugtest@gmail.com",
    "display_name": "Debug User",
    "currency": "USD ($)",
    "two_fa_enabled": True,
    "biometric_login": False,
    "profile_image": None
}

print("Sending request to FastAPI...")
print(f"URL: {API_BASE}/users/save")
print(f"Payload: {payload}")

try:
    response = requests.post(f"{API_BASE}/users/save", json=payload, timeout=5)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.json()}")
except requests.exceptions.ConnectionError:
    print("❌ ERROR: FastAPI server is not running!")
    print("Fix: Run 'uvicorn main:app --reload' in Terminal 1 first")
except Exception as e:
    print(f"❌ ERROR: {e}")