import asyncio
import json
from http.server import BaseHTTPRequestHandler,HTTPServer,ThreadingHTTPServer
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
m17_server_address = ('192.168.0.216', 17000)

stats= b"{}"
html = b""


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
            self.wfile.write(html)
            self.server.path = self.path
            return
        print(self.path)    
        if self.path == "/status":
            try:
                sock.sendto(b"INFO",m17_server_address)
                stats = sock.recv(4000)
            except:
                stats = b"{}"
            self.send_response(200)
            self.send_header("Content-type", 'application/json')
            self.end_headers()
            self.wfile.write(stats) #Send history in JSOn format
            self.server.path = self.path 
            return
	    

        
        
def init_server(server_class=ThreadingHTTPServer, handler_class=ClientHandler): 
    server_address = ('0.0.0.0', 3001)
    httpd = server_class(server_address, handler_class)
    #httpd.serve_forever()
    while True:
        httpd.handle_request() #Handle Requests
    
html = loadHTML()
init_server()

