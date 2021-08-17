import socket
import sys
import time


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('0.0.0.0', 17000)


timeout = 60
pingTime = 10

modules = {}
clients = {}

def init():
    sock.bind(server_address)
    for x in range(65,91):
        modules[x] = set()



    
def handleUDP():
    now = time.time()
    data, addr = sock.recvfrom(56)
    magic = data[0:4]
    if magic == b"CONN":
        address = data[4:10]
        print("CONN ",address)
        module = data[10]
        modules[module].add(address)
        clients[address] = {}
        clients[address]["module"] = module
        clients[address]["pingTime"] = time.time()
        clients[address]["pinged"] = False
        clients[address]["addr"] = addr
        sock.sendto(b"ACKN",addr)
    elif magic == b"PONG":
        address = data[4:10]
        print("PONG ",address)
        clients[address]["pingTime"] = time.time()
        clients[address]["pinged"] = False
    elif magic == b"DISC":
        address = data[4:10]
        print("DISC ",address)
        module = clients[address]["module"]
        modules[module].discard(address)
        del clients[address]
        sock.sendto(b"DISC",addr)
    elif magic == b"M17 ":
        address = data[12:18]
        module = clients[address]["module"]
        for x in modules[module]:
            sock.sendto(data,clients[x]["addr"])
    elif magic == b"INFO":
        print(clients)
        print(modules)
    else:
        print(data.decode())
    
    
    
    for x in clients.keys():
        if now - clients[x]["pingTime"]  > timeout:
            print("TIMEOUT ",x)
            sock.sendto(b"DISC"+x,clients[x]["addr"])
            module = clients[x]["module"]
            modules[module].discard(x)
            del clients[x]
        elif now - clients[x]["pingTime"] > pingTime:
            if not clients[x]["pinged"]:
                clients[x]["pinged"] = True
                sock.sendto(b"PING"+x,clients[x]["addr"])
   
def run():
    init()   
    while True:
        handleUDP()
        
