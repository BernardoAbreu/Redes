import re
import socket
import struct


QUERY = 2
TTL = 3

HEADER_SIZE = 18
MAX_QUERY_SIZE = 178

MAX_SIZE = MAX_QUERY_SIZE

class Client(object):

    def __init__(self, port, input_file, neighbors):
        self.port = port
        self.input_file = input_file
        self.neighbors = neighbors.split(':')
        self.sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
        self.sock.bind(('', port))

        self.values = self.__read_input()


    def __read_input(self):
        pattern = re.compile(r'^\s*([^#\s][^\s]+)\s*([^\s].+[^\s])\s*$')
        with open(self.input_file, 'r') as file:
            return {line.group(1) : line.group(2)
                    for line in map(pattern.match,file) if line is not None}


    def run(self):

        while True:
            data, addr = self.sock.recvfrom(MAX_SIZE) # buffer size is 1024 bytes
            print "received message:", data
            print 'from:',addr


# Message type (uint16_t) : 2 (QUERY),
# TTL (uint16_t),
# IP PORT (uint16_t) consulting client program
# Seq number (uint32_t)
# Text (Max 160 caracteres)


def __encode_query(ttl, ip, port, sequence_number, text):
    header1 = struct.pack('!HH', QUERY, ttl)
    header2 = struct.pack('=4sl', socket.inet_aton(ip), socket.INADDR_ANY)
    header3 = struct.pack('!HI', port, sequence_number)

    return (header1 + header2 + header3 + text)


def __decode_header(header):
    query,ttl = struct.unpack('!HH',header[:4])
    ip,ay  = struct.unpack('=4sl',header[4:12])
    port,seq_number = struct.unpack('!HI', header[12:18])
    ip =  socket.inet_ntoa(ip)
    print query,ttl,ip,port,seq_number