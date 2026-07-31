import json
import os
import socket
import threading
import time
import requests
from rich.console import Console
from rich.panel import Panel

console = Console()
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
APP_NAME = "NOVA SMS"
CLOUD_API = "https://alerta-sula-hn.vercel.app/api"
BROADCAST_PORT = 8082
DISCOVERED_ANDROID = {"ip": "", "port": 8080, "last_seen": 0}


def cargar_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def guardar_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def listen_for_android(stop_event):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(1)
    try:
        sock.bind(("0.0.0.0", BROADCAST_PORT))
    except OSError:
        pass
    while not stop_event.is_set():
        try:
            data, addr = sock.recvfrom(1024)
            msg = json.loads(data.decode())
            if msg.get("type") == "sms_server":
                DISCOVERED_ANDROID["ip"] = msg["ip"]
                DISCOVERED_ANDROID["port"] = msg.get("port", 8080)
                DISCOVERED_ANDROID["last_seen"] = time.time()
                cfg = cargar_config()
                cfg["android_server"] = {"ip": msg["ip"], "port": msg.get("port", 8080)}
                guardar_config(cfg)
        except (socket.timeout, json.JSONDecodeError, KeyError):
            pass
    sock.close()


def get_android_ip():
    if DISCOVERED_ANDROID["ip"] and (time.time() - DISCOVERED_ANDROID["last_seen"]) < 10:
        return DISCOVERED_ANDROID["ip"], DISCOVERED_ANDROID["port"]
    cfg = cargar_config().get("android_server", {})
    ip = cfg.get("ip", "")
    if not ip and DISCOVERED_ANDROID["ip"]:
        ip = DISCOVERED_ANDROID["ip"]
    return ip, cfg.get("port", 8080)


def setup_android_server():
    console.print()
    console.print(Panel.fit(
        "[bold cyan]CONFIGURAR ANDROID - NOVA SMS[/bold cyan]\n\n"
        "Paso 1: Instala Termux + Termux:API desde F-Droid\n\n"
        "Paso 2: Abri Termux, corre:\n"
        "  [bold]pkg update && pkg upgrade -y[/bold]\n"
        "  [bold]pkg install python termux-api -y[/bold]\n"
        "  [bold]pip install requests[/bold]\n\n"
        "Paso 3: Crea el archivo server_android.py (copialo de la PC):\n"
        "  [bold]termux-setup-storage[/bold]\n"
        "  [bold]cp /storage/emulated/0/Download/server_android.py ~/[/bold]\n\n"
        "Paso 4: Corre el servidor:\n"
        "  [bold]python ~/server_android.py[/bold]\n\n"
        "Paso 5: Conecta tu Android al hotspot WiFi de tu PC\n"
        "   Fijate la IP del Android: Settings > WiFi > (tu red) > IP\n"
        "   O en Termux corre: [bold]ip addr[/bold] y busca 192.168.x.x",
        border_style="cyan"
    ))
    ip = console.input("\n[cyan]IP del Android:[/cyan] ").strip()
    config = cargar_config()
    config["android_server"] = {"ip": ip, "port": 8080}
    guardar_config(config)
    console.print(f"[green]Android configurado en {ip}:8080![/green]")
    console.print("[yellow]Deja Termux abierto con el servidor corriendo[/yellow]")
    console.input("\nPresiona ENTER para volver al menu...")


def enviar_android_server(numero, mensaje):
    ip, port = get_android_ip()
    if not ip:
        return False, "Android no configurado ni detectado en la red"
    url = f"http://{ip}:{port}"
    try:
        resp = requests.post(url, json={"to": numero, "message": mensaje}, timeout=20)
        data = resp.json()
        if data.get("success"):
            return True, "SMS enviado desde tu Android"
        return False, data.get("error", "Error del servidor Termux")
    except requests.exceptions.ConnectionError:
        detected = DISCOVERED_ANDROID["ip"]
        if detected and detected != ip:
            DISCOVERED_ANDROID["ip"] = ""
            ip2, port2 = get_android_ip()
            if ip2:
                url2 = f"http://{ip2}:{port2}"
                try:
                    resp2 = requests.post(url2, json={"to": numero, "message": mensaje}, timeout=20)
                    data2 = resp2.json()
                    if data2.get("success"):
                        return True, f"SMS enviado via IP descubierta {ip2}"
                    return False, data2.get("error", "Error")
                except Exception:
                    pass
        return False, f"No conecta a {url}\nEl servidor se auto-detecta cuando este en la red"
    except Exception as e:
        return False, str(e)


