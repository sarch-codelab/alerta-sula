import json
import subprocess
import sys
import socket
import threading
import time
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

HOST = "0.0.0.0"
PORT = 8080
BROADCAST_PORT = 8082
BROADCAST_INTERVAL = 3


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def broadcast_presence(stop_event):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(1)
    while not stop_event.is_set():
        try:
            ip = get_local_ip()
            msg = json.dumps({"type": "sms_server", "ip": ip, "port": PORT}).encode()
            sock.sendto(msg, ("255.255.255.255", BROADCAST_PORT))
        except Exception:
            pass
        stop_event.wait(BROADCAST_INTERVAL)
    sock.close()


class SMSHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/ping":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "port": PORT}).encode())
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(content_len)
        sys.stderr.write(f"[DEBUG] raw={raw!r}\n")
        body = json.loads(raw.decode("utf-8"))
        phone = body.get("to", "")
        message = body.get("message", "")

        if not phone or not message:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": "Faltan parametros"}).encode())
            return

        try:
            result = subprocess.run(
                ["termux-sms-send", "-n", phone, message],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True}).encode())
            else:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"success": False, "error": result.stderr}).encode())
        except FileNotFoundError:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": False,
                "error": "termux-sms-send no encontrado. Instala: pkg install termux-api"
            }).encode())
        except subprocess.TimeoutExpired:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": "Timeout"}).encode())

    def log_message(self, format, *args):
        sys.stderr.write(f"[SMS Server] {args[0]} {args[1]} {args[2]}\n")


def run_server(stop_event):
    server = HTTPServer((HOST, PORT), SMSHandler)
    print(f"\n+----------------------------+")
    print(f":       N O V A   S M S      :")
    print(f":  Servidor Android activo   :")
    print(f"+----------------------------+")
    print(f"\nPuerto: {PORT}  |  Broadcast: {BROADCAST_PORT} (c/{BROADCAST_INTERVAL}s)")
    print(f"IP actual: {get_local_ip()}")
    print("Esperando peticiones...\n")
    while not stop_event.is_set():
        server.timeout = 1
        server.handle_request()
    server.server_close()


if __name__ == "__main__":
    wake_lock = None
    try:
        wake_lock = subprocess.Popen(
            ["termux-wake-lock"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception:
        pass

    stop_event = threading.Event()
    broadcaster = threading.Thread(target=broadcast_presence, args=(stop_event,), daemon=True)
    broadcaster.start()

    while True:
        try:
            run_server(stop_event)
            break
        except OSError as e:
            print(f"[ERROR] {e}, reiniciando en 3s...")
            time.sleep(3)
        except KeyboardInterrupt:
            print("\nServidor detenido.")
            break

    if wake_lock:
        try:
            subprocess.run(["termux-wake-unlock"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
