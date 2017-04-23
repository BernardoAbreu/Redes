#!/usr/bin/env python

import sys
import socket

#from struct import pack
import struct


def carry_around_add(a, b):
    c = a + b
    return(c &0xffff)+(c >>16)

def checksum(msg):
    s =0
    for i in range(0, len(msg),2):
        w = ord(msg[i])+(ord(msg[i+1])<<8)
        s = carry_around_add(s, w)
    return~s &0xffff


class Server():

    def __init__(self):
        self.HOST = '127.0.0.1'
        self.PORT = 51515
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.HOST,self.PORT))
        self.sock.listen(1)
        self.counter = 0


    def receptor(self):
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


    def transmitter(self, arg):
        try:
            addr = (self.HOST,self.PORT)
            self.sock.connect((addr))

            request = '+' if arg=='inc' else '-'

            sent = self.sock.send(request)

            #Receive value of counter from server in 4 bytes
            data = self.sock.recv(4)
            #Unpack value received and get the first element of the output tuple
            data = struct.unpack('!i',data)[0]

            print('Counter value received: ' + str(data))
            
            data = '00' + str(data)     #Make sure the string to be sent has at least 3 bytes

            # Send the last three characters of the string, insuring 3 byte size.
            # The send method send the methods in left to right order. (i.e. hundred, ten, unit)
            sent = self.sock.send(data[-3:])

        except struct.error:
            # Error unpacking value received from server
            sys.stderr.write('ERROR: Value received from Server does not follow standard\n')
        except Exception as e:
            sys.stderr.write('ERROR: '+ str(e)+ '\n')
        finally:
            self.sock.close()


    def error_check(self):

if __name__ == '__main__':
    data = "dc c0 23 c2 dc c0 23 c2 00 00 00 04 00 00 01 02 03 04"

    data = data.split()
    data = map(lambda x: int(x,16), data)
    data = struct.pack("%dB" % len(data), *data)

    print ' '.join('%02X' % ord(x) for x in data)
    print "Checksum: 0x%04x" % checksum(data)