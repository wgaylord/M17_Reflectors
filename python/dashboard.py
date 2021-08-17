import asyncio
import json
from http.server import BaseHTTPRequestHandler,HTTPServer,ThreadingHTTPServer
import socket


stats= {}

class EchoClientProtocol:
    def __init__(self, message, on_con_lost):
        self.message = message
        self.on_con_lost = on_con_lost
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        self.transport.sendto(self.message.encode())

    def datagram_received(self, data, addr):
        global stats
        stats = json.loads(data.decode())
        print(stats)
        self.transport.close()
    def connection_lost(self, exc):
        self.on_con_lost.set_result(True)


async def getData():
    # Get a reference to the event loop as we plan to use
    # low-level APIs.
    loop = asyncio.get_running_loop()

    on_con_lost = loop.create_future()
    message = "STAT"

    transport, protocol = await loop.create_datagram_endpoint(
        lambda: EchoClientProtocol(message, on_con_lost),
        remote_addr=('127.0.0.1', 17000))

    try:
        await on_con_lost
    finally:
        transport.close()



def loadHTML(): #Load the main client html file
    htmlFile = open("Client.html","rb")
    html = htmlFile.read()
    htmlFile.close()
    return html

class ClientHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/": #Handle requests to the server with no path
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(loadHTML())
            self.server.path = self.path
            return
        if self.path == "/status":
            self.send_response(200)
            self.send_header("Content-type", 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(stats).encode("utf-8")) #Send history in JSOn format
            self.server.path = self.path 
            return
	    

        
        
def init_server(server_class=ThreadingHTTPServer, handler_class=ClientHandler): 
    server_address = ('0.0.0.0', 3001)
    httpd = server_class(server_address, handler_class)
    #httpd.serve_forever()
    while True:
        httpd.handle_request() #Handle Requests
        asyncio.run(getData())
    
     
init_server()

