import argparse
import socket
import shlex
import subprocess
import sys
import threading
import textwrap

'''
 Executes a command in the local shell and returns its output.
 This function is used by the server to run commands sent by the client
'''    
def execute(cmd):
    cmd = cmd.strip()
    if not cmd:
        return ""
    try:
        # shlex.split() safely splits the command string, handling quotes and arguments.
        # This prevents command injection vulnerabilities.
        # We redirect stderr to stdout to capture all output, including errors.
        output = subprocess.run(shlex.split(cmd),
                                stdout = subprocess.PIPE,
                                stderr = subprocess.STDOUT,
                                text = True)
        return output.stdout
    except FileNotFoundError:
        return f"Command not found: {cmd}\n"


class NetCat: # How creative, I know. I'm sorry.
    def __init__(self, args, buffer=b''):
        self.args = args
        self.buffer = buffer
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   # SO_REUSEADDR allows the socket to be reused immediately after it's closed.
                                                                            # This is useful for restarting the server without waiting for the OS to release the port.

    def run(self):
        if self.args.listen:
            self.listen()
        else:
            self.send()

    def send(self):
        try:
            self.socket.connect((self.args.target, self.args.port))
           
            if self.buffer:
                self.socket.send(self.buffer)
            # This is the main interactive loop for the client.
            while True:
                recv_len = 1
                response = ''
                while recv_len:
                    data = self.socket.recv(4096)
                    recv_len = len(data)
                    response += data.decode()
                    if recv_len < 4096:
                        break
                 # Continuously receive data until the server sends a smaller chunk
                if response:
                    # Print the server's response without an extra newline.
                    print(response, end='')
                    
                # Wait for new input from the user.
                buffer = input()
                buffer += '\n'
                self.socket.send(buffer.encode())

        except KeyboardInterrupt:
            print('\nConnection closed by the user.')
        except EOFError:
           
            print('Conection closed.')
        except ConnectionRefusedError:
            print(f"Conection refused by {self.args.target}:{self.args.port}")
        finally:
            self.socket.close()

    def listen(self):
        self.socket.bind((self.args.target, self.args.port))
        self.socket.listen(5)
        print(f'[*] Escutando em {self.args.target}:{self.args.port}')
        
        while True:
            client_socket, _ = self.socket.accept()
            print(f'[*] Conexão accepted from {_[0]}:{_[1]}')
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
                message = f'File saved in {self.args.upload}\n'
                client_socket.send(message.encode())
            except IOError as e:
                message = f'Errow while attempting to save file: {e}\n'
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
                        response = "\n"
                    client_socket.send(response.encode())
                
                except Exception as e:
                  
                    print(f'[!] Client disconnected: {e}')
                    break 
        
        client_socket.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='PyCat',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(r'''Exemplos:
    # Start remote shell
    netcat.py -t 0.0.0.0 -p 5555 -l -c
    
    # File upload
    netcat.py -t 0.0.0.0 -p 5555 -l -u=meuarquivo.txt
    
    # Execute a single specific command
    netcat.py -t 0.0.0.0 -p 5555 -l -e="whoami"
    
    # Send text to a server (pipe)
    echo 'ABC' | ./netcat.py -t 192.168.1.108 -p 135
    
    # Connect to the server
    netcat.py -t 192.168.1.108 -p 5555
    '''))
    
    parser.add_argument('-c', '--command', action='store_true', help='start a command shell')
    parser.add_argument('-e', '--execute', help='execute a specific command')
    parser.add_argument('-l', '--listen', action='store_true', help='listening mode (server)')
    parser.add_argument('-p', '--port', type=int, default=5555, help='desired port')
    parser.add_argument('-t', '--target', default='0.0.0.0', help='Host IP')
    parser.add_argument('-u', '--upload', help='file upload')
    args = parser.parse_args()

   
    buffer = b''
     # This logic prevents the client from hanging when run in an interactive terminal.
     # We only read from stdin if the input is being piped to the script.
    if not args.listen:
        
        if not sys.stdin.isatty():  # sys.stdin.isatty() returns False if input is piped
            buffer = sys.stdin.read().encode()

    nc = NetCat(args, buffer)
    nc.run()
