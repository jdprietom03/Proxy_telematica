from socket import *
import threading
import config 
from log import *
from tqdm import tqdm

file_name = 'proxy.log'

class RoundRobin:
    def __init__(self):
        self.id = 0
    def next(self):
        self.id = (self.id + 1) % len(config.SERVERS)
        return self.id

class ProxyClient(threading.Thread):
    def __init__(self, conn, addr, proxy):
        threading.Thread.__init__(self)
        self.conn = conn
        self.addr = addr
        self.proxy = proxy
        self.daemon = True
        self.start()

    def run(self):
        log(f"Proxy client started on: {self.addr}", file_name)
        # Receive Request from Client
        request = self.conn.recv(config.BUFFER_SIZE)

        if not request or request == b'':
            print("CLOSING CONNECTION")
            self.conn.close()
            self.proxy.close()
            return

        log(message_received_from_client(request.decode()), file_name)
        
        self.find_cache(self.decorated_url(request), request)
        self.conn.close()
        self.proxy.close()

    def decorated_url(self, request):
        return "cache/" + self.get_url(request) + "__" + self.get_file(request)

    def get_url(self, request):
        print(request.decode())
        url = request.split(b' ')[3].decode()
        url = url.replace('/', '_').replace("\r\n","")

        return url.split(":")[0]

    def get_file(self, request):
        file = str(request.split(b' ')[1])
        file = file[2: len(file) - 1]
        print(file)
        file = "index.html" if file == "/" else file.split("/")[-1]
        return file

    def find_cache(self, url, request):
        print("URL: ", url)
        
        try:
            response_message = ""
            print("Opening file")
            with open(url, 'rb') as cached_file:
                # for line in cached_file:
                #     response_message += line
                buf = cached_file.read(config.BUFFER_SIZE_ACK)
                while buf:
                    self.conn.send(buf)
                    buf = cached_file.read(config.BUFFER_SIZE_ACK)

            cached_file.close()
            #log('Cached Response from Server: ' + response_message, file_name)
            #self.conn.sendall(response_message.encode())
        
        except FileNotFoundError:
            # sendall Request to Server
            #Show host of proxy server
            self.proxy.sendall(request)
            # Receive Response from Server
            response = self.proxy.recv(config.BUFFER_SIZE_ACK)
            print("Before while loop")
            with open(url, "wb") as f:
                print("Creating cache file")
                while response:
                    print(response)
                    f.write(response)
                    response = self.proxy.recv(config.BUFFER_SIZE_ACK)
            #log('Received Response from Server: ' + response.decode(), file_name)

            # cached_file = open(url, 'wb')
            # cached_file.write(response)
            # cached_file.close()

            #  sendall Response to Client
            self.conn.sendall(response)


# Start Proxy Server
def start_proxy_server():
    with socket(AF_INET, SOCK_STREAM) as s:
        # Bind Socket to Host and Port
        s.bind((config.RHOST, config.RPORT))
        # Listen for Connections
        s.listen(10)
        # Set Timeout for Socket
        #s.settimeout(5)
        log(host_message(config.RHOST, config.RPORT), file_name)
        robin = RoundRobin()
        while True:
            # Accept Connection
            conn, addr = s.accept()
            #log('Accepted Connection from: ' + addr, file_name)
            # Create a TCP Socket
            proxy = socket(AF_INET, SOCK_STREAM)
            
            ID = robin.next()
            proxy.connect((config.SERVERS[config.ID][1], config.SERVERS[config.ID][2]))
            log(host_message(config.SERVERS[config.ID][1], config.SERVERS[config.ID][2]), file_name)
            # Create a Proxy Client Thread
            ProxyClient(conn, addr, proxy)

# Start Proxy Server
start_proxy_server()