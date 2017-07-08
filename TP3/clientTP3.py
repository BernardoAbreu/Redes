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

            msg_type =  struct.unpack('!H',data[:MSG_TYPE_SIZE])[0]

            if msg_type == RESPONSE:
                print '\nResposta de %s na porta %d:'%addr
                print data[MSG_TYPE_SIZE:]
            else:
                print '\nTipo inesperado de mensagem.'
            

    def __issue_request(self, key):
        wait_answers = True
        retransmit = True

        message = self.__encode_request(key)

        self.sock.sendto(message, self.addr)

        while wait_answers:
            r, w, x = select.select([self.sock], [], [], TIMEOUT)

            if not (r or w or x):
                if retransmit:
                    self.sock.sendto(message, self.addr)
                    retransmit = False
                else:
                    wait_answers = False
            else:
                retransmit = False
                self.__handle_input(r)

        print '\nNao ha mais respostas.\n'


    def run(self):
        try:
            while True:
                key = raw_input('Digite uma chave para ser pesquisada: ')

                self.__issue_request(key)
        except KeyboardInterrupt:
            print '\nTerminando.'
        except EOFError:
            print '\nTerminando.'




if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('Numero incorreto de argumentos.\nUso: <IP:port>')
    else:
        ip,port = sys.argv[1].split(':')

        client = Client(ip, int(port))
        client.run()