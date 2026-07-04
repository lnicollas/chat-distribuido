import subprocess
import socket
import threading
import time
import json


SERVER_HOST = "127.0.0.1"
SERVER_PORT = 65432


# ---------------- SERVER ----------------
def run_server():
    return subprocess.Popen(
        ["python3", "server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )


# ---------------- CLIENT ----------------
class TestClient:
    def __init__(self, name):
        self.name = name
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.received = []

    def connect(self):
        self.sock.connect((SERVER_HOST, SERVER_PORT))

        self.sock.send(json.dumps({
            "name": self.name
        }).encode())

        threading.Thread(target=self.listen, daemon=True).start()

    def listen(self):
        while True:
            try:
                data = self.sock.recv(1024)
                if not data:
                    break
                msg = json.loads(data.decode())
                self.received.append(msg)
            except:
                break

    def send_message(self, text):
        self.sock.send(json.dumps({
            "type": "message",
            "text": text
        }).encode())

    def get_messages(self):
        return self.received

    def close(self):
        self.sock.close()


# ---------------- TEST ----------------
def test_system():
    print(" Iniciando teste do sistema distribuído...")

    server = run_server()
    time.sleep(2)

    # clientes
    alice = TestClient("Alice")
    bob = TestClient("Bob")

    alice.connect()
    bob.connect()

    time.sleep(2)

    # troca de mensagens
    alice.send_message("Olá Bob!")
    bob.send_message("Oi Alice!")

    time.sleep(2)

    # validações básicas
    alice_msgs = alice.get_messages()
    bob_msgs = bob.get_messages()

    print("\n Mensagens Alice:", alice_msgs)
    print("\n Mensagens Bob:", bob_msgs)

    # asserts simples
    assert any(m.get("type") == "message" for m in alice_msgs), "Alice não recebeu mensagens"
    assert any(m.get("type") == "message" for m in bob_msgs), "Bob não recebeu mensagens"

    print("\n Teste de broadcast OK")

    # cleanup
    alice.close()
    bob.close()
    server.terminate()

    print("Sistema finalizado")


if __name__ == "__main__":
    test_system()