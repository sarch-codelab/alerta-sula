import sys, socket, os, json, threading, time

BROADCAST_PORT = 8082
ANDROID_IP = ""
ANDROID_PORT = 8080
LAST_SEEN = 0
LOCK = threading.Lock()


def listen_for_android():
    global ANDROID_IP, ANDROID_PORT, LAST_SEEN
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(1)
    try:
        sock.bind(("0.0.0.0", BROADCAST_PORT))
    except OSError:
        pass
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            msg = json.loads(data.decode())
            if msg.get("type") == "sms_server":
                with LOCK:
                    ANDROID_IP = msg["ip"]
                    ANDROID_PORT = msg.get("port", 8080)
                    LAST_SEEN = time.time()
        except (socket.timeout, json.JSONDecodeError, KeyError):
            pass


def get_android_addr():
    with LOCK:
        if ANDROID_IP and (time.time() - LAST_SEEN) < 10:
            return ANDROID_IP, ANDROID_PORT
    return None, None


def handle_client(conn, addr):
    log(f"conn from {addr}")
    data = b""
    while True:
        chunk = conn.recv(4096)
        if not chunk:
            break
        data += chunk
        if len(data) > 65536:
            break
    target_ip, target_port = get_android_addr()
    if not target_ip:
        log(f"Error: No Android detectado")
        conn.close()
        return
    try:
        t = socket.socket()
        t.settimeout(30)
        t.connect((target_ip, target_port))
        t.sendall(data)
        resp = b""
        while True:
            chunk = t.recv(4096)
            if not chunk:
                break
            resp += chunk
        conn.sendall(resp)
        log(f"ok {len(resp)} bytes via {target_ip}:{target_port}")
    except Exception as e:
        log(f"Error: {e}")
    finally:
        conn.close()
        t.close()


def log(msg):
    p = os.environ.get("TEMP", ".") + "\\relay_debug.txt"
    with open(p, "a") as f:
        f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")


if __name__ == "__main__":
    listener_thread = threading.Thread(target=listen_for_android, daemon=True)
    listener_thread.start()

    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", 8081))
    s.listen(5)
    log("NOVA SMS Relay iniciado - esperando Android...")
    while True:
        c, a = s.accept()
        threading.Thread(target=handle_client, args=(c, a), daemon=True).start()
