import socket


class Client():

    def __init__(self):
        self.HOST = '127.0.0.1'
        self.PORT = 51515
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
    
    try:
        addr = (HOST,PORT)
        sock.connect((addr))

        print('Connected to:'+str(addr))

        request = raw_input('Enter "+" or "-" to increment or decrement the counter: ')

        while request not in ('+','-'):
            request = raw_input('Enter "+" or "-" to increment or decrement the counter: ')


        print('Sending request to '+ ('in' if request == '+' else 'de') + 'crement counter')
        sent = sock.send(request)
        print('Sending: ' + str(sent))
        if sent != 1:
            print("error")
        
        data = sock.recv(4096)
        print('Received: ' + str(data))
        sent = sock.send(data)
        print('Sending:' + str(sent))
    except Exception as e:
        print(e)
    finally:
        sock.close()


if __name__ == '__main__':
    client()