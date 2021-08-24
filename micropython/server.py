import socket
import sys
import time
import json
import struct

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
        if module == 69: #Module E on this reflector is a Parrot only send back to sender
            sock.sendto(data,clients[address]["addr"])
        else:
            for x in modules[module]:
                if(x != address): #Only send voice to others do back to sender
                    sock.sendto(data,clients[x]["addr"])
    elif magic == b"INFO": #Custom magic used by status page to get info from ESP32 reflector. This is still under development.
        data = json.dumps(clients)
        sock.sendto(data.encode("ASCII"),addr)
    else:
        print(data.decode()) #If some odd magic shows up, log it out.
    
    
    
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

def decodeCallsign(x):
    unpacked = struct.unpack(">HI",x)
    q = (unpacked[0]<<(8*4))+unpacked[1]  
    call = ""
    while q > 0:
        call += " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-/."[q%40]
        q = q //40
    return call

def run():
    init()   
    while True:
        handleUDP()
        
