# wg-gen-python
Basic usage: 
```
cd /etc/wireguard
git clone https://github.com/jafnhaar/wg-gen-python
python wg-gen.py
```

This command will generate json-data file where you can edit whatever you like. Don't forget to edit ip_address if your machine is behind NAT.  

If you want to generate qrcode out of your configuration file use this command:

```
qrencode -t ansiutf8 < wg_client_3.conf
```
WIP