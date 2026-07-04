# Documentação Técnica: Aplicação de Chat Distribuído

## 1. Introdução

Este documento detalha o desenvolvimento de uma aplicação de chat distribuído em Python, concebida para ilustrar e aplicar os princípios fundamentais dos Sistemas Distribuídos. A aplicação consiste num servidor central e múltiplos clientes, permitindo a comunicação em tempo real entre os utilizadores. O objetivo principal é demonstrar a implementação prática de conceitos como concorrência, ausência de relógio global, recursos compartilhados, **transparência de localização** e tolerância a falhas (parcial), utilizando protocolos de comunicação como TCP e UDP, e sincronização de tempo via NTP. Esta versão aprimorada incorpora o uso explícito de **processos** e **threads** para gerenciar a concorrência e a modularidade.

## 2. Arquitetura do Sistema

A arquitetura da aplicação é baseada num modelo cliente-servidor, onde um servidor central gerencia as conexões e o fluxo de mensagens entre os clientes. A modularidade é alcançada através da utilização de processos e threads para diferentes funcionalidades.

### 2.1. Servidor Central (`server.py`)

O servidor é o componente principal do sistema, responsável por:

*   **Gestão de Conexões (TCP)**: Aceita e mantém conexões TCP persistentes com múltiplos clientes, utilizando **threads** para lidar com cada cliente concorrentemente.
*   **Roteamento de Mensagens**: Recebe mensagens de um cliente e as retransmite para todos os outros clientes conectados (broadcast).
*   **Gestão de Estado**: Mantém uma lista de clientes ativos, incluindo seus endereços e nomes de utilizador, protegida por um lock de thread.
*   **Sincronização de Tempo**: Atua como cliente NTP para sincronizar seu próprio relógio com servidores de tempo públicos, garantindo que os timestamps das mensagens sejam consistentes.
*   **Anúncio de Serviço (UDP)**: Um **processo** separado utiliza UDP para anunciar a presença do servidor na rede, facilitando a descoberta por parte dos clientes (Transparência de Localização).

### 2.2. Clientes (`client.py`)

Os clientes são as interfaces através das quais os utilizadores interagem com o sistema de chat. Cada cliente é responsável por:

*   **Descoberta de Servidor (UDP)**: Utiliza UDP para descobrir automaticamente o endereço IP e a porta TCP do servidor na rede local.
*   **Conexão ao Servidor (TCP)**: Estabelece uma conexão TCP com o servidor central.
*   **Envio e Recebimento de Mensagens**: Permite que o utilizador digite e envie mensagens, e exibe as mensagens recebidas de outros utilizadores. A recepção de mensagens ocorre numa **thread** dedicada.
*   **Sincronização de Tempo**: Atua como cliente NTP para sincronizar seu próprio relógio, contribuindo para a consistência global dos eventos.

## 3. Características de Sistemas Distribuídos Implementadas

A aplicação demonstra as seguintes características essenciais de Sistemas Distribuídos:

### 3.1. Concorrência

O servidor é projetado para lidar com múltiplas requisições de clientes simultaneamente. Cada nova conexão TCP de um cliente resulta na criação de uma **nova thread** (`handle_client`) no servidor. Esta thread é dedicada a gerenciar a comunicação com aquele cliente específico, permitindo que o servidor aceite novas conexões e processe mensagens de outros clientes em paralelo. Além disso, o processo de anúncio UDP roda em um **processo separado (`multiprocessing.Process`)**, demonstrando a concorrência em um nível mais alto de abstração, onde diferentes funcionalidades do servidor são isoladas em unidades de execução independentes.

### 3.2. Ausência de Relógio Global

Em um sistema distribuído, cada máquina possui seu próprio relógio físico, que pode divergir dos relógios de outras máquinas. A aplicação aborda isso utilizando o **Protocolo de Tempo de Rede (NTP)**. Tanto o servidor quanto cada cliente sincronizam seus relógios independentemente com servidores NTP públicos (`pool.ntp.org`). Embora não haja um relógio global único e perfeitamente sincronizado, o NTP minimiza a diferença de tempo entre os componentes, permitindo que os timestamps das mensagens sejam razoavelmente consistentes e úteis para ordenar eventos.

### 3.3. Recursos Compartilhados

O servidor gerencia recursos que são acessados e modificados por múltiplos componentes. O principal recurso compartilhado é a lista de **clientes conectados** (`clients`). Para garantir a integridade e a consistência deste recurso em um ambiente concorrente (com múltiplas threads acessando-o), é utilizado um **lock de thread (`threading.Lock`)**. Isso previne condições de corrida e garante que apenas uma thread por vez possa modificar a lista de clientes, evitando dados inconsistentes ou corrompidos.

### 3.4. Transparência de Localização

A aplicação demonstra a transparência de localização através do mecanismo de descoberta de serviço via UDP. Os clientes não precisam saber o endereço IP ou a porta TCP exata do servidor antecipadamente. Em vez disso, eles utilizam um mecanismo de broadcast UDP para "descobrir" o servidor na rede local. O servidor, por sua vez, anuncia sua presença periodicamente. Isso abstrai a localização física do servidor dos clientes, tornando o sistema mais flexível e fácil de usar, pois o cliente pode se conectar ao servidor sem configuração manual de endereço.

### 3.5. Tolerância a Falhas (Parcial)

Se um cliente se desconectar abruptamente (por exemplo, devido a uma falha de rede ou encerramento inesperado), o servidor deteta essa desconexão (`ConnectionResetError` ou `if not data` no `recv`) e remove o cliente da lista de ativos. A falha de um cliente individual não causa a falha do servidor ou de outros clientes, permitindo que o sistema continue a operar. No entanto, a falha do processo principal do servidor resultaria na interrupção do serviço para todos os clientes, indicando uma tolerância a falhas parcial e não completa.

