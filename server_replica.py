import socket
import time
import multiprocessing
import sys
import os

# Importa módulos e variáveis globais do servidor original
from server import (
    get_ntp_offset,
    udp_announcer_process,
    start_tcp_server,
    TCP_PORT,
    UDP_PORT,
    HOST
)

PRIMARY_HOST = "127.0.0.1"  # IP do servidor principal

def is_primary_alive():
    try:
        # Tenta estabelecer uma conexão TCP rápida com o servidor principal
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2.0)
        sock.connect((PRIMARY_HOST, TCP_PORT))
        sock.close()
        return True
    except Exception:
        return False

def main():
    print("=== RÉPLICA DO SERVIDOR ===")
    print(f"[REPLICA] Monitorando o servidor principal em {PRIMARY_HOST}:{TCP_PORT}...")

    # Monitora o servidor principal até que ele caia
    primary_was_alive = False
    while True:
        alive = is_primary_alive()
        if alive:
            if not primary_was_alive:
                print("[REPLICA] Servidor principal detectado como ATIVO. Em espera (standby)...")
                primary_was_alive = True
        else:
            if primary_was_alive:
                print("\n[REPLICA] ATENÇÃO: Servidor principal caiu! Assumindo o controle...")
                break
            else:
                print("[REPLICA] Servidor principal inativo. Assumindo o controle...")
                break
        time.sleep(2)

    # Inicia o servidor réplica assumindo a porta e o serviço
    offset = get_ntp_offset()
    print(f"[REPLICA] Offset NTP obtido: {offset}s")

    # Inicia o processo de anúncio UDP para descoberta
    udp = multiprocessing.Process(
        target=udp_announcer_process,
        args=(TCP_PORT, UDP_PORT),
        daemon=True
    )
    udp.start()
    print("[REPLICA] Anúncio de descoberta UDP iniciado.")

    # Inicia o servidor TCP principal na porta padrão
    start_tcp_server(offset)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[REPLICA] Encerrando réplica...")
        sys.exit(0)
