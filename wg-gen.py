import sys
import subprocess
import random
import datetime
import socket
import os.path


cidr = '/24'  # default cidr
subnet = '10.'  # default subnets


def generate_wireguard_keys():
    """
    Generate Wireguard key pair private/public. Both strings.
    """
    privkey = subprocess.check_output("wg genkey", shell=True).decode("utf-8").strip()
    pubkey = subprocess.check_output(f"echo '{privkey}' | wg pubkey", shell=True).decode("utf-8").strip()
    return (privkey, pubkey)


content = generate_wireguard_keys()



#f = open('private.key', 'a')
#f.write(content[0] + '\n')
#f.close()
#
#f = open('public.key', 'a')
#f.write(content[1] + '\n')
#f.close

# get ip local ip address
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
ip_address = s.getsockname()[0]
s.close()
print(ip_address)

with open('wghub.conf', 'a') as f:
    datenow = datetime.datetime.now().isoformat(' ', 'seconds')
    #print(datenow)
    f.write('# hub generated at '  + str(datenow) + '\n')
    guest_subnet = ('Address = ' + subnet + str(random.randrange(0,254)) + '.' + str(random.randrange(0,254)) + '.' + '1' + cidr + '\n')
    f.write(guest_subnet)
    f.write('ListenPort = ' + str(random.randrange(9000, 50000, 1)) + '\n')
    f.write('PrivateLey = ' + content[0] + '\n')
    f.write('SaveConfig = False\n')
    f.write('PostUp = iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE\n')
    f.write('PostUp = iptables -A FORWARD -i %i -j ACCEPT\n')
    f.write('PostDown = PostDown = iptables -D FORWARD -i %i -j ACCEPT\n')
    f.write('PostDown = iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE\n')
    f.write('PostUp = sysctl -q -w net.ipv4.ip_forward=1\n')
    f.write('PostDown = sysctl -q -w net.ipv4.ip_forward=0\n')