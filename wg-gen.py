import json
import os.path
import random
import sys
import subprocess

from datetime import datetime
from typing import Dict, Tuple

class Wireguard:
    def generate_private_ip(self):
        return f'10.{random.randrange(0, 255)}.{random.randrange(0, 255)}.'

    def get_current_time(self) -> str:
        return datetime.now().isoformat(' ', 'seconds')

    def read_json(self) -> json:
        with open('data.json', 'r') as file:
            return json.load(file)
    
    def save_json(self, data: Dict) -> None:
        with open('data.json', 'w') as file:
            json.dump(data, file, indent=4)

    def generate_wg_keys(self) -> Tuple[str, str]:
        """Generate key pair for wireguard peer."""
        privkey = subprocess.check_output('wg genkey', shell=True).decode('utf-8').strip()
        pubkey = subprocess.check_output(f"echo '{privkey}' | wg pubkey", shell=True).decode("utf-8").strip()
        return (privkey, pubkey)

    def generate_preshared_key(self) -> str:
        """Generate a preshared key"""
        return subprocess.check_output('wg genkey', shell=True).decode('utf-8').strip()

    def generate_guest_configs(self, name: str, data: Dict) -> None:
        "Generates peer config and adds it to wghub.conf"
        peer_keys = self.generate_wg_keys()
        preshared_key = self.generate_preshared_key()
        with open('wghub.conf', 'a') as file:
            file.write(
                f'\n\n'
                f'#{data["seqno"]} Generated at {self.get_current_time()} for {name}\n'
                f'[Peer]\n'
                f'PublicKey = {peer_keys[1]}\n'
                f'PresharedKey = {preshared_key}\n'
                f'AllowedIPs = {data["private_ip"]}{data["seqno"]}/32'
            )
        with open('wgclient_' + data['seqno'] + '.conf', 'w') as file:
            file.write(
                f'#{data["seqno"]} generated at {self.get_current_time()} for {name}\n'
                f'[Interface]\n'
                f'PrivateKey = {peer_keys[0]}\n'
                f'Address = {data["private_ip"]}{data["seqno"]}{data["cidr"]}\n'
                f'MTU = 1280'
                f'DNS = {data["DNS"]}\n\n'
                f'[Peer]\n'
                f'PublicKey = {data["hub_public_key"]}\n'
                f'PresharedKey = {preshared_key}\n'
                f'AllowedIPs = 0.0.0.0/0\n'
                f'Endpoint = {data["public_ip"]}:{data["port"]}\n'
                f'PersistentKeepalive = 25'
            )
        data['seqno'] = str(int(data['seqno']) + 1)
        return data

    def generate_hub(self, data: Dict[str, str]) -> None:
        with open('wghub.conf', 'w') as file:
            file.write(
                f'# hub generated at {self.get_current_time()}\n'
                f'[Interface]\n'
                f'Address = {data["private_ip"]}1{data["cidr"]}\n'
                f'ListenPort = {data["port"]}\n'
                f'PrivateKey = {data["hub_private_key"]}\n'
                f'SaveConfig = False\n'
                f'PostUp = iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE\n'
                f'PostUp = iptables -A FORWARD -i %i -j ACCEPT\n'
                f'PostDown = PostDown = iptables -D FORWARD -i %i -j ACCEPT\n'
                f'PostDown = iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE\n'
                f'PostUp = sysctl -q -w net.ipv4.ip_forward=1\n'
                f'PostDown = sysctl -q -w net.ipv4.ip_forward=0\n'
            )

    def get_public_ip(self) -> str:
        """Returns a string of a public ip address"""
        return json.loads(subprocess.check_output('curl -s https://ipinfo.io', shell=True).decode('utf-8'))['ip']

 
wireguard = Wireguard()
if os.path.isfile('./data.json'):
    wireguard_data = wireguard.read_json()
    wireguard.generate_guest_configs('client', wireguard_data)
else:
    hub_keys = wireguard.generate_wg_keys()
    wireguard_data = {
        'private_ip': wireguard.generate_private_ip(),
        'public_ip': wireguard.get_public_ip(),
        'hub_private_key': hub_keys[0],
        'hub_public_key': hub_keys[1],
        'seqno': '2',
        'port': str(random.randrange(10000, 60000)),
        'cidr': '/24',
        'DNS': '1.1.1.1'
    }
    wireguard.generate_hub(wireguard_data)
    wireguard.save_json(wireguard_data)
    wireguard_data = wireguard.generate_guest_configs('client', wireguard_data)
    wireguard.save_json(wireguard_data)