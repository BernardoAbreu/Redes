#!/usr/bin/env python

import select
import socket
import struct
import sys

CLIREQ = 1
QUERY = 2
RESPONSE = 3

TIMEOUT = 4

MAX_KEY_SIZE = 40
MAX_VALUE_SIZE = 160
MSG_TYPE_SIZE = 2

MAX_RESPONSE_SIZE = MSG_TYPE_SIZE + MAX_KEY_SIZE + 1 + MAX_VALUE_SIZE + 1


class Client(object):

    def __init__(self, ip, port):
        self.addr = (ip, int(port))
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.message = ''


    def __encode_request(self, key):
        header = struct.pack('!H', CLIREQ)

        return header + key + '\0'


    def __handle_input(self, readable):
        # Handle inputs
        for s in readable:
            data, addr = s.recvfrom(MAX_RESPONSE_SIZE)

            msg_type =  struct.unpack('!H',data[:2])[0]
            print msg_type
            if msg_type == RESPONSE:
                print 'RESPONSE from:',addr
                print "received message", len(data[2:]), ':', data[2:]
            

    def __handle_recv(self):
        wait_answers = True
        while wait_answers:
            # Wait for at least one of the sockets to be ready for processing
            print >>sys.stderr, '\nwaiting for the next event'
            r, w, x = select.select([self.sock], [], [], TIMEOUT)

            if not (r or w or x):
                print >>sys.stderr, '  timed out, do some other work here'
                wait_answers = False
            else:
                self.__handle_input(r)


    def run(self):

        while True:

            key = raw_input('Digite uma chave para ser pesquisada: ')

            self.message = self.__encode_request(key)

            self.sock.sendto(self.message, self.addr)

            self.__handle_recv()




if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('Numero incorreto de argumentos.\nUso: <IP:port>')
    else:
        ip,port = sys.argv[1].split(':')

        client = Client(ip, int(port))
        client.run()