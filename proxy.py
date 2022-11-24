from socket import *
import threading
import config 
from log import *
from tqdm import tqdm
from datetime import datetime
import os

file_name = f'proxy_{datetime.now().strftime("%Y-%m-%d_%H-%M")}.log'
printLock = threading.Lock()
temporal_cache = {}

class RoundRobin:
    def __init__(self):
        self.id = 0
    def next(self):
        self.id = (self.id + 1) % len(config.SERVERS)
        return self.id

class ProxyClient(threading.Thread):
    def __init__(self, conn, addr, proxy, HOST, PORT):
        self.HOST = HOST
        self.PORT = PORT
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

        # if not request or request == b'':
        #     log("CLOSING CONNECTION", file_name)
        #     self.conn.close()
        #     self.proxy.close()
        #     return

        log(message_received_from_client(request.decode()), file_name)
        
        self.find_cache(self.decorated_url(request), request)
        self.conn.close()
        self.proxy.close()
        printLock.release()

    def decorated_url(self, request):
        #return "cache/" + self.get_url(request) + "__" + self.get_file(request)
        return "cache/" + self.HOST + "__" + self.get_file(request)

    def get_url(self, request):
        url = request.split(b' ')[3].decode()
        url = url.replace('/', '_').replace("\r\n","")

        return url.split(":")[0]

    def get_file(self, request):
        file = str(request.split(b' ')[1])
        file = file[2: len(file) - 1]
        file = "index.html" if file == "/" else file.split("/")[-1]
        return file

    def get_time_left(self, url):
        return str(config.TTL - (datetime.now() - temporal_cache[url]).total_seconds())

    def find_cache(self, url, request):
        log("Caching URL: " + url, file_name)

        if url in temporal_cache:
            if (datetime.now() - temporal_cache[url]).total_seconds() > config.TTL:
                del temporal_cache[url]
                log("Cache expired for " + url, file_name)
                os.remove(f"{url}")


        
        try:
            with open(url, 'rb') as cached_file:
                # for line in cached_file:
                #     response_message += line
                buf = cached_file.read(config.BUFFER_SIZE_ACK)
                while buf:
                    self.conn.send(buf)
                    buf = cached_file.read(config.BUFFER_SIZE_ACK)

            cached_file.close()
            log('Cached Response from Server... Time to Live: ' + self.get_time_left(url) , file_name)
            #self.conn.sendall(response_message.encode())
        
        except FileNotFoundError:
            self.proxy.sendall(request)
            # Receive Response from Server
            response = self.proxy.recv(config.BUFFER_SIZE_ACK)
            temporal_cache[url] = datetime.now()
            with open(url, "wb") as f:
                while response:
                    #print(response)
                    
                    f.write(response)
                    response = self.proxy.recv(config.BUFFER_SIZE_ACK)
            log('Received Response from Server... ', file_name)

            #  sendall Response to Client
            self.conn.sendall(response)

def start_proxy_server():
    s = socket(AF_INET, SOCK_STREAM)
    # Bind Socket to Host and Port
    s.bind((config.RHOST, config.RPORT))
    # Listen for Connections
    s.listen(10)
    # Set Timeout for Socket
    #s.settimeout(5)
    log(host_message(config.RHOST, config.RPORT), file_name)
    robin = RoundRobin()
    try:
        while True:
            # Accept Connection
            log("Waiting for Connection...", file_name)
            conn, addr = s.accept()
            log('Accepted Connection from: ' + str(addr), file_name)
            # Create a TCP Socket
            proxy = socket(AF_INET, SOCK_STREAM)
            
            ID = robin.next()
            printLock.acquire()
            proxy.connect((config.SERVERS[ID][1], config.SERVERS[ID][2]))
            log(host_message(config.SERVERS[ID][1], config.SERVERS[ID][2]), file_name)
            # Create a Proxy Client Thread
            ProxyClient(conn, addr, proxy, config.SERVERS[ID][1], config.SERVERS[ID][2])
    except KeyboardInterrupt:
        s.close()

start_proxy_server()