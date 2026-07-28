import json
import os
import requests
from rich.console import Console
from rich.panel import Panel

console = Console()
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
APP_NAME = "SMS RAPIDO - Honduras"


def cargar_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def guardar_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def setup_android_server():
    console.print()
    console.print(Panel.fit(
        "[bold cyan]CONFIGURAR ANDROID (Termux server)[/bold cyan]\n\n"
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
    cfg = cargar_config().get("android_server", {})
    ip = cfg.get("ip", "")
    port = cfg.get("port", 8080)
    if not ip:
        return False, "Android no configurado"
    url = f"http://{ip}:{port}"
    try:
        resp = requests.post(url, json={"to": numero, "message": mensaje}, timeout=20)
        data = resp.json()
        if data.get("success"):
            return True, "SMS enviado desde tu Android"
        return False, data.get("error", "Error del servidor Termux")
    except requests.exceptions.ConnectionError:
        return False, f"No conecta a [bold]{url}[/bold]\nVerifica que Termux corra el servidor y esten en la misma red"
    except Exception as e:
        return False, str(e)


ENVIADORES = {"android_server": enviar_android_server}

PROVEEDORES = [("android_server", "Android (Termux server)", "WiFi/hotspot, servidor Python")]


def main():
    console.print()
    console.print(Panel.fit(
        f"[bold green]{APP_NAME}[/bold green]\n"
        "[dim]Envia SMS usando tu Android como puerta de enlace[/dim]",
        border_style="green"
    ))

    while True:
        console.print()
        console.print("[bold cyan] MENU [/bold cyan]")
        console.print("  [bold green]1[/bold green] Enviar SMS")
        console.print("  [bold green]2[/bold green] Configurar/conectar Android")
        console.print("  [bold green]3[/bold green] Salir")
        console.print()

        opcion = console.input("[cyan]Selecciona (1-3):[/cyan] ").strip()

        if opcion == "1":
            cfg = cargar_config().get("android_server", {})
            if not cfg.get("ip"):
                console.print("[red]Primero configura el Android (opcion 2)[/red]")
                continue

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

            console.print(f"\n[yellow]Enviando via ANDROID...[/yellow]")
            ok, info = enviar_android_server(numero, mensaje)

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
            console.print("\n[green]Chao![/green]")
            break
        else:
            console.print("[red]Opcion no valida.[/red]")

        console.print()
        input("Presiona ENTER para continuar...")


if __name__ == "__main__":
    main()
