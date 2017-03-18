import socket


class Server():

    def __init__(self):
        self.HOST = '127.0.0.1'
        self.PORT = 51515
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.HOST,self.PORT))
        self.sock.listen(1)
        self.counter = 0


    def run(self):
        print('Initializinf server')
        try:
            while True:
                print('Waiting for connection')
                conn,address = self.sock.accept()
                print('Connection established to: ' + str(address))
                data = conn.recv(1024)
                if data == '+':
                    next_counter = (self.counter + 1)%1000
                elif data == '-':
                    next_counter = (self.counter - 1)%1000

                sent = conn.send(str(next_counter))
                print(sent)
                if sent != 1:
                    print("error")
                
                data = conn.recv(3072)
                
                if int(data) == next_counter:
                    self.counter = next_counter
                    print('ok: '+str(self.counter))
                else:
                    print('not ok')

                conn.close()
        except Exception as e:
            print(e)
        finally:
            self.sock.close()


if __name__ == '__main__':
    s = Server()
    s.run()