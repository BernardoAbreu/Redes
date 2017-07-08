#!/usr/bin/env python

import re
import socket
import struct
import sys
from operator import methodcaller

CLIREQ = 1
QUERY = 2
RESPONSE = 3

TTL = 3

MSG_TYPE_SIZE = 2
HEADER_SIZE = 12
MAX_KEY_SIZE = 40
MAX_VALUE_SIZE = 160


MAX_REQ_SIZE = MSG_TYPE_SIZE + MAX_KEY_SIZE + 1

MAX_QUERY_SIZE = MSG_TYPE_SIZE + HEADER_SIZE + MAX_KEY_SIZE + 1

MAX_RESPONSE_SIZE = MSG_TYPE_SIZE + MAX_KEY_SIZE + 1 + MAX_VALUE_SIZE + 1

MAX_SIZE = max(MAX_REQ_SIZE, MAX_QUERY_SIZE)



class Servent(object):

    def __init__(self, port, input_file, neighbors):
        self.port = int(port)
        self.input_file = input_file
        self.sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP

        self.sock.bind(('', self.port))

        self.neighbors = [(x[0], int(x[1])) 
                        for x in map(methodcaller("split", ":"), neighbors)]

        self.values = self.__read_input()
        self.seq_number = 0
        self._handlers = (self.__handle_CLIREQ, self.__handle_QUERY)

        self.received_msgs = set()


    def __read_input(self):
        pattern = re.compile(r'^\s*([^#\s][^\s]*)\s*([^\s].*[^\s]|[^\s])\s*$')
        with open(self.input_file, 'r') as f:
            return {line.group(1) : line.group(2)
                    for line in map(pattern.match, f) if line is not None}


    def __decode_msg_type(self, msg_type):
        msg_type = struct.unpack('!H',msg_type)[0]

        return msg_type


    def __encode_query(self, ttl, addr, sequence_number, text):
        ip, port = addr
        header1 = struct.pack('!HH', QUERY, ttl)
        header2 = socket.inet_aton(ip)
        header3 = struct.pack('!HI', port, sequence_number)

        return (header1 + header2 + header3 + text + '\0')


    def __encode_response(self, key, value):
        header = struct.pack('!H', RESPONSE)

        return (header + key + '\t' + value + '\0')


    def __decode_query_header(self, header):
        ttl = struct.unpack('!H',header[:2])[0]
        ip =  socket.inet_ntoa(header[2:6])
        port,seq_number = struct.unpack('!HI', header[6:12])

        return ttl,ip,port,seq_number


    def __send_response(self, client_address, key, value):
        response = self.__encode_response(key, value)

        self.sock.sendto(response, client_address)


    def __check_for_key(self, client_address, key):
        print 'Procurando por:', key
        if key in self.values:
            value = self.values[key]
            print 'Valor de',key, 'encontrado:',value
            self.__send_response(client_address, key, value)
        else:
            print 'Valor de',key, 'nao encontrado.'


    def __handle_CLIREQ(self, key, client_address):
        print 'CLIREQ'

        msg = self.__encode_query(TTL, client_address, self.seq_number, key)

        ip, port = client_address
        self.received_msgs.add((ip, port, self.seq_number, key))

        self.seq_number += 1

        for neighbor in self.neighbors:
            self.sock.sendto(msg, neighbor)

        self.__check_for_key(client_address, key)


    def __handle_QUERY(self, message_body, source_neighbor_addr):
        print 'QUERY'

        header = message_body[:HEADER_SIZE]
        key = message_body[HEADER_SIZE:]

        ttl, ip, port, seq_number = self.__decode_query_header(header)

        if (ip, port, seq_number, key) not in self.received_msgs:
            self.received_msgs.add((ip, port, seq_number, key))
            self.__check_for_key((ip, port), key)

            ttl -= 1

            if ttl > 0:
                msg = self.__encode_query(ttl, (ip, port), seq_number, key)
                for neighbor in self.neighbors:
                    if neighbor != source_neighbor_addr:

                        self.sock.sendto(msg, neighbor)


    def __recv(self):

        data, addr = self.sock.recvfrom(MAX_SIZE)

        msg_type = self.__decode_msg_type(data[:MSG_TYPE_SIZE])

        try:
            self._handlers[msg_type-1](data[MSG_TYPE_SIZE:-1], addr)
        except IndexError:
            print >>sys.stderr, 'Tipo de mensagem nao suportado.'


    def run(self):
        try:
            while True:
                self.__recv()
        except KeyboardInterrupt:
            print '\nTerminando.'




if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit('Numero insuficiente de argumentos.\n' + 
            'Uso: <localport> <key-values> <ip1:port1> ... <ipN:portN>')
    else:
        port = int(sys.argv[1])
        input_file = sys.argv[2]
        neighbors = sys.argv[3:]

        s = Servent(port, input_file, neighbors)
        s.run()