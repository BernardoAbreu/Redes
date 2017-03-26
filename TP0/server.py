#!/usr/bin/env python

import sys
import socket

#from struct import pack
import struct

class Server():

    def __init__(self):
        self.HOST = '127.0.0.1'
        self.PORT = 51515
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.HOST,self.PORT))
        self.sock.listen(1)
        self.counter = 0


    def run(self):
        try:
            while True:
                conn,address = self.sock.accept()
                conn.settimeout(3)

                data = conn.recv(1)
                if data == '+':
                    next_counter = (self.counter + 1)%1000
                elif data == '-':
                    next_counter = (self.counter - 1)%1000

                data_send = struct.pack('!i',next_counter)

                sent = conn.send(data_send)
                
                data = conn.recv(3)

                if int(data) == next_counter:
                    self.counter = next_counter

                print('Counter: '+str(self.counter))

                conn.close()
        except KeyboardInterrupt:
            pass
        except Exception as e:
            sys.stderr.write(str(e)+ '\n')
        finally:
            self.sock.close()


if __name__ == '__main__':
    s = Server()
    s.run()