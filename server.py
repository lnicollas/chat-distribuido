import socket
import threading
import multiprocessing
import datetime
import ntplib
import json
import time
import os
import signal
import sys

TCP_PORT = 65432
UDP_PORT = 65433
HOST = "0.0.0.0"

clients = {}
clients_lock = threading.Lock()
running = True


# ---------------- NTP ----------------
def get_ntp_offset():
    client = ntplib.NTPClient()
    try:
        response = client.request("pool.ntp.org", version=3)
        return response.offset
    except:
        return 0.0


# ---------------- UDP DISCOVERY ----------------
def udp_announcer_process(tcp_port, udp_port):
    print(f"[UDP] PID {os.getpid()} iniciando broadcast")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    while True:
        data = json.dumps({
            "type": "DISCOVERY",
            "service": "CHAT",
            "port": tcp_port
        }).encode()

        sock.sendto(data, ("<broadcast>", udp_port))
        time.sleep(5)


# ---------------- BROADCAST ----------------
def broadcast(payload, sender=None):
    msg = json.dumps(payload).encode()

    with clients_lock:
        dead = []

        for addr, c in clients.items():
            if addr == sender:
                continue
            try:
                c["conn"].sendall(msg)
            except:
                dead.append(addr)

        for d in dead:
            del clients[d]


# ---------------- CLIENT HANDLER ----------------
def handle_client(conn, addr, offset):
    try:
        data = json.loads(conn.recv(1024).decode())
        name = data.get("name", "anon")

        with clients_lock:
            clients[addr] = {"conn": conn, "name": name}

        broadcast({
            "type": "system",
            "msg": f"{name} entrou no chat"
        })

        while True:
            raw = conn.recv(1024)
            if not raw:
                break

            data = json.loads(raw.decode())
            msg_type = data.get("type")

            if msg_type == "message":
                timestamp = (
                    datetime.datetime.now() +
                    datetime.timedelta(seconds=offset)
                ).isoformat()

                broadcast({
                    "type": "message",
                    "from": name,
                    "text": data["text"],
                    "time": timestamp
                }, sender=addr)

            elif msg_type == "command":
                handle_command(data, conn, addr)

    except:
        pass
    finally:
        with clients_lock:
            if addr in clients:
                name = clients[addr]["name"]
                del clients[addr]

                broadcast({
                    "type": "system",
                    "msg": f"{name} saiu"
                })

        conn.close()


# ---------------- COMMANDS ----------------
def handle_command(data, conn, addr):
    cmd = data.get("cmd")

    with clients_lock:
        if cmd == "users":
            users = [c["name"] for c in clients.values()]
            conn.sendall(json.dumps({
                "type": "users",
                "users": users
            }).encode())


# ---------------- SERVER ----------------
def start_tcp_server(offset):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, TCP_PORT))
    server.listen()

    print(f"[TCP] rodando na porta {TCP_PORT}")

    def shutdown(sig, frame):
        global running
        running = False
        print("\n[SHUTDOWN] encerrando servidor...")
        server.close()
        os._exit(0)

    signal.signal(signal.SIGINT, shutdown)

    while running:
        try:
            conn, addr = server.accept()
            t = threading.Thread(
                target=handle_client,
                args=(conn, addr, offset),
                daemon=True
            )
            t.start()
        except:
            break


# ---------------- MAIN ----------------
if __name__ == "__main__":
    print("=== CHAT DISTRIBUÍDO ===")

    offset = get_ntp_offset()

    udp = multiprocessing.Process(
        target=udp_announcer_process,
        args=(TCP_PORT, UDP_PORT),
        daemon=True
    )
    udp.start()

    start_tcp_server(offset)