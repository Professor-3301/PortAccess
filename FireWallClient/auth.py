import requests
import json
import os

# ✅ API ENDPOINTS
BASE_URL = "http://127.0.0.1:333/api/"
SIGNUP_URL = f"{BASE_URL}signup/"
LOGIN_URL = f"{BASE_URL}login/"
SERVER_OWNER_DETAILS_URL = f"{BASE_URL}serverowner/details/"  # ✅ Fetch server owner details

TOKEN_FILE = "auth_token.json"  # ✅ Stores authentication token

def save_token(token):
    """Save the authentication token to a file."""
    with open(TOKEN_FILE, "w") as f:
        json.dump(token, f)

def load_token():
    """Load the authentication token from the file."""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    return None

def signup():
    """Signup a new server owner."""
    username = input("Enter username: ")
    email = input("Enter email: ")  # ✅ Email is now required
    password = input("Enter password: ")
    server_name = input("Enter server name: ")
    ip_address = input("Enter server IP address: ")
    aadhar_ssn = input("Enter Aadhar/SSN number: ")
    contact_number = input("Enter contact number: ")
    
    data = {
        "username": username,
        "email": email,
        "password": password,
        "name": server_name,
        "ip": ip_address,
        "aadhar_or_ssn": aadhar_ssn,
        "contact_no": contact_number,
        "role": "server_owner"
    }
    
    response = requests.post(SIGNUP_URL, json=data)
    if response.status_code == 201:
        print("[✅] Signup successful! Please login.")
    else:
        print(f"[❌] Signup failed: {response.json()}")

def login():
    """Login and retrieve an authentication token."""
    email = input("Enter email: ")  # ✅ Login with email instead of username
    password = input("Enter password: ")
    
    data = {
        "email": email,
        "password": password
    }
    
    response = requests.post(LOGIN_URL, json=data)
    if response.status_code == 200:
        token = response.json()  # ✅ Get token
        save_token(token)  # ✅ Store token for future API calls
        print("[✅] Login successful! Token saved.")
        # get_server_owner_details()  # ✅ Fetch server owner details after login
    else:
        print(f"[❌] Login failed: {response.json()}")

def get_auth_headers():
    """Return headers with stored JWT token."""
    token = load_token()
    if token:
        return {"Authorization": f"Bearer {token['token']}"}  # ✅ Correct token key
    else:
        print("[⚠️] Not authenticated. Please login.")
        return None

def get_server_owner_details():
    """Fetch server owner details using stored token."""
    headers = get_auth_headers()
    if headers:
        response = requests.get(SERVER_OWNER_DETAILS_URL, headers=headers)
        if response.status_code == 200:
            owner_details = response.json()
            print("\n[✅] Server Owner Details:")
            print(f"🔹 Server Name: {owner_details.get('server_name', 'N/A')}")
            print(f"🔹 IP Address: {owner_details.get('ip_address', 'N/A')}")
            print(f"🔹 Email: {owner_details.get('email', 'N/A')}")
            print(f"🔹 Contact Number: {owner_details.get('contact_number', 'N/A')}")
            print(f"🔹 Aadhar/SSN: {owner_details.get('aadhar_ssn', 'N/A')}")
            print(f"🔹 Password: {owner_details.get('password', '******')}")  # Masked for security
        else:
            print(f"[❌] Failed to fetch server owner details: {response.json()}")

if __name__ == "__main__":
    print("\n1. Signup")
    print("2. Login")
    choice = input("\nSelect an option: ")

    if choice == "1":
        signup()
    elif choice == "2":
        login()
    else:
        print("[❌] Invalid choice.")
