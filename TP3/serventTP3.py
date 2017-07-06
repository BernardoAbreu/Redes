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
HEADER_SIZE = 18
MAX_QUERY_SIZE = 60

MAX_SIZE = MAX_QUERY_SIZE

class Servent(object):

    def __init__(self, port, input_file, neighbors):
        self.port = port
        self.input_file = input_file
        self.sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
        self.sock.bind(('', port))

        self.neighbors = [(x[0], int(x[1])) 
                        for x in map(methodcaller("split", ":"), neighbors)]

        self.values = self.__read_input()
        self.sequence_number = 0
        self._handlers = (self.__handle_CLIREQ, self.__handle_QUERY)


    def __read_input(self):
        pattern = re.compile(r'^\s*([^#\s][^\s]+)\s*([^\s].+[^\s])\s*$')
        with open(self.input_file, 'r') as file:
            return {line.group(1) : line.group(2)
                    for line in map(pattern.match,file) if line is not None}


    def run(self):

        while True:
            data, addr = self.sock.recvfrom(MAX_SIZE) # buffer size is 1024 bytes

            self.__handle_recv(data,addr)


    def __handle_recv(self, data, addr):
        print "received message:", data
        print 'from:',addr

        msg_type = self.__decode_msg_type(data[:MSG_TYPE_SIZE])

        print msg_type

        try:
            self._handlers[msg_type-1](data[MSG_TYPE_SIZE:], addr)
        except IndexError:
            print >>sys.stderr, 'Unsupported message type'


    # Message type (uint16_t) : 2 (QUERY),
    # TTL (uint16_t),
    # IP PORT (uint16_t) consulting client program
    # Seq number (uint32_t)
    # Text Key (Max 40 caracteres)
    def __encode_query(self, ttl, addr, sequence_number, text):
        ip, port = addr
        header1 = struct.pack('!HH', QUERY, ttl)
        header2 = struct.pack('=4sl', socket.inet_aton(ip), socket.INADDR_ANY)
        header3 = struct.pack('!HI', port, sequence_number)

        return (header1 + header2 + header3 + text)

    def __encode_response(self, key, value):
        header = struct.pack('!H', RESPONSE)

        return (header + key + '\t' + value + '\0')


    def __decode_msg_type(self, msg_type):
        msg_type = struct.unpack('!H',msg_type)[0]

        return msg_type


    def __decode_query_header(self, header):
        ttl = struct.unpack('!H',header[:2])[0]
        ip,ay  = struct.unpack('=4sl',header[2:10])
        port,seq_number = struct.unpack('!HI', header[10:16])
        ip =  socket.inet_ntoa(ip)
        print ttl,ip,port,seq_number
        return ttl,ip,port,seq_number



    def __handle_CLIREQ(self, message_body, client_address):
        print 'CLIREQ'
        key_text = message_body
        msg = self.__encode_query(TTL, client_address, 
                self.sequence_number, key_text)

        self.sequence_number += 1

        for neighbor in self.neighbors:
            print neighbor
            print msg
            self.sock.sendto(msg, neighbor)
        print 'here'
        self.__check_for_key(client_address, key_text)


    def __handle_QUERY(self, message_body, source_neighbor_addr):
        print 'QUERY'
        print HEADER_SIZE
        header = message_body[:(HEADER_SIZE-MSG_TYPE_SIZE)]
        key = message_body[(HEADER_SIZE-MSG_TYPE_SIZE):]
        print header
        ttl, ip, port, seq_number = self.__decode_query_header(header)

        print ttl, ip, port, seq_number
        # check if message was received before

        self.__check_for_key((ip, port), key)

        # ttl -= 1

        # if ttl > 0:
        #     msg = __encode_query(ttl, (ip, port), seq_number, key_text)
        #     for neighbor in self.neighbors:
        #         if neighbor != source_neighbor_addr:
        #             self.sock.sendto(msg, neighbor)


        
    def __check_for_key(self, client_address, key):

        if key in self.values:
            value = self.values[key]
            print 'value', value
            self.__send_response(client_address, key, value)


    def __send_response(self, client_address, key, value):
        response = self.__encode_response(key, value)
        print 'response', response
        # make header
        self.sock.sendto(response, client_address)


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