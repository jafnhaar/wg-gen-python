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

    """
    Gets system IP Address on interface. Never tested on a machine with multiple interfaces. WIP
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip_address = s.getsockname()[0]
    s.close()
    return ip_address

def generate_config(seqno: int, count_of_configs: int):
    """
    Generate wireguard configs and append at the end of wghub.conf
    """
    try:
        publickey = str(open('public.key', 'r').read())
        ip_address = str(open('ip_address.txt', 'r').read())
        port_number = str(open('portno.txt', 'r').read())
        
        for i in range (seqno, seqno + count_of_configs):
            guest_priv_public_keys = generate_wireguard_keys()
            guest_preshared_key = generate_preshared_key()
            counter = str(i)
            with open('wghub.conf', 'a') as f:
                f.write('\n')
                f.write('# ' + counter + ' generated at ' + str(datenow) + '\n')
                f.write('[Peer]\n')
                f.write('PublicKey = ' + guest_priv_public_keys[1] + '\n')
                f.write('PresharedKey = ' + guest_preshared_key +'\n')
                f.write('AllowedIPs = ' + guest_subnet + '.' + counter + guest_cidr + '\n')
            with open('wg_client_' + counter +'.conf', 'w') as f:
                f.write('[Interface]')
                f.write('Address = ' + guest_subnet + '.' + counter + guest_cidr + '\n')
                f.write('DNS = ' + dns + '\n')
                f.write('PrivateKey = ' + guest_priv_public_keys[0] + '\n\n')
                f.write('[Peer]\n')
                f.write('PublicKey = ' + publickey + '\n')
                f.write('PreshareKey = ' + guest_preshared_key + '\n')
                f.write('AllowedIPs = 0.0.0.0/0\n')
                f.write('Endpoint = ' + ip_address + ':' + port_number + '\n')
                f.write('PersistentKeepalive = 25')
            with open('seqno.txt', 'w') as f:
                f.write(str(counter))
    except:
        pass
    pass

priv_public_keys = generate_wireguard_keys()
cidr = '/24'  # default cidr
guest_cidr = '/32'
subnet = '10.'  # default private subnet for wg guests
guest_subnet = (subnet + str(random.randrange(0,254)) + '.' + str(random.randrange(0,254)))
dns = '1.1.1.1'  # default DNS
datenow = str(datetime.datetime.now().isoformat(' ', 'seconds'))
port_number = str(random.randrange(9000, 50000))
ip_address = str(get_ip_address())

if os.path.isfile('wghub.conf'):
    pass
    desired_configs = 1  # by default
    seqno = int(open('seqno.txt', 'r').read())
    try:
        desired_configs = sys.argv[1]  # if sysargv is set
    except IndexError:
        print('argument not set, defaults to 1 configuration file')
        print('Example Usage: python wg-gen.py 5 will generate 5 guest configs')
    generate_config(seqno, desired_configs)


    
else:

    with open('priv.key', 'w') as file:
        file.write(priv_public_keys[0])
    with open('public.key', 'w') as file:
        file.write(priv_public_keys[1])
    with open('ip_address.txt', 'w') as file:
        file.write(get_ip_address())
    with open('portno.txt', 'w') as file:
        file.write(str(port_number))

    # generate first part of wghub.conf file 
    with open('wghub.conf', 'a') as f:
        f.write('# hub generated at '  + datenow + '\n')
        f.write('Address = ' + guest_subnet  + '.' + '1' + cidr + '\n')
        f.write('ListenPort = ' + port_number + '\n')
        f.write('PrivateLey = ' + priv_public_keys[0] + '\n')
        f.write('SaveConfig = False\n')
        f.write('PostUp = iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE\n')
        f.write('PostUp = iptables -A FORWARD -i %i -j ACCEPT\n')
        f.write('PostDown = PostDown = iptables -D FORWARD -i %i -j ACCEPT\n')
        f.write('PostDown = iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE\n')
        f.write('PostUp = sysctl -q -w net.ipv4.ip_forward=1\n')
        f.write('PostDown = sysctl -q -w net.ipv4.ip_forward=0\n')
    generate_config(2, 3)
