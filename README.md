# wg-gen-python
Basic usage: 
```Bash
apt install python -y
cd /etc/wireguard
git clone https://github.com/jafnhaar/wg-gen-python
cd wg-gen-python
python wg-gen.py
```

This command will generate json-data file where you can edit whatever you like. Don't forget to edit ip_address if your machine is behind NAT.  

If you want to generate qrcode out of your configuration file use this command:

```bash
apt install qrencode -y
qrencode -t ansiutf8 < wg_client_3.conf
```

# Running Wireguard
```Bash
ln -s $pwd/wghub.con /etc/wireguard/wg0.conf
wg-quick up wg0
```
WIP