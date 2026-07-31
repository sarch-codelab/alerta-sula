import requests
import subprocess
import time
import json
import sys
import os

API_BASE = "https://alerta-sula-hn.vercel.app/api"
POLL_INTERVAL = 5


def send_sms(to, message):
    try:
        result = subprocess.run(
            ["termux-sms-send", "-n", to, message],
            capture_output=True, text=True, timeout=30
        )
        return result.returncode == 0, result.stderr if result.returncode != 0 else None
    except FileNotFoundError:
        return False, "termux-sms-send no encontrado. Instala: pkg install termux-api"
    except subprocess.TimeoutExpired:
        return False, "Timeout enviando SMS"


def poll_loop():
    print("\n+----------------------------+")
    print(":      N O V A   S M S       :")
    print(":  Modo Cloud (Vercel)       :")
    print("+----------------------------+")
    print(f"\nPolling {API_BASE}/sms-poll cada {POLL_INTERVAL}s")
    print("Esperando mensajes...\n")

    while True:
        try:
            resp = requests.get(f"{API_BASE}/sms-poll", timeout=10)
            data = resp.json()
            msg = data.get("message")
            if msg:
                mid = msg.get("id", "?")
                to = msg.get("to", "")
                text = msg.get("message", "")
                print(f"[{mid}] Enviando SMS a {to}...")
                ok, err = send_sms(to, text)
                if ok:
                    print(f"[{mid}] Entregado")
                else:
                    print(f"[{mid}] Fallo: {err}")
                try:
                    requests.post(f"{API_BASE}/sms-report", json={
                        "id": mid,
                        "success": ok,
                        "error": err
                    }, timeout=10)
                except Exception as e:
                    print(f"[{mid}] Error al reportar: {e}")
        except requests.exceptions.ConnectionError:
            print("[NOVA] Sin conexion a Vercel, reintentando...")
        except Exception as e:
            print(f"[NOVA] Error: {e}")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    wake_lock = None
    try:
        wake_lock = subprocess.Popen(
            ["termux-wake-lock"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception:
        pass

    try:
        poll_loop()
    except KeyboardInterrupt:
        print("\nDetenido.")
    finally:
        if wake_lock:
            try:
                subprocess.run(["termux-wake-unlock"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
