import os
import json
import requests
import typer
import time
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from auth import load_token, login, signup
import subprocess

# ✅ API Endpoint
BASE_URL = "http://127.0.0.1:333/api/"

console = Console()
app = typer.Typer()

def check_auth():
    """Ensure authentication before proceeding."""
    token = load_token()
    if not token:
        console.print("[⚠️] No valid auth token found. Please log in or sign up.", style="bold red")
        action = Prompt.ask("Do you want to (1) Login or (2) Signup?", choices=["1", "2"])
        if action == "1":
            login()
        elif action == "2":
            signup()
        else:
            console.print("[❌] Invalid choice. Exiting...", style="bold red")
            raise typer.Exit()

def get_auth_headers():
    """Return headers with JWT token if authenticated."""
    token = load_token()
    if token:
        return {"Authorization": f"Bearer {token['token']}"}
    else:
        console.print("[⚠️] Not authenticated. Please login.", style="bold yellow")
        return None

def view_access_requests():
    """View access requests submitted by pentesters."""
    check_auth()
    console.print("\n[📄] Viewing Access Requests:", style="bold cyan")
    server_id = Prompt.ask("Enter Server ID")

    headers = get_auth_headers()
    if not headers:
        return

    response = requests.get(f"{BASE_URL}server/{server_id}/access-requests/", headers=headers)

    if response.status_code == 200:
        requests_data = response.json()
        if not requests_data:
            console.print("[ℹ️] No pending access requests.", style="bold yellow")
            return

        table = Table(title="Access Requests", style="bold magenta")
        table.add_column("Request ID", style="cyan")
        table.add_column("Pentester", style="blue")
        table.add_column("Aadhar/SSN", style="green")
        table.add_column("Certifications", style="yellow")
        table.add_column("Status", style="bold red")
        table.add_column("Requested At", style="white")

        for request in requests_data:
            pentester = request['pentester']
            table.add_row(
                str(request['request_id']),  # Convert to string
                str(pentester['username']),
                str(pentester['aadhar_or_ssn']),
                str(pentester.get('certifications', 'N/A')),
                str(request['status']),
                str(request['requested_at'])  # Convert to string
            )

        console.print(table)
    else:
        console.print(f"[❌] Failed to fetch access requests: {response.json()}", style="bold red")


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
        console.print(f"[✅] Request {action}d successfully.", style="bold green")

        if "pentester_ip" in data:
            pentester_ip = data["pentester_ip"]
            
            if action == "approve":
                add_ip(pentester_ip)  # Add IP if approved
            else:
                remove_ip(pentester_ip)  # Remove IP if rejected

            # Run script to update whitelist
            subprocess.run(["python3", "whitelist_ip.py"])  
            console.print(f"[🔹] Whitelist updated successfully.", style="bold cyan")
        
    else:
        console.print(f"[❌] Failed to update request: {response.json()}", style="bold red")


def change_password():
    """Allow the server owner to change their password."""
    check_auth()

    old_password = Prompt.ask("[🔑] Enter Old Password", password=True)
    new_password = Prompt.ask("[🔑] Enter New Password", password=True)

    headers = get_auth_headers()
    if not headers:
        return

    response = requests.post(  # Change PATCH to POST or PUT
        f"{BASE_URL}server-owner/change-password/",
        json={"old_password": old_password, "new_password": new_password},
        headers=headers
    )

    try:
        if response.status_code == 200:
            console.print("[✅] Password updated successfully.", style="bold green")
        else:
            error_message = response.json() if response.text else "[❌] No response from server."
            console.print(f"[❌] Failed to update password: {error_message}", style="bold red")
    except requests.exceptions.JSONDecodeError:
        console.print("[❌] Server returned an invalid response. Check if the API is running.", style="bold red")

def add_ip(ip):
    """Add the approved IP to whitelist.txt."""
    with open("whitelist.txt", "a") as file:
        file.write(ip + "\n")
    console.print(f"[🔹] IP {ip} added to whitelist.txt", style="bold blue")

def remove_ip(ip):
    """Remove the rejected IP from whitelist.txt."""
    try:
        with open("whitelist.txt", "r") as file:
            lines = file.readlines()

        with open("whitelist.txt", "w") as file:
            for line in lines:
                if line.strip() != ip:
                    file.write(line)

        console.print(f"[🔻] IP {ip} removed from whitelist.txt", style="bold red")

    except FileNotFoundError:
        console.print("[⚠] whitelist.txt not found. No changes made.", style="bold yellow")

def logout():
    """Log out by removing the authentication token."""
    if os.path.exists("auth_token.json"):
        os.remove("auth_token.json")
        console.print("[✅] Logged out successfully.", style="bold green")
    else:
        console.print("[❌] No token found to log out.", style="bold red")

def main_menu():
    """Interactive main menu."""
    check_auth()

    while True:
        console.print("\n[🔧] Server Owner Actions:", style="bold blue")
        console.print("[1] View Access Requests", style="bold cyan")
        console.print("[2] Approve/Reject Access Request", style="bold yellow")
        console.print("[3] Change Password", style="bold green")
        console.print("[4] Logout", style="bold red")
        console.print("[5] Exit", style="bold white")

        choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4", "5"])

        if choice == "1":
            view_access_requests()
        elif choice == "2":
            approve_or_reject_request()
        elif choice == "3":
            change_password()
        elif choice == "4":
            logout()
            break
        elif choice == "5":
            console.print("[👋] Exiting CLI. Goodbye!", style="bold magenta")
            break
        else:
            console.print("[❌] Invalid choice. Please try again.", style="bold red")

if __name__ == "__main__":
    main_menu()
