import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import socket
import threading
import json
import datetime
import time
import queue
import sys

# ============================================================================
# CONSTANTES
# ============================================================================
UDP_PORT = 65433
TCP_PORT = 65432
DISCOVERY_TIMEOUT = 3.0

# ============================================================================
# FUNÇÕES DE REDE (mesmas do original)
# ============================================================================

def discover():
    """Descobre o servidor via UDP broadcast."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", UDP_PORT))
    sock.settimeout(DISCOVERY_TIMEOUT)
    try:
        data, addr = sock.recvfrom(2048)
        info = json.loads(data.decode())
        return addr[0], info.get("port", TCP_PORT)
    except Exception:
        return None, None
    finally:
        sock.close()

def connect_to_server(host, port, name):
    """Conecta ao servidor TCP e envia o nome."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((host, port))
        sock.settimeout(None)  # bloqueante
        sock.send(json.dumps({"name": name}).encode())
        return sock
    except Exception as e:
        raise e

# ============================================================================
# CLASSE PRINCIPAL DA INTERFACE
# ============================================================================

class ChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("💬 Chat Bate Papo")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)

        # Variáveis de estado
        self.name = ""
        self.host = ""
        self.port = TCP_PORT
        self.sock = None
        self.connected = False
        self.reconnecting = False
        self.running = False
        self.users = []
        self.messages = []

        # Fila para comunicação entre thread e GUI
        self.queue = queue.Queue()

        # Cores e estilos
        self.bg_color = "#f0f2f5"
        self.primary_color = "#007bff"
        self.secondary_color = "#6c757d"
        self.font_family = "Segoe UI, sans-serif"

        self.root.configure(bg=self.bg_color)

        # Inicia com a tela de login
        self.show_login()

        # Configura fechamento seguro
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # ------------------- MÉTODOS DE UI -------------------

    def clear_window(self):
        """Remove todos os widgets da janela."""
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_login(self):
        """Exibe a tela de login."""
        self.clear_window()
        self.root.geometry("500x450")
        self.root.minsize(400, 350)

        # Frame centralizado
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(expand=True, fill="both", padx=30, pady=30)

        # Título
        title = tk.Label(main_frame, text="💬 Chat Bate papo", font=(self.font_family, 24, "bold"),
                         bg=self.bg_color, fg="#1a1a2e")
        title.pack(pady=(0, 5))

        subtitle = tk.Label(main_frame, text="Converse com quem quiser", font=(self.font_family, 10),
                            bg=self.bg_color, fg=self.secondary_color)
        subtitle.pack(pady=(0, 20))

        # Formulário
        form = tk.Frame(main_frame, bg=self.bg_color)
        form.pack(fill="x", pady=10)

        # Nome
        tk.Label(form, text="Seu nome:", bg=self.bg_color, font=(self.font_family, 10, "bold"),
                 anchor="w").pack(fill="x", pady=(0, 2))
        self.name_entry = tk.Entry(form, font=(self.font_family, 12), bd=2, relief="groove")
        self.name_entry.pack(fill="x", pady=(0, 10))
        self.name_entry.focus()

        # Opção de descoberta
        self.discovery_var = tk.BooleanVar(value=True)
        

        # Frame para IP/Porta manual
        self.manual_frame = tk.Frame(form, bg=self.bg_color)
        self.manual_frame.pack(fill="x", pady=(0, 10))
        self.manual_frame.pack_forget()  # escondido inicialmente

        tk.Label(self.manual_frame, text="IP do servidor:", bg=self.bg_color,
                 font=(self.font_family, 10)).grid(row=0, column=0, sticky="w", pady=(0, 2))
        self.ip_entry = tk.Entry(self.manual_frame, font=(self.font_family, 12), bd=2, relief="groove")
        self.ip_entry.grid(row=1, column=0, sticky="ew", pady=(0, 5))
        self.ip_entry.insert(0, "127.0.0.1")

        tk.Label(self.manual_frame, text="Porta:", bg=self.bg_color,
                 font=(self.font_family, 10)).grid(row=2, column=0, sticky="w", pady=(0, 2))
        self.port_entry = tk.Entry(self.manual_frame, font=(self.font_family, 12), bd=2, relief="groove")
        self.port_entry.grid(row=3, column=0, sticky="ew", pady=(0, 5))
        self.port_entry.insert(0, str(TCP_PORT))

        self.manual_frame.columnconfigure(0, weight=1)

        # Botão conectar
        connect_btn = tk.Button(main_frame, text="🚀 Entrar no chat", font=(self.font_family, 12, "bold"),
                                bg=self.primary_color, fg="white", relief="flat", padx=20, pady=8,
                                command=self.do_connect)
        connect_btn.pack(pady=20, fill="x")

        # Status
        self.status_label = tk.Label(main_frame, text="", bg=self.bg_color, fg=self.secondary_color,
                                     font=(self.font_family, 9))
        self.status_label.pack()

    def toggle_manual(self):
        """Mostra ou esconde os campos manuais conforme o checkbox."""
        if self.discovery_var.get():
            self.manual_frame.pack_forget()
        else:
            self.manual_frame.pack(fill="x", pady=(0, 10))

    def show_chat(self):
        """Exibe a interface principal do chat."""
        self.clear_window()
        self.root.geometry("900x600")
        self.root.minsize(700, 450)

        # Layout principal: side bar (usuários) + chat
        main_panel = tk.Frame(self.root, bg=self.bg_color)
        main_panel.pack(fill="both", expand=True, padx=10, pady=10)

        # Barra lateral (usuários)
        sidebar = tk.Frame(main_panel, bg="#ffffff", width=200, relief="groove", bd=1)
        sidebar.pack(side="right", fill="y", padx=(10, 0))

        tk.Label(sidebar, text="👥 Online", font=(self.font_family, 12, "bold"),
                 bg="#ffffff", fg="#1a1a2e").pack(pady=(10, 5))

        self.user_listbox = tk.Listbox(sidebar, font=(self.font_family, 10), bg="#f8f9fa",
                                       relief="flat", highlightthickness=0)
        self.user_listbox.pack(fill="both", expand=True, padx=10, pady=5)

        # Área de chat
        chat_frame = tk.Frame(main_panel, bg="#ffffff", relief="groove", bd=1)
        chat_frame.pack(side="left", fill="both", expand=True)

        # Cabeçalho
        header = tk.Frame(chat_frame, bg="#ffffff", height=40)
        header.pack(fill="x", padx=10, pady=(5, 0))

        tk.Label(header, text=f"💬 Chat - {self.name}", font=(self.font_family, 12, "bold"),
                 bg="#ffffff").pack(side="left")

        self.chat_status_label = tk.Label(header, text="🟢 Conectado", font=(self.font_family, 9),
                                          fg="#28a745", bg="#ffffff")
        self.chat_status_label.pack(side="right")

        # Área de mensagens (com scroll)
        self.text_area = scrolledtext.ScrolledText(chat_frame, wrap="word", font=(self.font_family, 11),
                                                   bg="#f8f9fa", fg="#1a1a2e", relief="flat",
                                                   height=20)
        self.text_area.pack(fill="both", expand=True, padx=10, pady=10)
        self.text_area.config(state="disabled")

        # Frame de entrada
        input_frame = tk.Frame(chat_frame, bg="#ffffff")
        input_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.entry_msg = tk.Entry(input_frame, font=(self.font_family, 11), bd=2, relief="groove")
        self.entry_msg.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.entry_msg.bind("<Return>", lambda e: self.send_message())

        self.send_btn = tk.Button(input_frame, text="Enviar", font=(self.font_family, 10, "bold"),
                                  bg=self.primary_color, fg="white", relief="flat", padx=15,
                                  command=self.send_message)
        self.send_btn.pack(side="right")

        # Botão desconectar
        disconnect_btn = tk.Button(chat_frame, text="🚪 Desconectar", font=(self.font_family, 9),
                                   bg="#dc3545", fg="white", relief="flat", padx=10,
                                   command=self.do_disconnect)
        disconnect_btn.pack(side="bottom", pady=5, anchor="e", padx=10)

        # Inicia thread de recebimento
        self.start_receiver()

        # Solicita lista de usuários inicial
        self.send_command("users")

        # Atualiza a lista de usuários periodicamente
        self.update_users()

        # Processa a fila de mensagens
        self.process_queue()

    # ------------------- COMANDOS DA UI -------------------

    def do_connect(self):
        """Tenta conectar ao servidor."""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Aviso", "Digite um nome de usuário.")
            return

        self.name = name
        self.status_label.config(text="Conectando...", fg="#856404")

        try:
            if self.discovery_var.get():
                self.status_label.config(text="Descobrindo servidor...")
                host, port = discover()
                if not host:
                    messagebox.showerror("Erro", "Nenhum servidor encontrado via broadcast.\nTente digitar o IP manualmente.")
                    self.status_label.config(text="Falha na descoberta", fg="#dc3545")
                    return
                self.host = host
                self.port = port
            else:
                self.host = self.ip_entry.get().strip()
                try:
                    self.port = int(self.port_entry.get().strip())
                except ValueError:
                    messagebox.showerror("Erro", "Porta inválida.")
                    return

            self.status_label.config(text=f"Conectando a {self.host}:{self.port}...")
            self.sock = connect_to_server(self.host, self.port, self.name)
            self.connected = True
            self.running = True
            self.messages = []
            self.users = []

            # Limpa mensagens de status
            self.status_label.config(text="")
            self.show_chat()

        except Exception as e:
            messagebox.showerror("Erro de conexão", f"Não foi possível conectar:\n{str(e)}")
            self.status_label.config(text="Falha na conexão", fg="#dc3545")

    def send_message(self):
        """Envia uma mensagem ou comando."""
        if not self.connected or not self.sock:
            messagebox.showwarning("Aviso", "Você não está conectado.")
            return

        text = self.entry_msg.get().strip()
        if not text:
            return

        self.entry_msg.delete(0, tk.END)

        # Comandos especiais
        if text.startswith("/"):
            cmd = text[1:].strip().lower()
            if cmd == "quit":
                self.do_disconnect()
                return
            elif cmd == "users":
                self.send_command("users")
                return
            else:
                self.display_system_message(f"Comando desconhecido: /{cmd}")
                return

        # Mensagem normal
        try:
            self.sock.send(json.dumps({
                "type": "message",
                "text": text
            }).encode())
            # Adiciona localmente (feedback)
            self.messages.append({
                "type": "message",
                "from": self.name,
                "text": text,
                "time": datetime.datetime.now().isoformat(),
                "is_own": True
            })
            self.refresh_messages()
        except Exception as e:
            self.display_system_message(f"Erro ao enviar mensagem: {e}")
            self.handle_connection_loss()

    def send_command(self, cmd):
        """Envia um comando ao servidor."""
        try:
            self.sock.send(json.dumps({
                "type": "command",
                "cmd": cmd
            }).encode())
        except Exception:
            pass

    def do_disconnect(self):
        """Desconecta e volta para o login."""
        self.running = False
        self.connected = False
        self.reconnecting = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
        # Volta para tela de login
        self.show_login()

    def on_closing(self):
        """Finaliza a aplicação."""
        self.running = False
        self.connected = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        self.root.destroy()
        sys.exit(0)

    # ------------------- RECEPÇÃO DE MENSAGENS -------------------

    def start_receiver(self):
        """Inicia a thread que recebe dados do servidor."""
        if not self.connected:
            return
        self.running = True
        thread = threading.Thread(target=self.receiver_loop, daemon=True)
        thread.start()

    def receiver_loop(self):
        """Loop de recebimento (executa em thread separada)."""
        while self.running and self.connected:
            try:
                raw = self.sock.recv(4096)
                if not raw:
                    break
                data = json.loads(raw.decode())
                # Coloca na fila para processamento na GUI
                self.queue.put(data)
            except socket.error:
                break
            except json.JSONDecodeError:
                continue
            except Exception:
                continue

        # Se saiu do loop involuntariamente, trata a perda de conexão
        if self.running and self.connected:
            self.handle_connection_loss()
        else:
            self.queue.put({"type": "_disconnect"})

    def handle_connection_loss(self):
        """Trata a perda de conexão, iniciando o processo de reconexão."""
        if not self.reconnecting and self.connected:
            self.connected = False
            self.reconnecting = True
            if self.sock:
                try:
                    self.sock.close()
                except:
                    pass
            self.queue.put({"type": "_lost_connection"})

    def start_reconnect_thread(self):
        """Inicia a thread de reconexão."""
        thread = threading.Thread(target=self.reconnect_loop, daemon=True)
        thread.start()

    def reconnect_loop(self):
        """Tenta reconectar ao servidor de forma assíncrona."""
        time.sleep(1.0)  # Pequeno delay antes da primeira tentativa
        
        while self.running and self.reconnecting and not self.connected:
            host = self.host
            port = self.port
            
            if self.discovery_var.get():
                try:
                    disc_host, disc_port = discover()
                    if disc_host:
                        host = disc_host
                        port = disc_port
                except Exception:
                    pass
            
            if host:
                try:
                    sock = connect_to_server(host, port, self.name)
                    self.sock = sock
                    self.host = host
                    self.port = port
                    self.connected = True
                    self.reconnecting = False
                    self.queue.put({"type": "_reconnected"})
                    return
                except Exception:
                    pass
            
            time.sleep(2.0)

    def process_queue(self):
        """Processa eventos da fila na thread principal."""
        try:
            while True:
                data = self.queue.get_nowait()
                if data.get("type") == "_disconnect":
                    self.do_disconnect()
                    return
                elif data.get("type") == "_lost_connection":
                    self.handle_lost_connection_ui()
                elif data.get("type") == "_reconnected":
                    self.handle_reconnected_ui()
                else:
                    self.handle_server_data(data)
        except queue.Empty:
            pass
        finally:
            # Agenda nova verificação
            if self.connected or self.reconnecting:
                self.root.after(100, self.process_queue)

    def handle_lost_connection_ui(self):
        """Atualiza a UI para refletir a perda de conexão e inicia a reconexão."""
        if hasattr(self, "chat_status_label"):
            self.chat_status_label.config(text="⚠️ Conectando...", fg="#ffc107")
        if hasattr(self, "entry_msg"):
            self.entry_msg.config(state="disabled")
        if hasattr(self, "send_btn"):
            self.send_btn.config(state="disabled")
        self.display_system_message("Conexão perdida. Tentando reconectar...")
        self.start_reconnect_thread()

    def handle_reconnected_ui(self):
        """Atualiza a UI para refletir a reconexão com sucesso."""
        if hasattr(self, "chat_status_label"):
            self.chat_status_label.config(text="🟢 Conectado", fg="#28a745")
        if hasattr(self, "entry_msg"):
            self.entry_msg.config(state="normal")
        if hasattr(self, "send_btn"):
            self.send_btn.config(state="normal")
        self.display_system_message("Reconectado ao servidor com sucesso!")
        self.start_receiver()
        self.send_command("users")

    def handle_server_data(self, data):
        """Processa dados recebidos do servidor."""
        msg_type = data.get("type")

        if msg_type == "message":
            self.messages.append({
                "type": "message",
                "from": data.get("from", "?"),
                "text": data.get("text", ""),
                "time": data.get("time", datetime.datetime.now().isoformat()),
                "is_own": data.get("from") == self.name
            })
            self.refresh_messages()

        elif msg_type == "system":
            self.display_system_message(data.get("msg", ""))

        elif msg_type == "users":
            self.users = data.get("users", [])
            self.update_users()

    # ------------------- ATUALIZAÇÃO DA UI -------------------

    def refresh_messages(self):
        """Atualiza a área de texto com todas as mensagens."""
        self.text_area.config(state="normal")
        self.text_area.delete("1.0", tk.END)

        if not self.messages:
            self.text_area.insert(tk.END, "✨ Nenhuma mensagem ainda.\nSeja o primeiro a dizer olá!", "center")
        else:
            for msg in self.messages:
                if msg["type"] == "message":
                    sender = msg["from"]
                    text = msg["text"]
                    ts = msg.get("time", "")
                    try:
                        dt = datetime.datetime.fromisoformat(ts)
                        time_str = dt.strftime("%H:%M")
                    except:
                        time_str = ts[:5] if len(ts) >= 5 else ts

                    is_own = msg.get("is_own", False)

                    # Formata a linha
                    if is_own:
                        prefix = f"Você ({time_str}): "
                        tag = "own"
                    else:
                        prefix = f"{sender} ({time_str}): "
                        tag = "other"

                    self.text_area.insert(tk.END, prefix, tag)
                    self.text_area.insert(tk.END, f"{text}\n", "text")

                elif msg["type"] == "system":
                    self.text_area.insert(tk.END, f"  {msg['msg']}\n", "system")

        self.text_area.config(state="disabled")
        self.text_area.see(tk.END)

        # Configura tags de estilo
        self.text_area.tag_config("own", foreground="#007bff", font=(self.font_family, 10, "bold"))
        self.text_area.tag_config("other", foreground="#6c757d", font=(self.font_family, 10, "bold"))
        self.text_area.tag_config("text", font=(self.font_family, 11))
        self.text_area.tag_config("system", foreground="#856404", background="#fff3cd",
                                  font=(self.font_family, 9, "italic"))
        self.text_area.tag_config("center", justify="center", foreground="#adb5bd",
                                  font=(self.font_family, 10, "italic"))

    def display_system_message(self, msg):
        """Exibe uma mensagem de sistema."""
        self.messages.append({"type": "system", "msg": msg})
        self.refresh_messages()

    def update_users(self):
        """Atualiza a lista de usuários."""
        self.user_listbox.delete(0, tk.END)
        for user in self.users:
            if user != self.name:
                self.user_listbox.insert(tk.END, f"  {user}")
        # Adiciona o próprio com indicador
        self.user_listbox.insert(0, f"  {self.name} (você)")
        # Pode destacar
        self.user_listbox.itemconfig(0, foreground="#28a745")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClient(root)
    root.mainloop()