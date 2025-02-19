import subprocess
import json
import os

CONFIG_FILE = "config.json"

def check_install_iptables():
    """Check if iptables is installed, install if missing."""
    try:
        subprocess.run(["iptables", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("✅ IPTables is already installed.")
    except subprocess.CalledProcessError:
        print("⚠️  IPTables is not installed. Installing now...")
        subprocess.run(["sudo", "apt", "install", "-y", "iptables"])
        print("✅ IPTables installation complete.")

def first_time_setup():
    """Prompt the user for allowed ports and configure the firewall."""
    print("🔒 Welcome to the Server Security CLI Setup! 🔒")

    # Get allowed ports from user
    default_ports = input("Enter the default web server ports (default: 80,443): ") or "80,443"
    extra_ports = input("Enter additional ports to allow (comma-separated, or press Enter to skip): ")

    # Convert to list of integers
    allowed_ports = list(map(int, default_ports.split(",")))
    if extra_ports:
        allowed_ports.extend(map(int, extra_ports.split(",")))

    # Save configuration
    config = {"allowed_ports": allowed_ports}
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

    print(f"⚙️ Blocking all incoming traffic except on ports: {', '.join(map(str, allowed_ports))}")
    apply_firewall_rules(allowed_ports)

def apply_firewall_rules(allowed_ports):
    """Apply or update firewall rules."""
    print("🚀 Updating IPTables firewall rules...")

    # Flush existing rules
    subprocess.run(["sudo", "iptables", "-F"])

    # Allow incoming traffic only on specified ports
    for port in allowed_ports:
        subprocess.run(["sudo", "iptables", "-A", "INPUT", "-p", "tcp", "--dport", str(port), "-j", "ACCEPT"])

    # Block all other incoming traffic
    subprocess.run(["sudo", "iptables", "-A", "INPUT", "-j", "DROP"])

    print("✅ Firewall rules updated successfully!")

if __name__ == "__main__":
    check_install_iptables()

    if not os.path.exists(CONFIG_FILE):
        first_time_setup()
    else:
        # Load existing config and update firewall rules
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            apply_firewall_rules(config["allowed_ports"])
