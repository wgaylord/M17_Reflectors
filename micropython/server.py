import asyncio
import struct

import json

clients = set()
clientDests = {}
talking = {b"\00\00\00\00\00\00":False}

class DiscoveryProtocol(asyncio.DatagramProtocol):	
    def __init__(self):
        super().__init__()
        self.pingging = True
        self.pendingPong = False
        self.loop = asyncio.get_event_loop()
        self.address = (None,None,None)
    def connection_made(self, transport):

        self.transport = transport
        
        
    def datagram_received(self, data, addr):
       magic = data[0:4]
       if magic == b"STAT":
           data = ""
           dests = {}
           for x in clientDests.keys():
               if clientDests[x] in  dests.keys():
                   dests[decodeCallsign(clientDests[x])].append((decodeCallsign(x),talking[x]))
               else:
                   dests[decodeCallsign(clientDests[x])] = [(decodeCallsign(x),talking[x])]
           data = json.dumps(dests)
           self.transport.sendto(data.encode("ASCII"),addr)
       if magic == b"CONN":
           self.address = (addr,data[4:10],decodeCallsign(data[4:10]))
           clientDests[self.address[1]] = b"\00\00\00\00\00\00"
           talking[self.address[1]] = False
           clients.add((addr,data[4:10],self.address[2]))
           print(self.address[2],"Connected!")

           self.transport.sendto(b"ACKN",addr)
           self.transport.sendto(b"PING"+data[4:10],addr)
           self.pinger = self.loop.create_task(self.handlePing())
       if magic == b"DISC":
           self.transport.sendto(b"DISC",addr)
           clients.discard(self.address)
           del clientDests[self.address[1]]
           print(self.address[2],"Disconnected Gracefully.")
           self.pingging = False
       if magic == b"M17 ":
           #print(talking)
           #print("DST:",decodeCallsign(data[6:12]),"SRC:",decodeCallsign(data[12:18]))
           clientDests[data[12:18]] = data[6:12]
           talking[data[12:18]]=True
           for x in clients:
               if not x == self.address:
                   if clientDests[x[1]] == data[6:12]:
                       self.transport.sendto(data,x[0])
       if magic == b"PONG":
           #print("PONG")
           self.pendingPong=False


    async def handlePing(self):
        global talking
        while self.pingging:
            #print(self.pendingPong)
            if self.pendingPong:
                #self.transport.sendto(b"DISC",addr)
                clients.discard(self.address)
                del clientDests[self.address[1]]
                print(self.address[2],"Ping Timeout")

                self.pingging = False
            else:
                #print(talking,talking[self.address[1]])
                if talking[self.address[1]]:
                	talking[self.address[1]] = False
                self.transport.sendto(b"PING"+self.address[1],self.address[0])
                self.pendingPong = True
                await asyncio.sleep(10)
                
            
async def displayInfo():
    while True:
        dests = {}
        for x in clientDests.keys():
            if clientDests[x] in  dests.keys():
                dests[clientDests[x]].append(x)
            else:
                dests[clientDests[x]] = [x]
            print("Connected clients and Dests")
            for x in dests.keys():
                print("  ",decodeCallsign(x))
                for y in dests[x]:
                    print('    ',decodeCallsign(y),talking[y])
        await asyncio.sleep(60)          
            
def start_discovery():
    loop = asyncio.get_event_loop()
    t = loop.create_datagram_endpoint(DiscoveryProtocol,local_addr=('0.0.0.0',17000))
    loop.run_until_complete(t)
    loop.create_task(displayInfo())
    loop.run_forever()
    
    
def decodeCallsign(x):
    unpacked = struct.unpack(">HI",x)
    q = (unpacked[0]<<(8*4))+unpacked[1]  
    call = ""
    while q > 0:
        call += " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-/."[q%40]
        q = q //40
    return call

start_discovery()
