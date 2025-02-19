import os
import json
import requests
from auth import load_token, save_token

# API Endpoint (adjust based on your actual server URL)
BASE_URL = "http://127.0.0.1:8000/api/"
TOKEN_FILE = "auth_token.json"  # Location of saved token

def check_auth_token():
    """Check if a valid auth token exists."""
    token = load_token()
    if not token:
        print("[⚠️] No valid auth token found. Please log in first.")
        return False
    else:
        print("[✅] Token found.")
        return True

def issue_access_token():
    """Allow server owner to issue an access token to pentesters."""
    # Here you can implement the functionality to allow issuing tokens
    print("\n[🔑] Issue Access Token:")
    pentester_username = input("Enter Pentester's Username: ")
    # Assume the API allows issuing tokens to pentesters.
    # You can call a different endpoint here if needed.
    
    data = {"pentester_username": pentester_username}
    response = requests.post(f"{BASE_URL}issue-token/", json=data, headers=get_auth_headers())
    if response.status_code == 200:
        print(f"[✅] Token issued for {pentester_username}.")
    else:
        print(f"[❌] Failed to issue token: {response.json()}")

def get_auth_headers():
    """Return headers with stored JWT token."""
    token = load_token()
    if token:
        return {"Authorization": f"Bearer {token['access']}"}
    else:
        print("[⚠️] Not authenticated. Please login.")
        return None

def perform_task():
    """Perform tasks based on the server owner's role."""
    print("\n[🔧] Server Owner Actions:")
    print("1. Issue Access Token to Pentester")
    print("2. View Server Status")
    print("3. Logout")

    choice = input("Select an option: ")

    if choice == "1":
        issue_access_token()
    elif choice == "2":
        print("[⚙️] Server Status: Running smoothly.")
    elif choice == "3":
        logout()
    else:
        print("[❌] Invalid choice. Please try again.")

def logout():
    """Clear the auth token and log out."""
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)
        print("[✅] Logged out successfully.")
    else:
        print("[❌] No token found to log out.")

def login():
    """Prompt to log in if no token exists."""
    from auth import login
    print("[⚠️] No valid token found. Please log in.")
    login()

def main():
    """Main function to drive the interactive CLI interface."""
    if not check_auth_token():
        login()

    print("\n[🚀] Welcome to the PortAccess Server Owner Interface.")
    
    while True:
        perform_task()

if __name__ == "__main__":
    main()
