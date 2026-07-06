import socket
import threading
import json

UDP_PORT = 65433


def recv(sock):
    while True:
        try:
            data = json.loads(sock.recv(1024).decode())

            if data["type"] == "message":
                print(f"\n[{data['time']}] {data['from']}: {data['text']}")

            elif data["type"] == "system":
                print(f"\n[SYSTEM] {data['msg']}")

            elif data["type"] == "users":
                print("\nUSUÁRIOS:", data["users"])

            print("> ", end="")

        except:
            break


def discover():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", UDP_PORT))
    sock.settimeout(10)

    try:
        data, addr = sock.recvfrom(2048)
        info = json.loads(data.decode())
        return addr[0], info["port"]
    except:
        return None, None


def main():
    host, port = discover()

    if not host:
        host = input("IP servidor: ")
        port = 65432

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    name = input("nome: ")

    sock.send(json.dumps({
        "name": name
    }).encode())

    threading.Thread(target=recv, args=(sock,), daemon=True).start()

    while True:
        msg = input("> ")

        if msg == "/quit":
            try:
                sock.send(json.dumps({
                    "type": "command",
                    "cmd": "quit"
                }).encode())
            except:
                pass
            break

        elif msg == "/users":
            sock.send(json.dumps({
                "type": "command",
                "cmd": "users"
            }).encode())

        else:
            sock.send(json.dumps({
                "type": "message",
                "text": msg
            }).encode())

    sock.close()


if __name__ == "__main__":
    main()  