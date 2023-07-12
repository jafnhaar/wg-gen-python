#!/usr/bin/env python3
import ipaddress
import json
import os.path
import random
import subprocess
import sys
from datetime import datetime
from typing import Dict, Tuple


class Basic:
    def get_public_ip(self) -> str:
        """Returns a string of a public ip address"""
        return json.loads(subprocess.check_output('curl -s https://ipinfo.io', shell=True).decode('utf-8'))['ip']

    def generate_private_ip(self, subnet: int = 22):
        """Returns random subnet in 10.0.0.0/8 range, defaults to 22 bit subnet"""
        generated_ip_interface = ipaddress.IPv4Interface(
            f'10.{random.randrange(0, 255)}.{random.randrange(0, 255)}.{random.randrange(0, 255)}/{subnet}'
        )
        return (list(generated_ip_interface.network.hosts())[-1], generated_ip_interface.netmask)

    def get_current_time(self) -> str:
        """Returns current time w/o milliseconds"""
        return datetime.now().isoformat(' ', 'seconds')

    def get_default_interface_name(self):
        return subprocess.check_output("ip route show 0.0.0.0/0 | awk '{print $5}' | head -n 1", shell=True).decode('UTF-8').strip()

    def read_json(self) -> json:
        """Reads json from a file"""
        with open('data.json', 'r') as file:
            return json.load(file)

    def save_json(self, data: Dict) -> None:
        """Saves json to a file"""
        with open('data.json', 'w') as file:
            json.dump(data, file, indent=4)


class Wireguard(Basic):
    def generate_wg_keys(self) -> Tuple[str, str]:
        """Generate key pair for wireguard peer."""
        privkey = subprocess.check_output('wg genkey', shell=True).decode('utf-8').strip()
        pubkey = subprocess.check_output(f"echo '{privkey}' | wg pubkey", shell=True).decode("utf-8").strip()
        return (privkey, pubkey)

    def generate_preshared_key(self) -> str:
        """Generate a preshared key"""
        return subprocess.check_output('wg genkey', shell=True).decode('utf-8').strip()

    def generate_guest_configs(self, name: str, data: Dict) -> Dict:
        "Generates peer config and adds it to wghub.conf. Takes config json file and spits it back with changed seqno"
        peer_keys = self.generate_wg_keys()
        preshared_key = self.generate_preshared_key()
        gw_address = ipaddress.IPv4Interface(f'{data["private_ip"]}/{data["private_ip_netmask"]}')
        client_ip = list(gw_address.network.hosts())[int(data["seqno"])]
        client_interface = ipaddress.IPv4Interface(f'{client_ip}/{data["private_ip_netmask"]}')

        if gw_address == client_interface:
            raise Exception('You reached last IP address in your wireguard network. No more clients can be generated.')

        with open('wghub.conf', 'a') as file:
            file.write(
                f'\n\n'
                f'# {data["seqno"]} Generated at {self.get_current_time()} for {name}\n'
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
                f'Address = {client_interface.with_prefixlen}\n'
                f'MTU = 1280\n'
                f'DNS = {data["DNS"]}\n\n'
                f'[Peer]\n'
                f'PublicKey = {data["hub_public_key"]}\n'
                f'PresharedKey = {preshared_key}\n'
                f'AllowedIPs = {data["client_allowed_ips"]}\n'
                f'Endpoint = {data["public_ip"]}:{data["port"]}\n'
                f'PersistentKeepalive = 25\n'
            )
        self.gen_qr_code(data)

        data['seqno'] = str(int(data['seqno']) + 1)
        return data

    def generate_hub(self, data: Dict[str, str]) -> None:
        """Generates wghub.conf configuration file from dictionary"""
        gw_address = ipaddress.IPv4Interface(f'{data["private_ip"]}/{data["private_ip_netmask"]}')

        with open('wghub.conf', 'w') as file:
            file.write(
                f'# hub generated at {self.get_current_time()}\n'
                f'[Interface]\n'
                f'Address = {gw_address.with_prefixlen}\n'
                f'ListenPort = {data["port"]}\n'
                f'PrivateKey = {data["hub_private_key"]}\n'
                f'SaveConfig = False\n'
                f'PostUp = iptables -t nat -A POSTROUTING -o {data["oiface"]} -j MASQUERADE\n'
                f'PostUp = iptables -A FORWARD -i %i -j ACCEPT\n'
                f'PostDown = iptables -D FORWARD -i %i -j ACCEPT\n'
                f'PostDown = iptables -t nat -D POSTROUTING -o {data["oiface"]} -j MASQUERADE\n'
                f'PostUp = sysctl -q -w net.ipv4.ip_forward=1\n'
                f'PostDown = sysctl -q -w net.ipv4.ip_forward=0\n'
            )

    def gen_qr_code(self, data: dict) -> None:
        """Generates qr code from a configuration file"""
        subprocess.run(f'qrencode -t ansiutf8 < wgclient_{int(data["seqno"])}.conf', shell=True)


def main():
    wireguard = Wireguard()
    if os.path.isfile('./data.json'):
        wireguard_data = wireguard.read_json()
        try:
            client_name = sys.argv[1]
            wireguard_data = wireguard.generate_guest_configs(client_name, wireguard_data)
        except IndexError:
            wireguard_data = wireguard.generate_guest_configs('client', wireguard_data)

        wireguard.save_json(wireguard_data)
    else:
        hub_keys = wireguard.generate_wg_keys()
        hub_ips = wireguard.generate_private_ip()
        wireguard_data = {
            'private_ip': str(hub_ips[0]),
            'private_ip_netmask': str(hub_ips[1]),
            'public_ip': wireguard.get_public_ip(),
            'hub_private_key': hub_keys[0],
            'hub_public_key': hub_keys[1],
            'seqno': '1',
            'port': str(random.randrange(10000, 60000)),
            'DNS': '1.1.1.1',
            'oiface': wireguard.get_default_interface_name(),
            'client_allowed_ips': '0.0.0.0/0'
        }
        wireguard.generate_hub(wireguard_data)

        try:
            client_name = sys.argv[1]
            wireguard_data = wireguard.generate_guest_configs(client_name, wireguard_data)
        except IndexError:
            wireguard_data = wireguard.generate_guest_configs('client', wireguard_data)

        wireguard.save_json(wireguard_data)


if __name__ == '__main__':
    main()
