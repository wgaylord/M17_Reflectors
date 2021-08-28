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

    data, addr = sock.recvfrom(56)

    now = time.time()
    magic = data[0:4]
    if magic == b"CONN":
        address = data[4:10]
#        print("CONN ",decode_callsign_base40(address))
        module = data[10]
        modules[module].add(address)
        clients[address] = {}
        clients[address]["module"] = module
        clients[address]["pingTime"] = time.time()
        clients[address]["pinged"] = False
        clients[address]["addr"] = addr
        clients[address]["talking"] = False
        sock.sendto(b"ACKN",addr)
    elif magic == b"PONG":
        address = data[4:10]
        if clients[address]["pinged"]: #Only care about a pong if we send a PING, work around for "dumb" clients that blindly PONG
#            print("PONG ",decode_callsign_base40(address))
            clients[address]["pingTime"] = time.time()
            clients[address]["pinged"] = False
            clients[address]["talking"] = False
            
    elif magic == b"DISC":
        address = data[4:10]
#        print("DISC ",decode_callsign_base40(address))
        module = clients[address]["module"]
        modules[module].discard(address)
        del clients[address]
        sock.sendto(b"DISC",addr)
    elif magic == b"M17 ":
        address = data[12:18]
        module = clients[address]["module"]
        clients[address]["talking"] = True
        if module == 69:
            sock.sendto(data,clients[address]["addr"])
        else:
            for x in modules[module]:
                if(x != address):
                    sock.sendto(data,clients[x]["addr"])
    elif magic == b"INFO":
        temp = {}
        for x in clients.keys():
            temp[decode_callsign_base40(x)] = {}
            temp[decode_callsign_base40(x)]["module"] = chr(clients[x]["module"])
            temp[decode_callsign_base40(x)]["talking"] = clients[x]["talking"]
           
        data = json.dumps(temp)
        sock.sendto(data.encode("ASCII"),addr)
    else:
        print(data.decode())
    
    
    
    for x in clients.keys():
        #print("Checking Ping Time!",decode_callsign_base40(x),clients[x]["pingTime"],now-clients[x]["pingTime"])
        if now - clients[x]["pingTime"]  > timeout:
#            print("TIMEOUT ",x)
            sock.sendto(b"DISC"+x,clients[x]["addr"])
            module = clients[x]["module"]
            modules[module].discard(x)
            del clients[x]
        elif now - clients[x]["pingTime"] > pingTime:
            if not clients[x]["pinged"]:
#               print("PINGING!",decode_callsign_base40(x))
                clients[x]["pinged"] = True
                sock.sendto(b"PING"+x,clients[x]["addr"])
                
def decode_callsign_base40(encoded_bytes):
    unpacked = struct.unpack(">HI",encoded_bytes)
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
        
