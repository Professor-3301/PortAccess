import os
import json
import requests
from auth import load_token, save_token, login

# API Endpoint (adjust based on your actual server URL)
BASE_URL = "http://127.0.0.1:333/api/"
TOKEN_FILE = "auth_token.json"  # Location of saved token

def check_auth_token():
    """Check if a valid auth token exists."""
    token = load_token()
    if not token:
        print("[⚠️] No valid auth token found. Please log in first.")
        return False
    print("[✅] Token found.")
    return True

def get_auth_headers():
    """Return headers with stored JWT token."""
    token = load_token()
    if token:
        return {"Authorization": f"Bearer {token['token']}"}
    print("[⚠️] Not authenticated. Please login.")
    return None

def view_access_requests():
    """View access requests submitted by pentesters."""
    print("\n[📄] Viewing Access Requests:")
    server_id = input("Enter Server ID: ")

    headers = get_auth_headers()
    if not headers:
        return

    response = requests.get(f"{BASE_URL}server/{server_id}/access-requests/", headers=headers)

    if response.status_code == 200:
        requests_data = response.json()
        if not requests_data:
            print("[ℹ️] No pending access requests.")
            return

        for request in requests_data:
            pentester = request['pentester']
            print(f"\n[🆔] Request ID: {request['request_id']}")
            print(f"🔹 Pentester Username: {pentester['username']}")
            print(f"🆔 Aadhar Number: {pentester['aadhar_or_ssn']}")
            print(f"🎓 Certifications: {pentester.get('certifications', 'N/A')}")
            print(f"📌 Status: {request['status']}")
            print(f"📅 Requested At: {request['requested_at']}")
    else:
        print(f"[❌] Failed to fetch access requests: {response.json()}")

def approve_or_reject_request():
    """Approve or reject an access request."""
    server_id = input("Enter Server ID: ")
    request_id = input("Enter Access Request ID: ")
    action = input("Approve or Reject? (approve/reject): ").lower()

    if action not in ["approve", "reject"]:
        print("[❌] Invalid action. Please choose 'approve' or 'reject'.")
        return

    headers = get_auth_headers()
    if not headers:
        return

    response = requests.patch(f"{BASE_URL}server/{server_id}/access-requests/{request_id}/",
                              json={"action": action},
                              headers=headers)

    if response.status_code == 200:
        print(f"[✅] Request {action}d successfully.")
    else:
        print(f"[❌] Failed to update request: {response.json()}")

def logout():
    """Clear the auth token and log out."""
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)
        print("[✅] Logged out successfully.")
    else:
        print("[❌] No token found to log out.")

def perform_task():
    """Perform tasks based on the server owner's role."""
    print("\n[🔧] Server Owner Actions:")
    print("1. View Access Requests")
    print("2. Approve/Reject Access Request")
    print("3. Logout")
    print("4. Exit")

    choice = input("Select an option: ")

    if choice == "1":
        view_access_requests()
    elif choice == "2":
        approve_or_reject_request()
    elif choice == "3":
        logout()
    elif choice == "4":
        print("[👋] Exiting CLI. Goodbye!")
        exit()
    else:
        print("[❌] Invalid choice. Please try again.")

def main():
    """Main function to drive the interactive CLI interface."""
    if not check_auth_token():
        login()

    print("\n[🚀] Welcome to the PortAccess Server Owner Interface.")
    
    while True:
        perform_task()

if __name__ == "__main__":
    main()