def enviar_cloud(numero, mensaje):
    try:
        resp = requests.post(f"{CLOUD_API}/send-sms", json={
            "to": numero, "message": mensaje
        }, timeout=20)
        data = resp.json()
        if data.get("success"):
            return True, f"Encolado en nube (ID: {data.get('id', '?')})"
        return False, data.get("error", "Error del servidor")
    except requests.exceptions.ConnectionError:
        return False, f"No conecta a {CLOUD_API}"
    except Exception as e:
        return False, str(e)


def get_modo():
    cfg = cargar_config().get("modo", "cloud")
    return cfg


def set_modo(m):
    cfg = cargar_config()
    cfg["modo"] = m
    guardar_config(cfg)


def main():
    console.print()
    console.print(Panel.fit(
        f"[bold bright_cyan]   N O V A   S M S   v2.0   [/bold bright_cyan]\n"
        "[dim]  Envio inteligente via Android + Vercel Cloud  [/dim]\n"
        "[bold green]  Modos: Local (directo) / Cloud (Vercel)[/bold green]",
        border_style="cyan"
    ))

    stop_event = threading.Event()
    listener = threading.Thread(target=listen_for_android, args=(stop_event,), daemon=True)
    listener.start()

    while True:
        console.print()
        console.print("[bold cyan] MENU [/bold cyan]")
        console.print("  [bold green]1[/bold green] Enviar SMS")
        console.print("  [bold green]2[/bold green] Configurar/conectar Android (local)")
        console.print("  [bold green]3[/bold green] Cambiar modo de envio")
        console.print("  [bold green]4[/bold green] Salir")
        console.print()

        modo = get_modo()
        if modo == "local":
            if DISCOVERED_ANDROID["ip"]:
                last = time.time() - DISCOVERED_ANDROID["last_seen"]
                status = f"[green]Local - Android en {DISCOVERED_ANDROID['ip']}:{DISCOVERED_ANDROID['port']}[/green]"
            else:
                cfg = cargar_config().get("android_server", {})
                if cfg.get("ip"):
                    status = f"[yellow]Local - config {cfg['ip']}:{cfg.get('port', 8080)} (no responde)[/yellow]"
                else:
                    status = "[red]Local - Android no configurado[/red]"
        else:
            status = f"[cyan]Cloud - via Vercel[/cyan]"
        console.print(f"  Modo: {status}")

        opcion = console.input("[cyan]Selecciona (1-4):[/cyan] ").strip()

        if opcion == "1":
            if modo == "local":
                ip, port = get_android_ip()
                if not ip:
                    console.print("[red]Android no detectado en modo local[/red]")
                    continue
                destino = f"ANDROID ({ip}:{port})"
            else:
                destino = "CLOUD (Vercel)"

            console.print("\n[bold yellow]Numero de destino (formato internacional):[/bold yellow]")
            numero = console.input("[cyan]>[/cyan] ").strip()
            if not numero.startswith("+"):
                if numero.isdigit() and len(numero) == 8:
                    numero = f"+504{numero}"
                else:
                    console.print("[red]Formato invalido. Usa +504XXXXXXXX[/red]")
                    continue

            console.print("\n[bold yellow]Escribe tu mensaje:[/bold yellow]")
            mensaje = console.input("[cyan]>[/cyan] ").strip()
            if not mensaje:
                console.print("[red]El mensaje no puede estar vacio.[/red]")
                continue

            if modo == "local":
                console.print(f"\n[yellow]Enviando via {destino}...[/yellow]")
                ok, info = enviar_android_server(numero, mensaje)
            else:
                console.print(f"\n[yellow]Enviando via {destino}...[/yellow]")
                ok, info = enviar_cloud(numero, mensaje)

            if ok:
                console.print(Panel.fit(
                    f"[bold green]SMS ENVIADO[/bold green]\n\n"
                    f"[bold]Para:[/bold] {numero}\n"
                    f"[bold]Mensaje:[/bold] {mensaje}\n"
                    f"[bold]Info:[/bold] {info}",
                    border_style="green"
                ))
            else:
                console.print(Panel.fit(f"[bold red]ERROR[/bold red]\n\n{info}", border_style="red"))

        elif opcion == "2":
            setup_android_server()

        elif opcion == "3":
            m = get_modo()
            nuevo = "cloud" if m == "local" else "local"
            set_modo(nuevo)
            nombre = "Cloud (Vercel)" if nuevo == "cloud" else "Local (directo)"
            console.print(f"[green]Modo cambiado a: {nombre}[/green]")

        elif opcion == "4":
            console.print("\n[green]Chao![/green]")
            stop_event.set()
            break
        else:
            console.print("[red]Opcion no valida.[/red]")

        console.print()
        input("Presiona ENTER para continuar...")


if __name__ == "__main__":
    main()
