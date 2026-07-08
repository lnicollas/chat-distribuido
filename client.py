import socket
import threading
import json
import time

UDP_PORT = 65433


def recv(state):
    while state["running"]:
        try:
            raw = state["sock"].recv(1024)
            if not raw:
                raise ConnectionError()
            
            data = json.loads(raw.decode())

            if data["type"] == "message":
                print(f"\n[{data['time']}] {data['from']}: {data['text']}")

            elif data["type"] == "system":
                print(f"\n[SYSTEM] {data['msg']}")

            elif data["type"] == "users":
                print("\nUSUÁRIOS:", data["users"])

            print("> ", end="")

        except Exception:
            if not state["running"]:
                break
            
            print("\n[SYSTEM] Conexão perdida com o servidor. Tentando reconectar...")
            
            try:
                state["sock"].close()
            except:
                pass
            
            reconnected = False
            while state["running"]:
                host, port = discover()
                if host:
                    try:
                        new_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        new_sock.connect((host, port))
                        new_sock.send(json.dumps({
                            "name": state["name"]
                        }).encode())
                        state["sock"] = new_sock
                        reconnected = True
                        break
                    except Exception:
                        pass
                time.sleep(2)
            
            if reconnected:
                print("[SYSTEM] Reconectado com sucesso ao servidor!")
                print("> ", end="")
            else:
                if not state["running"]:
                    break
                print("[SYSTEM] Não foi possível reconectar. Saindo...")
                state["running"] = False
                break


def discover():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", UDP_PORT))
    sock.settimeout(5)

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
    try:
        sock.connect((host, port))
    except Exception as e:
        print(f"Não foi possível conectar ao servidor: {e}")
        return

    name = input("nome: ")

    try:
        sock.send(json.dumps({
            "name": name
        }).encode())
    except:
        print("Erro de comunicação inicial.")
        return

    state = {
        "sock": sock,
        "name": name,
        "running": True,
        "host": host,
        "port": port
    }

    threading.Thread(target=recv, args=(state,), daemon=True).start()

    while state["running"]:
        try:
            msg = input("> ")
        except (KeyboardInterrupt, EOFError):
            break

        if not state["running"]:
            break

        if msg == "/quit":
            state["running"] = False
            try:
                state["sock"].send(json.dumps({
                    "type": "command",
                    "cmd": "quit"
                }).encode())
            except:
                pass
            break

        elif msg == "/users":
            try:
                state["sock"].send(json.dumps({
                    "type": "command",
                    "cmd": "users"
                }).encode())
            except:
                print("\n[SYSTEM] Não foi possível enviar o comando. Tentando reconectar...")

        else:
            try:
                state["sock"].send(json.dumps({
                    "type": "message",
                    "text": msg
                }).encode())
            except:
                print("\n[SYSTEM] Não foi possível enviar a mensagem. Tentando reconectar...")

    try:
        state["sock"].close()
    except:
        pass


if __name__ == "__main__":
    main()     