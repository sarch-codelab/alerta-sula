import sys, socket, os
log = os.environ.get("TEMP",".") + "\\relay_debug.txt"
s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("0.0.0.0", 8081))
s.listen(5)
with open(log, "w") as f: f.write("relay started\n")
while True:
    c, a = s.accept()
    with open(log, "a") as f: f.write(f"conn from {a}\n")
    d = b""
    while True:
        chunk = c.recv(4096)
        if not chunk: break
        d += chunk
        if len(d) > 65536: break
    try:
        t = socket.socket()
        t.settimeout(30)
        t.connect(("192.168.137.188", 8080))
        t.sendall(d)
        r = b""
        while True:
            chunk = t.recv(4096)
            if not chunk: break
            r += chunk
        c.sendall(r)
        with open(log, "a") as f: f.write(f"ok {len(r)} bytes\n")
    except Exception as e:
        with open(log, "a") as f: f.write(f"Error: {e}\n")
    finally:
        c.close(); t.close()
