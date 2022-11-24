def log(t, file): 
    print(t)
    f = open(f'logs/{file}', 'a')
    f.write(t +  '\n')
    f.close()

def host_message(host, port):
    return f"Connected Succesfully to Host: {host} on Port: {port}"

def message_received_from_client(message):
    return f"Received a message from client: \n{message}"
