import io
import json
import os.path
import random
import sys
import subprocess
import pathlib
import qrcode

from typing import Tuple
from datetime import datetime
from requests import get

def generate_wireguard_keys() -> Tuple[str, str]:
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
    return subprocess.check_output("wg genkey", shell=True).decode("utf-8").strip()


def get_ip_address() -> str:

    """
    Gets system public IP Address from ipinfo.io
    """
    return get('https://ipinfo.io').json()['ip']


def generate_qr_code(filename: str) -> None:
    """Generates qr-code from file to stdout"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    f = open(filename, 'r').read()
    qr.add_data(f)
    f = io.StringIO()
    qr.print_ascii(out=f)
    f.seek(0)
    print(f.read())


def generate_config(seqno: int, count_of_configs: int) -> None:
    """
    Generate wireguard configs and append at the end of wghub.conf
    """
    # try:
    current_dir = str(pathlib.Path(__file__).parent.resolve())  # get current directory of a script

    with open(current_dir + os.sep + 'wg-gen.json') as json_file:
        data = json.load(json_file)

    for i in range(seqno, seqno + int(count_of_configs)):
        guest_priv_public_keys = generate_wireguard_keys()
        guest_preshared_key = generate_preshared_key()
        counter = str(i)
        with open(current_dir + os.sep + 'wghub.conf', 'a') as f:
            f.write(
                f'\n'
                f'# {counter} generated at {datenow}\n'
                f'[Peer]\n'
                f'PublicKey = {guest_priv_public_keys[1]}\n'
                f'PresharedKey = {guest_preshared_key}\n'
                f'AllowedIPs = {data["guest_subnet"]}{counter}{data["guest_cidr"]}\n'
            )
        client_config_name = current_dir + os.sep + 'wg_client_' + counter + '.conf'
        with open(client_config_name, 'w') as f:
            f.write(
                f'[Interface]\n'
                f'Address = {data["guest_subnet"]}{counter}{data["guest_cidr"]}\n'
                f'DNS = {data["dns"]}\n'
                f'PrivateKey = {guest_priv_public_keys[0]}\n\n'
                f'[Peer]\n'
                f'PublicKey = {data["public_key"]}\n'
                f'PresharedKey = {guest_preshared_key}\n'
                f'AllowedIPs = 0.0.0.0/0\n'
                f'Endpoint = {data["ip_address"]}:{data["portno"]}\n'
                f'PersistentKeepalive = 25'
            )
        data['seqno'] = counter
        current_dir = str(pathlib.Path(__file__).parent.resolve())
        with open('wg-gen.json', 'w') as jsonfile:
            json.dump(data, jsonfile, indent=4)
        generate_qr_code(client_config_name)
    # except:
    #     raise ValueError


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
        'guest_subnet': ('10.' + str(random.randrange(0, 254)) + '.' + str(random.randrange(0, 254)) + '.'
                         ),
        'dns': '1.1.1.1',
        'portno': str(random.randrange(9000, 50000)),
        'ip_address': str(get_ip_address()),
        'seqno': 1
    }

    with open(current_dir + os.sep + 'wg-gen.json', 'w') as file:
        file.write(json.dumps(data_dictionary, indent=4))

    with open(current_dir + os.sep + 'wghub.conf', 'w') as f:
        f.write(
            f'# hub generate at {datenow} \n'
            f'[Interface]\n'
            f'Address = {data_dictionary["guest_subnet"]}1{data_dictionary["cidr"]}\n'
            f'ListenPort = {data_dictionary["portno"]}\n'
            f'PrivateKey = {data_dictionary["private_key"]}\n'
            f'SaveConfig = False\n'
            f'PostUp = iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE\n'
            f'PostUp = iptables -A FORWARD -i %i -j ACCEPT\n'
            f'PostDown = PostDown = iptables -D FORWARD -i %i -j ACCEPT\n'
            f'PostDown = iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE\n'
            f'PostUp = sysctl -q -w net.ipv4.ip_forward=1\n'
            f'PostDown = sysctl -q -w net.ipv4.ip_forward=0\n'
        )
    generate_config(2, 1)  # generates 1 config by default in first run
