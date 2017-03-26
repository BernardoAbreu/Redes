#!/usr/bin/env python

import sys
import socket

import struct

class Client():

    def __init__(self):
        # Set socket initial values
        self.HOST = '127.0.0.1'
        self.PORT = 51515
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(3)     #Set socket timeout to 3 seconds

    def run(self, arg):
    
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


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.stderr.write("You must pass one argument to the program\n")
    elif sys.argv[1] not in ('inc','dec'):
        sys.stderr.write("The argument must be either 'inc' or 'dec'\n")
    else:
        c = Client()
        c.run(sys.argv[1])