## 4. Implementação Técnica

### 4.1. Comunicação TCP

O protocolo **TCP (Transmission Control Protocol)** é utilizado para a comunicação principal entre o servidor e os clientes. O TCP oferece uma comunicação orientada à conexão, confiável e ordenada, o que é crucial para um sistema de chat onde a perda ou a desordem de mensagens é inaceitável. Cada cliente estabelece uma conexão TCP persistente com o servidor, através da qual as mensagens são enviadas e recebidas.

### 4.2. Comunicação UDP

O protocolo **UDP (User Datagram Protocol)** é utilizado de forma funcional para a descoberta de serviço. O servidor executa um **processo separado (`udp_announcer_process`)** que envia mensagens de broadcast UDP periodicamente, anunciando seu serviço e porta TCP. Os clientes, por sua vez, escutam essas mensagens UDP para localizar o servidor automaticamente antes de tentar uma conexão TCP. Isso demonstra o uso do UDP para comunicação não confiável e sem conexão, ideal para tarefas como descoberta de serviços onde a velocidade e a simplicidade são prioritárias.

### 4.3. Sincronização NTP

A biblioteca `ntplib` é utilizada para implementar a sincronização de tempo. Tanto o servidor quanto os clientes fazem requisições a servidores NTP públicos (`pool.ntp.org`) para obter o `offset` (diferença) entre o seu relógio local e o tempo de referência. Este `offset` é então aplicado ao `datetime.datetime.now()` para obter um tempo "sincronizado" que é usado para timestamping de mensagens, minimizando as discrepâncias de tempo entre os nós.

### 4.4. Multiprocessing e Multithreading

*   **Multiprocessing**: O servidor utiliza o módulo `multiprocessing` para criar um processo separado (`udp_announcer_process`) para lidar com o anúncio UDP. Isso garante que a funcionalidade de descoberta de serviço seja isolada e possa operar independentemente do servidor TCP principal, melhorando a robustez e a modularidade.
*   **Multithreading**: O módulo `threading` do Python é empregado no servidor para gerenciar a concorrência das conexões TCP. Cada vez que um novo cliente se conecta, uma nova thread (`handle_client`) é criada para lidar com a comunicação específica desse cliente. Isso permite que o servidor atenda a múltiplos clientes em paralelo, sem bloquear a thread principal ou a comunicação com outros clientes. Nos clientes, uma thread dedicada (`receive_messages`) é usada para receber mensagens do servidor de forma assíncrona, permitindo que o utilizador continue a digitar e enviar mensagens.

## 5. Estrutura do Código

```
. 
├── README.md
├── server.py
├── client.py
├── requirements.txt
├── test_app.py
└── DOCUMENTACAO_TECNICA.md
```

### 5.1. `server.py`

*   **`TCP_PORT`, `UDP_PORT`, `HOST`**: Configurações de rede.
*   **`clients`, `clients_lock`**: Dicionário para armazenar clientes conectados e um lock para acesso seguro.
*   **`get_ntp_offset()`**: Função para obter o offset NTP.
*   **`udp_announcer_process(tcp_port, udp_port)`**: Função que roda em um processo separado para enviar broadcasts UDP do servidor.
*   **`broadcast(message, sender_addr=None)`**: Envia mensagens para todos os clientes conectados, exceto o remetente.
*   **`handle_client(conn, addr, offset)`**: Função executada em uma thread separada para cada cliente TCP, gerencia o recebimento e retransmissão de mensagens.
*   **`start_tcp_server(offset)`**: Loop principal que aceita novas conexões TCP e inicia threads para cada uma.
*   **`if __name__ == "__main__"`**: Bloco principal que inicia a sincronização NTP, o processo UDP e o servidor TCP.

### 5.2. `client.py`

*   **`UDP_PORT`**: Porta UDP para descoberta de servidor.
*   **`get_ntp_offset()`**: Função para obter o offset NTP.
*   **`discover_server()`**: Função que utiliza UDP para encontrar o servidor na rede.
*   **`receive_messages(sock, offset)`**: Thread que escuta e imprime mensagens recebidas do servidor.
*   **`start_client()`**: Função principal que solicita o nome do utilizador, realiza a descoberta UDP, conecta ao servidor via TCP, envia o nome e inicia a thread de recebimento, permitindo ao utilizador enviar mensagens.

### 5.3. `requirements.txt`

Lista as dependências Python necessárias para o projeto:

*   `ntplib`

### 5.4. `test_app.py`

Script para testar a funcionalidade básica do servidor e clientes, incluindo a descoberta UDP e a comunicação TCP.

## 6. Como Executar

1.  **Instalar Dependências**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Iniciar o Servidor**:
    Abra um terminal e execute:
    ```bash
    python server.py
    ```
    O servidor iniciará o processo de anúncio UDP e o servidor TCP.

3.  **Iniciar Clientes**:
    Abra terminais separados para cada cliente e execute:
    ```bash
    python client.py
    ```
    Cada cliente tentará descobrir o servidor via UDP. Se não encontrar, pedirá para digitar o IP manualmente. Em seguida, solicitará um nome de utilizador.

## 7. Conclusão

Esta aplicação de chat distribuído serve como uma demonstração abrangente dos conceitos de Sistemas Distribuídos. Através da concorrência (multiprocessing e multithreading), da sincronização de tempo (NTP), da gestão de recursos compartilhados, da transparência de localização (descoberta UDP) e de uma forma básica de tolerância a falhas, o projeto ilustra como esses princípios são aplicados para construir sistemas robustos, responsivos e modulares. A utilização de TCP para comunicação confiável e UDP para descoberta de serviço complementam a demonstração dos protocolos de rede essenciais, atendendo a todos os requisitos propostos.
