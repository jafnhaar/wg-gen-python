from typing import Tuple
import sys
import subprocess
from requests import get
import random
from datetime import datetime
import os.path
import pathlib
import json
import qrcode
import io

"""
1. Check if files exists in filesystem
2. If file does not exist create configuration files, get private/publc keys and create n number of configs
3. if file exists create additional configuration files in current directory. Default to 1 file
"""


def generate_wireguard_keys() -> Tuple:
    """
    Generate Wireguard key pair private/public. Both strings.
    """
    privkey = subprocess.check_output("wg genkey", shell=True).decode("utf-8").strip()
    pubkey = subprocess.check_output(f"echo '{privkey}' | wg pubkey", shell=True).decode("utf-8").strip()
    return (privkey, pubkey)


def generate_preshared_key() -> str:
    """
    Generate wireguard preshared key for guests.
    """
    return str(subprocess.check_output("wg genkey", shell=True).decode("utf-8"))


def get_ip_address() -> str:

    """
    Gets system public IP Address from ipinfo.io
    """
    ip_address = get('https://ipinfo.io')
    ip_address = json.loads(ip_address.text)
    return ip_address['ip']


def generate_qr_code(filename: str) -> None:
    """generates qr-code from file to stdout"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    f = open('wg_client_3.conf', 'r').read()
    qr.add_data(f)
    f = io.StringIO()
    qr.print_ascii(out=f)
    f.seek(0)
    print(f.read())


def generate_config(seqno: int, count_of_configs: int) -> None:
    """
    Generate wireguard configs and append at the end of wghub.conf
    """
    try:
        current_dir = str(pathlib.Path(__file__).parent.resolve())  # get current directory of a script

        with open(current_dir + os.sep + 'wg-gen.json') as json_file:
            data = json.load(json_file)

        for i in range(seqno, seqno + int(count_of_configs)):
            guest_priv_public_keys = generate_wireguard_keys()
            guest_preshared_key = generate_preshared_key()
            counter = str(i)
            with open(current_dir + os.sep + 'wghub.conf', 'a') as f:
                f.write('\n')
                f.write('# ' 
                        + counter 
                        + ' generated at ' 
                        + str(datenow) 
                        + '\n'
                        )
                f.write('[Peer]\n')
                f.write('PublicKey = ' 
                        + guest_priv_public_keys[1] 
                        + '\n'
                        )
                f.write('PresharedKey = ' 
                        + guest_preshared_key 
                        + '\n'
                        )
                f.write('AllowedIPs = ' 
                        + data['guest_subnet'] 
                        + counter 
                        + data['guest_cidr'] 
                        + '\n')
            with open(current_dir + os.sep + 'wg_client_' + counter + '.conf', 'w') as f:
                f.write('[Interface]\n')
                f.write('Address = ' 
                        + data['guest_subnet'] 
                        + counter 
                        + data['guest_cidr'] 
                        + '\n')
                f.write('DNS = ' 
                        + data['dns'] 
                        + '\n')
                f.write('PrivateKey = ' 
                        + guest_priv_public_keys[0] 
                        + '\n\n')
                f.write('[Peer]\n')
                f.write('PublicKey = ' 
                        + data['public_key'] 
                        + '\n')
                f.write('PresharedKey = ' 
                        + guest_preshared_key)
                f.write('AllowedIPs = 0.0.0.0/0\n')
                f.write('Endpoint = ' 
                        + data['ip_address'] + ':' 
                        + data['portno'] 
                        + '\n')
                f.write('PersistentKeepalive = 25')
            data['seqno'] = counter
            current_dir = str(pathlib.Path(__file__).parent.resolve())
            with open('wg-gen.json', 'w') as jsonfile:
                json.dump(data, jsonfile, indent=4)

    except:
        raise ValueError
    pass


priv_public_keys = generate_wireguard_keys()

current_dir = str(pathlib.Path(__file__).parent.resolve())  # get current directory of a script
datenow = str(datetime.now().isoformat(' ', 'seconds'))

if os.path.isfile('wg-gen.json'):
    try:
        configs_counter = sys.argv[1]
    except IndexError:
        configs_counter = 1

    with open(current_dir + os.sep + 'wg-gen.json') as json_file:
        data_dictionary = json.load(json_file)

    generate_config(int(data_dictionary['seqno']) + 1, configs_counter)

else:
    data_dictionary = {
        'private_key': priv_public_keys[0],
        'public_key': priv_public_keys[1],
        'cidr': '/24',
        'guest_cidr': '/32',
        'guest_subnet': ('10.'
                         + str(random.randrange(0, 254)) + '.'
                         + str(random.randrange(0, 254)) + '.'
                         ),
        'dns': '1.1.1.1',
        'portno': str(random.randrange(9000, 50000)),
        'ip_address': str(get_ip_address()),
        'seqno': 1
    }

    with open(current_dir + os.sep + 'wg-gen.json', 'w') as file:
        file.write(json.dumps(data_dictionary, indent=4))

    with open(current_dir + os.sep + 'wghub.conf', 'w') as f:
        f.write('# hub generated at ' + datenow + '\n')
        f.write('[Interface]\n')
        f.write('Address = ' 
                + data_dictionary['guest_subnet'] + '1' 
                + data_dictionary['cidr'] + '\n')
        f.write('ListenPort = ' 
                + data_dictionary['portno'] + '\n')
        f.write('PrivateKey = ' 
                + priv_public_keys[0] + '\n')
        f.write('SaveConfig = False\n')
        f.write('PostUp = iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE\n')
        f.write('PostUp = iptables -A FORWARD -i %i -j ACCEPT\n')
        f.write('PostDown = PostDown = iptables -D FORWARD -i %i -j ACCEPT\n')
        f.write('PostDown = iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE\n')
        f.write('PostUp = sysctl -q -w net.ipv4.ip_forward=1\n')
        f.write('PostDown = sysctl -q -w net.ipv4.ip_forward=0\n')
    generate_config(2, 1)  # generates 1 config by default in first run
