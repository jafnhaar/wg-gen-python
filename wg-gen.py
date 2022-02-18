import sys
import subprocess
import random
import datetime
import socket
import os.path
import pathlib
import json


"""
1. Check if files exists in filesystem
2. If file does not exist create configuration files, get private/publc keys and create n number of configs 
3. if file exists create additional configuration files in current directory. Default to 1 file
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

def generate_qr_code(filename: str):
    """WIP"""
    pass

def generate_config(seqno: int, count_of_configs: int) -> None:
    """
    Generate wireguard configs and append at the end of wghub.conf
    """
    try:
        current_dir = str(pathlib.Path(__file__).parent.resolve()) # get current directory of a script

        with open(current_dir + os.sep + 'wg-gen.json') as json_file:
            data = json.load(json_file)
        
        for i in range (seqno + 1, seqno + int(count_of_configs) + 1):
            guest_priv_public_keys = generate_wireguard_keys()
            guest_preshared_key = generate_preshared_key()
            counter = str(i)
            with open(current_dir + os.sep + 'wghub.conf', 'a') as f:
                f.write('\n')
                f.write('# ' + counter + ' generated at ' + str(datenow) + '\n')
                f.write('[Peer]\n')
                f.write('PublicKey = ' + guest_priv_public_keys[1] + '\n')
                f.write('PresharedKey = ' + guest_preshared_key +'\n')
                f.write('AllowedIPs = ' + data['guest_subnet'] + counter + data['guest_cidr'] +'\n')
            with open(current_dir + os.sep + 'wg_client_' + counter +'.conf', 'w') as f:
                f.write('[Interface]\n')
                f.write('Address = ' + data['guest_subnet'] + counter + data['guest_cidr'] + '\n')
                f.write('DNS = ' + data['dns'] + '\n')
                f.write('PrivateKey = ' + guest_priv_public_keys[0] + '\n\n')
                f.write('[Peer]\n')
                f.write('PublicKey = ' + data['public_key'] + '\n')
                f.write('PreshareKey = ' + guest_preshared_key + '\n')
                f.write('AllowedIPs = 0.0.0.0/0\n')
                f.write('Endpoint = ' + data['ip_address'] + ':' + data['portno'] + '\n')
                f.write('PersistentKeepalive = 25')
            data['seqno'] = counter
            current_dir = str(pathlib.Path(__file__).parent.resolve())
            with open(current_dir + os.sep + "wg-gen.json", 'r+') as file:
                data_dict = json.load(file)
                data.update(data)
                file.seek(0)
                json.dump(data, file, indent=4)

    except:
        raise ValueError
    pass

priv_public_keys = generate_wireguard_keys()

current_dir = str(pathlib.Path(__file__).parent.resolve())  # get current directory of a script
datenow = str(datetime.datetime.now().isoformat(' ', 'seconds'))

if os.path.isfile('wg-gen.json'):
    try:
        configs_counter = sys.argv[1]
    except IndexError:
        configs_counter = 1
        
    with open(current_dir + os.sep + 'wg-gen.json') as json_file:
        data_dictionary = json.load(json_file)
    
    generate_config(int(data_dictionary['seqno']), configs_counter)
    

    pass
else:
    data_dictionary = {
        'private_key': priv_public_keys[0],
        'public_key': priv_public_keys[1],
        'cidr': '/24',
        'guest_cidr': '/32',
        'guest_subnet': ('10.' + str(random.randrange(0,254)) + '.' + str(random.randrange(0,254)) + '.'),
        'dns': '1.1.1.1',
        'portno': str(random.randrange(9000, 50000)),
        'ip_address': str(get_ip_address()),
        'seqno': 1
    }
 
    with open(current_dir + os.sep + 'wg-gen.json', 'w') as file:
            file.write(json.dumps(data_dictionary, indent=4))

    with open(current_dir + os.sep + 'wghub.conf', 'a') as f:
        f.write('# hub generated at '  + datenow + '\n')
        f.write('[Interface]\n')
        f.write('Address = ' + data_dictionary['guest_subnet']  + '1' + data_dictionary['cidr'] + '\n')
        f.write('ListenPort = ' + data_dictionary['portno'] + '\n')
        f.write('PrivateKey = ' + priv_public_keys[0] + '\n')
        f.write('SaveConfig = False\n')
        f.write('PostUp = iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE\n')
        f.write('PostUp = iptables -A FORWARD -i %i -j ACCEPT\n')
        f.write('PostDown = PostDown = iptables -D FORWARD -i %i -j ACCEPT\n')
        f.write('PostDown = iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE\n')
        f.write('PostUp = sysctl -q -w net.ipv4.ip_forward=1\n')
        f.write('PostDown = sysctl -q -w net.ipv4.ip_forward=0\n')
    generate_config(1,1)  # generates 1 config by default in first run
