#!/usr/bin/env python

import sys
import socket
import struct

from message import Message
from message import MessageType
from client import Client

class ExhibitorClient(Client):

    def __init__(self, host, port):
        super(ExhibitorClient,self).__init__(host,port,0)


    def _command_loop(self):
        self._handle_recv()


    def _handle_MSG(self, source_id, dest_id, sequence_number):
        print 'MSG'
        msg_length = Message.decode_msg_size(self.sock.recv(2))
        msg = Message.decode_msg(msg_length,self.sock.recv(msg_length))

        print 'Mensagem de ' + str(source_id) + ': ' + msg


    def _handle_CLIST(self, source_id, dest_id, sequence_number):
        print 'CLIST'
        msg_length = Message.decode_msg_size(self.sock.recv(Message.MSG_SIZE))

        msg = Message.decode_list(msg_length,self.sock.recv(msg_length*2))
        self._send_msg(source_id, self.sequence_number, MessageType.OK)

        print 'Clientes conectados: ' + ', '.join(map(str,msg))



if __name__ == '__main__':
    c = ExhibitorClient('127.0.0.1', 51515)
    c.run()