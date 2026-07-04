# Aplicação de Chat Distribuído

## Visão Geral
Este projeto consiste no desenvolvimento de uma aplicação de chat distribuído em Python, projetada para demonstrar os conceitos fundamentais de Sistemas Distribuídos. A aplicação será composta por um servidor central e múltiplos clientes, permitindo a comunicação em tempo real entre os utilizadores.

## Requisitos Técnicos

A aplicação deve atender aos seguintes requisitos:

1.  **Características de Sistemas Distribuídos**: Implementar e demonstrar pelo menos 4 (quatro) características de Sistemas Distribuídos, tais como:
    *   **Concorrência**: O servidor deve ser capaz de lidar com múltiplas conexões de clientes simultaneamente.
    *   **Ausência de Relógio Global**: Cada componente (servidor e clientes) terá seu próprio relógio, e a sincronização será tratada via NTP.
    *   **Recursos Compartilhados**: Mensagens de chat e a lista de utilizadores ativos serão recursos compartilhados gerenciados pelo servidor.
    *   **Tolerância a Falhas (parcial)**: A falha de um cliente individual não deve comprometer a operação do servidor ou de outros clientes.

2.  **Processos e/ou Threads**: Utilizar threads para gerenciar a concorrência no servidor, permitindo que ele atenda a vários clientes em paralelo.

3.  **Protocolos TCP ou UDP**: A comunicação principal entre clientes e servidor será realizada via **TCP** para garantir a entrega confiável das mensagens de chat. O **UDP** poderá ser explorado para funcionalidades secundárias ou de descoberta, se aplicável.

4.  **Protocolo de Sincronização NTP**: Implementar a sincronização de tempo utilizando o protocolo NTP para garantir que todos os componentes do sistema operem com um tempo coordenado.

## Arquitetura Proposta

### Servidor Central
*   Responsável por aceitar conexões de clientes, rotear mensagens e manter o estado dos utilizadores ativos.
*   Utilizará `socket` TCP para comunicação com os clientes.
*   Empregará `threading` para lidar com múltiplos clientes concorrentemente.
*   Atuará como cliente NTP para sincronizar seu próprio relógio e poderá fornecer timestamps sincronizados aos clientes.

### Clientes
*   Conectar-se-ão ao servidor central via `socket` TCP.
*   Permitirão que os utilizadores enviem e recebam mensagens de chat.
*   Atuarão como clientes NTP para sincronizar seus próprios relógios.

## Estrutura do Projeto

```
. 
├── README.md
├── server.py
├── client.py
├── ntp_client.py
└── requirements.txt
```

## Próximos Passos

1.  Implementar a funcionalidade básica do servidor (conexão TCP, multithreading).
2.  Implementar a funcionalidade básica do cliente (conexão TCP, envio/recebimento de mensagens).
3.  Integrar a sincronização NTP no servidor e nos clientes.
4.  Adicionar funcionalidades de chat (listagem de utilizadores, mensagens privadas, etc.).
5.  Testar e depurar a aplicação.
6.  Elaborar a documentação detalhada.
