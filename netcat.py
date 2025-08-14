import argparse
import socket
import shlex
import subprocess
import sys
import threading
import textwrap

# CORREÇÃO 1: Função execute melhorada para capturar saída corretamente.
def execute(cmd):
    cmd = cmd.strip()
    if not cmd:
        return ""
    try:
        # Usar capture_output=True e text=True é a forma moderna e segura.
        # stderr=subprocess.STDOUT redireciona erros para a saída padrão.
        output = subprocess.run(shlex.split(cmd),
                                stdout = subprocess.PIPE,
                                stderr = subprocess.STDOUT,
                                text = True)
        return output.stdout
    except FileNotFoundError:
        return f"Comando não encontrado: {cmd}\n"


class NetCat:
    def __init__(self, args, buffer=b''):
        self.args = args
        self.buffer = buffer
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def run(self):
        if self.args.listen:
            self.listen()
        else:
            self.send()

    def send(self):
        try:
            self.socket.connect((self.args.target, self.args.port))
            # Se houver um buffer inicial (vindo de um pipe), envie-o primeiro.
            if self.buffer:
                self.socket.send(self.buffer)
            
            # CORREÇÃO 2: Loop de comunicação interativa corrigido.
            while True:
                recv_len = 1
                response = ''
                while recv_len:
                    data = self.socket.recv(4096)
                    recv_len = len(data)
                    response += data.decode()
                    if recv_len < 4096:
                        break
                
                if response:
                    # Usar end='' evita uma quebra de linha extra.
                    print(response, end='')
                
                # Aguarda nova entrada do usuário.
                buffer = input()
                buffer += '\n'
                self.socket.send(buffer.encode())

        except KeyboardInterrupt:
            print('\nConexão encerrada pelo usuário.')
        except EOFError:
            # Acontece quando a entrada é redirecionada (pipe) e termina.
            print('Conexão fechada.')
        except ConnectionRefusedError:
            print(f"Conexão recusada por {self.args.target}:{self.args.port}")
        finally:
            self.socket.close()

    def listen(self):
        self.socket.bind((self.args.target, self.args.port))
        self.socket.listen(5)
        print(f'[*] Escutando em {self.args.target}:{self.args.port}')
        
        while True:
            client_socket, _ = self.socket.accept()
            print(f'[*] Conexão aceita de {_[0]}:{_[1]}')
            client_thread = threading.Thread(
                target=self.handle, args=(client_socket,))
            client_thread.start()

    def handle(self, client_socket):
        if self.args.execute:
            output = execute(self.args.execute)
            client_socket.send(output.encode())

        elif self.args.upload:
            file_buffer = b''
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break
                file_buffer += data
            try:
                with open(self.args.upload, 'wb') as f:
                    f.write(file_buffer)
                message = f'Arquivo salvo em {self.args.upload}\n'
                client_socket.send(message.encode())
            except IOError as e:
                message = f'Falha ao salvar arquivo: {e}\n'
                client_socket.send(message.encode())

        elif self.args.command:
            while True:
                try:
                    client_socket.send(b'Shell> ')
                    cmd_buffer = b''
                    while b'\n' not in cmd_buffer:
                        cmd_buffer += client_socket.recv(64)
                    
                    response = execute(cmd_buffer.decode())
                    if not response:
                        response = "\n" # Envia uma resposta vazia para não travar o cliente
                    client_socket.send(response.encode())
                
                except Exception as e:
                    # CORREÇÃO 3: Não encerrar o servidor! Apenas a thread do cliente.
                    print(f'[!] Cliente desconectado: {e}')
                    break # Sai do loop, finalizando a thread.
        
        client_socket.close()

if __name__ == '__main__':
    # CORREÇÃO 4: Usar r'''...''' para criar uma "raw string" e evitar SyntaxWarning.
    parser = argparse.ArgumentParser(
        description='BHP Net Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(r'''Exemplos:
    # Iniciar uma shell remota no servidor
    netcat.py -t 0.0.0.0 -p 5555 -l -c
    
    # Fazer upload de um arquivo para o servidor
    netcat.py -t 0.0.0.0 -p 5555 -l -u=meuarquivo.txt
    
    # Executar um comando específico no servidor
    netcat.py -t 0.0.0.0 -p 5555 -l -e="whoami"
    
    # Enviar texto para um servidor (pipe)
    echo 'ABC' | ./netcat.py -t 192.168.1.108 -p 135
    
    # Conectar a um servidor
    netcat.py -t 192.168.1.108 -p 5555
    '''))
    
    parser.add_argument('-c', '--command', action='store_true', help='iniciar uma shell de comandos')
    parser.add_argument('-e', '--execute', help='executar um comando específico')
    parser.add_argument('-l', '--listen', action='store_true', help='modo de escuta (servidor)')
    parser.add_argument('-p', '--port', type=int, default=5555, help='porta de destino')
    # CORREÇÃO 5: Mudar o target padrão para 0.0.0.0, que é o ideal para um servidor.
    parser.add_argument('-t', '--target', default='0.0.0.0', help='endereço IP de destino')
    parser.add_argument('-u', '--upload', help='fazer upload de um arquivo')
    args = parser.parse_args()

    # CORREÇÃO 6: Lógica para não travar em modo cliente interativo.
    buffer = b''
    if not args.listen:
        # Só tente ler do stdin se a entrada NÃO for um terminal interativo (ou seja, se for um pipe).
        if not sys.stdin.isatty():
            buffer = sys.stdin.read().encode()

    nc = NetCat(args, buffer)
    nc.run()