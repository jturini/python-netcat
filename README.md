# PyNC - A Network tool in Python

![Python Version](https://img.shields.io/badge/python-3.x-blue.svg)

A network tool made in Python heavily inspired by `netcat`, created for study purposes in programming and sockets, network and cybersecurity. For now this project implements basic TCP functions, both client and server-side, allowing for remote command execution, file transfer, and the creation of reverse shells.

---

## About the project

This project came to life while reading the book "Black Hat Python" by Justin Seitz and Tim Arnold. The objetive here is to recreate some of the most important functionalities of `netcat` using only default libraries from Python, offering a good understanding of how network tools operate. 

## Current Functionalities:

-   **Server Mode (Listen)**: Listen to desired connections on a specific port.
-   **Client Mode**: Connects to a remote server.
-   **Remote Command Shell (`-c`)**: Starts a interactive shell on the server, accessible by the client.
-   **Command Execution (`-e`)**: Executes a single command on the server and returns the output to the client.
-   **File Upload (`-u`)**: Allows the client to send a file to the server.

---

## How to use

### Requirements

-   Python 3.x

### Examples of usage

Clone the repo:
```bash
git clone https://github.com/jturini/python-netcat.git
cd python-netcat
```

**1. Starting a server with a remote shell**

In your server (ex:Linux machine), define the host's address `ex: 0.0.0.0 /192.168.0.x` ,listen on the desired port (default is 5555).

```bash
python3 netcat.py -t 192.168.0.111 -l -c -p 5555
```
> Expected output: `[*] Listening on 192.168.0.111:5555`

**2. Connect to the server**

In the client machine, connect to the server's IP.

```bash
python3 netcat.py -t SERVER_IP -p 5555
```
> You will recieve the prompt `Shell> ` and may execute commands such as `whoami`, `ls`, `pwd`, etc.

**3. File Upload**

First, start the server in "upload mode":
```bash
# SERVER-SIDE
python3 netcat.py -l -u=your_file_here.txt -p 5555
```

After, send the file to the client:
```bash
# CLIENT-SIDE
python3 netcat.py -t SERVER_IP -p 5555 < file_to_send_here.txt
```

---

## Roadmap!!!!!

This will be a small personal project. The next planned functionalities are:

-   [ ] **UDP** support.
-   [ ] Allow for the usagege of **Cryptography SSL/TLS**.
-   [ ] Adding a **Port Scan**.
-   [ ] Improvements on the **logging system and overall verbose**.


## Special Thanks

-   The inspiration and the overall core of this project comes from the book "Black Hat Python" by Justin Seitz and Tim Arnold.
