#!/usr/bin/env python

import sys
import socket
import struct

from message import Message
from message import MessageType


class Client():

    def __init__(self, host, port):
        # Set socket initial values
        self.addr = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.id = 0
        self.server_id = 65535
        self.sequence_number = 0
        self.finish = False



    def open_connection(self):
        self.sock.connect((self.addr))
        msg = Message(self.id, self.server_id, self.sequence_number)
        msg.set_type(MessageType.OI)
        self.sock.send(str(msg))


        msg_type, source_id, dest_id, sequence_number = self.recv_header()
        if(msg_type == MessageType.OK):
            self.id = dest_id


    def recv_header(self):
        header = self.sock.recv(Message.HEADER_SIZE)
        msg_type, source_id, dest_id, sequence_number = Message.decode_header(header)

        print msg_type, source_id, dest_id, sequence_number

        return msg_type, source_id, dest_id, sequence_number



    def _handle_msg(self, msg_type, source_id, dest_id, sequence_number):
        if msg_type == MessageType.FLW:
            self.finish = True
            msg = Message(self.id, self.server_id, self.sequence_number)
            msg.set_type(MessageType.OK)
            self.sock.send(str(msg))
            self.sock.close()


    def run(self):
    
        try:
            self.open_connection()
            print('Seu identificador: ' + str(self.id))
            while not self.finish:
                msg_type, source_id, dest_id, sequence_number = self.recv_header()

                self._handle_msg(msg_type, source_id, dest_id, sequence_number)
           
        except KeyboardInterrupt:
            msg = Message(self.id, self.server_id, self.sequence_number)
            msg.set_type(MessageType.FLW)
            self.sock.send(str(msg))
            msg_type, source_id, dest_id, sequence_number = self.recv_header()
            if msg_type == MessageType.OK:
                print 'ok'
            elif msg_type == MessageType.ERROR:
                print 'error'
        
        except struct.error as e:
            # Error unpacking value received from server
            # sys.stderr.write('ERROR: Value received from Server does not follow standard\n')
            sys.stderr.write('ERROR: '+ str(e)+ '\n')
        except Exception as e:
            sys.stderr.write('ERROR: '+ str(e)+ '\n')
        finally:
            self.sock.close()


if __name__ == '__main__':
    c = Client('127.0.0.1', 51515)
    c.run()