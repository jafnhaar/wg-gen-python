# wg-gen-python
Creates configurations for peers and server. It just works.
## What this script does?
Generates pair of client-server configuration for Wireguard VPN. With ease. In future it will generates qr-codes and stdout them to console. 
Script automatically sets masquerade wg interface for you (with iptables) and does sysctl magic. No need to worry about anything. It just works.
### Requirements
```
curl
python3
wireguard-tools
qrencode
```
### Basic usage: 
```Bash
apt install python3 curl wireguard-tools qrencode -y
cd /etc/wireguard
git clone https://github.com/jafnhaar/wg-gen-python
cd wg-gen-python
chmod +x wg-gen.py
./wg-gen.py
```

First run of this commands will generate basic configuration. After that if wg-gen.json exists it will create additional config files for you
## qr codes
This script will automatically generate qrcode for your configuration if qrencode installed.
If you want to generate qrcode out of your configuration file use this command:

```Bash
qrencode -t ansiutf8 < wgclient_2.conf
```
## Easy identification
You can easily identify for whom you generated current config by adding client name to script while running it. Client name will appear in comment section before peer in wghub.conf and in client configuration file. In example:
```bash
./wg-gen.py my-laptop
```

# Starting Wireguard interface
```Bash
ln -s $PWD/wghub.conf /etc/wireguard/wg0.conf
wg-quick up wg0
```

# Reloading Wireguard
```Bash
wg-quick down wg0 && wg-quick up wg0
```

# Troubleshooting

Most common problem is correctly determining your main interface name. By default script masquerades eth0. If you have different interface name change it to whatever you like (i.e. ens18).

You can find your default interface by running next command:  
```
ip addr 
```

# Currently tested on:
 - Alpine Linux 3.15 (LXC)
 - Arch Linux
 - Debian 11
 - Ubuntu 21.10 (LXC)

WIP
