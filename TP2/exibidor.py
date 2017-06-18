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
        msg_length = Message.decode_msg_size(self.sock.recv(2))
        msg = Message.decode_msg(msg_length,self.sock.recv(msg_length))

        print 'Mensagem de ' + str(source_id) + ': ' + msg
        self._send_msg(source_id, sequence_number, MessageType.OK)


    def _handle_CLIST(self, source_id, dest_id, sequence_number):
        msg_length = Message.decode_msg_size(self.sock.recv(Message.MSG_SIZE))

        msg = Message.decode_list(msg_length,self.sock.recv(msg_length*2))

        print 'Clientes conectados: ' + ', '.join(map(str,msg))

        self._send_msg(source_id, sequence_number, MessageType.OK)



if __name__ == '__main__':

    if len(sys.argv) != 2:
        sys.exit('Numero incorreto de argumentos.\nUso: endereco_ip:porto')
    else:
        ip, port = sys.argv[1].split(':')
        c = ExhibitorClient(ip, int(port))
        c.run()