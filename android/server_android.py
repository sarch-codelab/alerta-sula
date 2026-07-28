import json
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

HOST = "0.0.0.0"
PORT = 8080


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


if __name__ == "__main__":
    print(f"\nServidor SMS Android iniciado en puerto {PORT}")
    print(f"Asegurate que el PC y el telefono esten en la misma red WiFi")
    print(f"\nEn el PC configura la IP que aparece abajo como 'Android IP'")
    print(f"\nEsperando peticiones...\n")
    server = HTTPServer((HOST, PORT), SMSHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
        server.server_close()