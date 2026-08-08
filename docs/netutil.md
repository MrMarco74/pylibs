# pylibs.netutil

Externe IP / Hostname-Helfer, portiert aus einem internen Projekt.

```python
from pylibs.netutil import get_external_ip, get_hostname, resolve_ips

ip = get_external_ip()  # gecached, TTL 300s
hostname = get_hostname()
ips = resolve_ips("example.com")
```

`get_external_ip()` versucht der Reihe nach: konfigurierte HTTP-Dienste (Default:
ipify, ifconfig.me, icanhazip, AWS-checkip) → ausgehender UDP-Socket-Trick (Verbindung
zu 8.8.8.8, liest die lokale Adresse aus) → Hostname-Auflösung. Ergebnis wird
prozessweit für `cache_ttl` Sekunden gecacht; `force_refresh=True` erzwingt eine
Neuabfrage.

Keine zusätzliche Dependency nötig (reine stdlib).
