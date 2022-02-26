# wg-gen-python
## What this script does?
Generates pair of client-server configuration for Wireguard VPN. With ease. In future it will generates qr-codes and stdout them to console. 
Script automatically sets masquerade wg interface for you (with iptables) and does sysctl magic. No need to worry about anything. It just works.
### Requirements
```
curl
python3
wireguard-tools
```
### Basic usage: 
```Bash
apt install python3 -y
cd /etc/wireguard
git clone https://github.com/jafnhaar/wg-gen-python
cd wg-gen-python
python3 wg-gen.py
```

First run of this commands will generate basic configuration. After that if wg-gen.json exists it will create additional config files for you
## qr codes
This script will automatically generate qrcode for your configuration if qrencode installed.
If you want to generate qrcode out of your configuration file use this command:

```bash
apt install qrencode -y
qrencode -t ansiutf8 < wgclient_2.conf
```
## Easy identification
You can easily identify for whom you generated current config by adding client name to script while running it. Client name will appear in comment section before peer in wghub.conf and in client configuration file. In example:
```bash
python3 wg-gen.py my-laptop
```



# Running Wireguard
```Bash
ln -s $PWD/wghub.conf /etc/wireguard/wg0.conf
wg-quick up wg0
```

### Currently tested on:
 - Alpine Linux 3.15 (LXC)
 - Debian 11
 - Arch Linux

WIP