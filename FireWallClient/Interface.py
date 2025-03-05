import os
import json
import requests
import time
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from auth import load_token, login, signup
import subprocess

# ✅ API Endpoint
BASE_URL = "http://127.0.0.1:333/api/"

console = Console()

def check_auth():
    """Ensure authentication before proceeding."""
    token = load_token()
    if not token:
        console.print("[!] No valid auth token found. Please log in or sign up.")
        action = Prompt.ask("Do you want to (1) Login or (2) Signup?", choices=["1", "2"])
        if action == "1":
            login()
        elif action == "2":
            signup()
        else:
            console.print("[!] Invalid choice. Exiting...")
            exit()

def get_auth_headers():
    """Return headers with JWT token if authenticated."""
    token = load_token()
    if token:
        return {"Authorization": f"Bearer {token['token']}"}
    else:
        console.print("[!] Not authenticated. Please login.")
        return None

def view_server_owner_details():
    """Fetch details of the currently logged-in server owner."""
    check_auth()
    console.print("\n[+] Fetching Server Owner Details...")

    headers = get_auth_headers()
    if not headers:
        return

    response = requests.get(f"{BASE_URL}server-owner/details/", headers=headers)

    if response.status_code == 200:
        owner_details = response.json()

        table = Table(title="Server Owner Details")
        table.add_column("Field", style="cyan", justify="right")
        table.add_column("Value", style="magenta")

        table.add_row("ID", str(owner_details.get("id", "N/A")))
        table.add_row("Username", str(owner_details.get("username", "N/A")))
        table.add_row("Email", str(owner_details.get("email", "N/A")))
        table.add_row("IP Address", str(owner_details.get("ip", "N/A")))
        table.add_row("Name", str(owner_details.get("name", "N/A")))
        table.add_row("Domain", str(owner_details.get("domain", "N/A")))

        console.print(table)
    elif response.status_code == 401:
        console.print("\n❌ Authentication Error: Invalid or expired token.")
    elif response.status_code == 403:
        console.print("\n⛔ Access Denied: Only server owners can view their details.")
    elif response.status_code == 404:
        console.print("\n⚠️ No server owner details found.")
    else:
        console.print(f"\n⚠️ Unexpected Error: {response.status_code} - {response.text}")

        
def view_access_requests():
    """View access requests submitted by pentesters."""
    check_auth()
    console.print("\n[+] Viewing Access Requests:")
    server_id = Prompt.ask("Enter Server ID")

    headers = get_auth_headers()
    if not headers:
        return

    response = requests.get(f"{BASE_URL}server/{server_id}/access-requests/", headers=headers)

    if response.status_code == 200:
        requests_data = response.json()
        if not requests_data:
            console.print("[-] No pending access requests.")
            return

        table = Table()
        table.add_column("Request ID")
        table.add_column("Pentester")
        table.add_column("Aadhar/SSN")
        table.add_column("Certifications")
        table.add_column("Status")
        table.add_column("Requested At")

        for request in requests_data:
            pentester = request['pentester']
            table.add_row(
                str(request['request_id']),
                str(pentester['username']),
                str(pentester['aadhar_or_ssn']),
                str(pentester.get('certifications', 'N/A')),
                str(request['status']),
                str(request['requested_at'])
            )
        
        console.print(table)
    else:
        console.print(f"[!] Failed to fetch access requests: {response.json()}")

def approve_or_reject_request():
    """Approve or reject an access request."""
    check_auth()
    server_id = Prompt.ask("Enter Server ID")
    request_id = Prompt.ask("Enter Access Request ID")
    action = Prompt.ask("Approve or Reject?", choices=["approve", "reject"])

    headers = get_auth_headers()
    if not headers:
        return

    response = requests.patch(f"{BASE_URL}server/{server_id}/access-requests/{request_id}/",
                              json={"action": action},
                              headers=headers)

    if response.status_code == 200:
        data = response.json()
        console.print(f"[+] Request {action}d successfully.")

        if "pentester_ip" in data:
            pentester_ip = data["pentester_ip"]
            
            if action == "approve":
                add_ip(pentester_ip)
            else:
                remove_ip(pentester_ip)

            subprocess.run(["python3", "whitelist_ip.py"])
            console.print("[+] Whitelist updated successfully.")
    else:
        console.print(f"[!] Failed to update request: {response.json()}")



def change_password():
    """Allow the server owner to change their password."""
    check_auth()

    old_password = Prompt.ask("Enter Old Password", password=True)
    new_password = Prompt.ask("Enter New Password", password=True)

    headers = get_auth_headers()
    if not headers:
        return

    response = requests.post(
        f"{BASE_URL}server-owner/change-password/",
        json={"old_password": old_password, "new_password": new_password},
        headers=headers
    )

    try:
        if response.status_code == 200:
            console.print("[+] Password updated successfully.")
        else:
            error_message = response.json() if response.text else "[!] No response from server."
            console.print(f"[!] Failed to update password: {error_message}")
    except requests.exceptions.JSONDecodeError:
        console.print("[!] Server returned an invalid response. Check if the API is running.")

def add_ip(ip):
    """Add the approved IP to whitelist.txt."""
    with open("whitelist.txt", "a") as file:
        file.write(ip + "\n")
    console.print(f"[+] IP {ip} added to whitelist.txt")

def remove_ip(ip):
    """Remove the rejected IP from whitelist.txt."""
    try:
        with open("whitelist.txt", "r") as file:
            lines = file.readlines()

        with open("whitelist.txt", "w") as file:
            for line in lines:
                if line.strip() != ip:
                    file.write(line)

        console.print(f"[-] IP {ip} removed from whitelist.txt")
    except FileNotFoundError:
        console.print("[!] whitelist.txt not found. No changes made.")

def logout():
    """Log out by removing the authentication token."""
    if os.path.exists("auth_token.json"):
        os.remove("auth_token.json")
        console.print("[+] Logged out successfully.")
    else:
        console.print("[!] No token found to log out.")

def main_menu():
    """Interactive main menu."""
    check_auth()

    while True:
        console.print("\n[ Server Owner Actions ]")
        console.print("[1] View Access Requests")
        console.print("[2] Approve/Reject Access Request")
        console.print("[3] Change Password")
        console.print("[4] View Server Owner Details")
        console.print("[5] Logout")
        console.print("[6] Exit")

        choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4", "5", "6"])

        if choice == "1":
            view_access_requests()
        elif choice == "2":
            approve_or_reject_request()
        elif choice == "3":
            change_password()
        elif choice == "4":
            view_server_owner_details()
        elif choice == "5":
            logout()
            break
        elif choice == "6":
            console.print("[+] Exiting CLI. Goodbye!")
            break
        else:
            console.print("[!] Invalid choice. Please try again.")

if __name__ == "__main__":
    main_menu()
