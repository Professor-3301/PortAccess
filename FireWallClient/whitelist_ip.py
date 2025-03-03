import os

def load_whitelist(filename):
    """Reads IPs from whitelist.txt and returns a list of valid IP addresses."""
    if not os.path.exists(filename):
        print(f"Error: {filename} not found.")
        return []
    
    with open(filename, 'r') as file:
        ips = [line.strip() for line in file if line.strip()]
    
    return ips

def apply_iptables_rules(whitelist_ips):
    """Applies iptables rules based on the given whitelist IPs."""
    print("Flushing existing rules...")
    os.system("sudo iptables -P INPUT ACCEPT")
    os.system("sudo iptables -P FORWARD ACCEPT")
    os.system("sudo iptables -P OUTPUT ACCEPT")
    os.system("sudo iptables -t nat -F")
    os.system("sudo iptables -t mangle -F")
    os.system("sudo iptables -F")
    os.system("sudo iptables -X")
    
    print("Setting default policies...")
    os.system("sudo iptables -P INPUT DROP")
    os.system("sudo iptables -P FORWARD DROP")
    os.system("sudo iptables -P OUTPUT ACCEPT")
    
    print("Allowing loopback traffic...")
    os.system("sudo iptables -A INPUT -i lo -j ACCEPT")
    
    print("Allowing established connections...")
    os.system("sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT")
    
    print("Allowing all ports for whitelisted IPs...")
    for ip in whitelist_ips:
        os.system(f"sudo iptables -A INPUT -s {ip} -j ACCEPT")
    
    print("Allowing HTTP (80) and HTTPS (443) for all users...")
    os.system("sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT")
    os.system("sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT")
    
    print("Blocking all other incoming traffic...")
    os.system("sudo iptables -A INPUT -j DROP")
    
    print("Saving rules...")
    os.system("sudo iptables-save | sudo tee /etc/iptables/rules.v4")
    
    print("Iptables rules updated successfully!")

if __name__ == "__main__":
    whitelist_ips = load_whitelist("whitelist.txt")
    if whitelist_ips:
        apply_iptables_rules(whitelist_ips)
    else:
        print("No IPs found in whitelist. No changes applied.")
