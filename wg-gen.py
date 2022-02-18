import sys
import subprocess
import random
import datetime
import socket
import os.path


"""
1. Check if files exists in filesystem
2. If file does not exist create configuration files, get private/publc keys and create n number of configs 
3. if file exists create additional configuration files in current directory
"""

def generate_wireguard_keys():
    """
    Generate Wireguard key pair private/public. Both strings.
    """
    privkey = subprocess.check_output("wg genkey", shell=True).decode("utf-8").strip()
    pubkey = subprocess.check_output(f"echo '{privkey}' | wg pubkey", shell=True).decode("utf-8").strip()
    return (privkey, pubkey)

def generate_preshared_key():
    """
    Generate wireguard preshared key for guests.
    """
    presharedkey = subprocess.check_output("wg genkey", shell=True).decode("utf-8").strip()
    return str(presharedkey)

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip_address = s.getsockname()[0]
    s.close()
    return ip_address

if os.path.isfile('wghub.conf'):
    pass
else: 
    priv_public_keys = generate_wireguard_keys()
    cidr = '/24'  # default cidr
    guest_cidr = '/32'
    subnet = '10.'  # default private subnet for wg guests
    guest_subnet = (subnet + str(random.randrange(0,254)) + '.' + str(random.randrange(0,254)))


    with open ('priv.key', 'a') as file:
        file.write(priv_public_keys[0])
        file.close()
    with open ('public.key', 'a') as file:
        file.write(priv_public_keys[1])
        file.close()
    with open('ip_address.txt', 'a') as file:
        file.write(get_ip_address())
        file.close()


    # generate first part of wghub.conf file 
    with open('wghub.conf', 'a') as f:
        datenow = str(datetime.datetime.now().isoformat(' ', 'seconds'))
        #print(datenow)
        f.write('# hub generated at '  + datenow + '\n')
        f.write('Address = ' + guest_subnet  + '.' + '1' + cidr + '\n')
        f.write('ListenPort = ' + str(random.randrange(9000, 50000, 1)) + '\n')
        f.write('PrivateLey = ' + priv_public_keys[0] + '\n')
        f.write('SaveConfig = False\n')
        f.write('PostUp = iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE\n')
        f.write('PostUp = iptables -A FORWARD -i %i -j ACCEPT\n')
        f.write('PostDown = PostDown = iptables -D FORWARD -i %i -j ACCEPT\n')
        f.write('PostDown = iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE\n')
        f.write('PostUp = sysctl -q -w net.ipv4.ip_forward=1\n')
        f.write('PostDown = sysctl -q -w net.ipv4.ip_forward=0\n')

    for i in range(2, 4):

    # generate client part of wghub.conf file
        guest_priv_public_keys = generate_wireguard_keys()
        guest_preshared_key = generate_preshared_key()
        counter = str(i)
        with open('wghub.conf', 'a') as f:
            f.write('\n')
            f.write('# generated at' + str(datenow) + '\n')
            f.write('[Peer]\n')
            f.write('PublicKey = ' + '\n')
            f.write('PresharedKey = ' + guest_preshared_key +'\n')
            f.write('AllowedIPs = ' + guest_subnet + '.' + counter + guest_cidr + '\n')
