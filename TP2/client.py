#!/usr/bin/env python

import sys
import socket
import struct

from message import Message
from message import MessageType


class Client(object):

    def __init__(self, host, port, id):
        self.addr = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.id = id
        self.server_id = 65535
        self.sequence_number = 0
        self.finish = False

        self._handlers = [  0,
                            self._handle_OK,
                            self._handle_ERRO,
                            self._handle_OI,
                            self._handle_FLW,
                            self._handle_MSG,
                            self._handle_CREQ,
                            self._handle_CLIST,
                        ]


    def open_connection(self):
        self.sock.connect((self.addr))
        msg = Message(self.id, self.server_id, self.sequence_number)
        msg.set_type(MessageType.OI)
        self.sock.send(str(msg))

        header = self.sock.recv(Message.HEADER_SIZE)

        if not header:
            self.finish = True
            return

        msg_type, source_id, dest_id, sequence_number = Message.decode_header(header)

        if(msg_type == MessageType.OK):
            self.id = dest_id
            print('Seu identificador: ' + str(self.id))
            self.sequence_number += 1
        else:
            print >>sys.stderr, 'Erro estabelecendo id.'
            id = 0
            self.finish = True


    def _finish(self):
        try:
            print >>sys.stderr, 'hello'
            msg = Message(self.id, self.server_id, self.sequence_number)
            msg.set_type(MessageType.FLW)
            print >>sys.stderr, 'almost sent'
            self.sock.send(str(msg))
            print >>sys.stderr, 'sent'
            header = self.sock.recv(Message.HEADER_SIZE)
            print >>sys.stderr, 'recv'
            if not header:
                self.finish = True
                return
            msg_type, source_id, dest_id, sequence_number = Message.decode_header(header)

            if msg_type == MessageType.OK:
                print 'ok'
            elif msg_type == MessageType.ERRO:
                print 'error'
        except socket.error,e:
            print >>sys.stderr,'SOCKER ERROR:', e


    def _send_msg(self, dest, sequence_number, msg_type, msgdata = ''):
        msg = Message(self.id, dest, sequence_number)
        msg.set_type(msg_type)
        if msgdata:
            msg.set_msg(msgdata)
        self.sock.send(str(msg))


    def _handle_OK(self, source_id, dest_id, sequence_number):
        return


    def _handle_ERRO(self, source_id, dest_id, sequence_number):
        print >>sys.stderr,'\nMensagem de erro recebida'
        # self._send_msg(source_id, sequence_number, MessageType.ERRO)


    def _handle_OI(self, source_id, dest_id, sequence_number):
        self._send_msg(source_id, sequence_number, MessageType.ERRO)


    def _handle_FLW(self, source_id, dest_id, sequence_number):
        print '\nFLW recebido.'
        #check if source_id is server

        if source_id == self.server_id:
            self.finish = True
            self._send_msg(self.server_id, self.sequence_number, MessageType.OK)
        else:
            self._send_msg(source_id, sequence_number, MessageType.ERRO)


    def _handle_MSG(self, source_id, dest_id, sequence_number):
        self._send_msg(source_id, sequence_number, MessageType.ERRO)


    def _handle_CREQ():
        self._send_msg(source_id, sequence_number, MessageType.ERRO)


    def _handle_CLIST():
        self._send_msg(source_id, sequence_number, MessageType.ERRO)


    def _handle_recv(self):
        try:
            header = self.sock.recv(Message.HEADER_SIZE)

            if not header:
                self.finish = True
                return

            msg_type, source_id, dest_id, sequence_number = Message.decode_header(header)

            if msg_type > len(self._handlers) or msg_type == 0:
                self._send_msg(source_id, sequence_number, MessageType.ERRO)
            else:
                self._handlers[msg_type](source_id, dest_id, sequence_number)
        except struct.error as e:

            sys.stderr.write('Error unpacking message: '+ str(e)+ '\n')


    def _command_loop(self):
        self._handle_recv()


    def run(self):
        try:
            self.open_connection()
            while not self.finish:
                self._command_loop()
        except KeyboardInterrupt:
            self._finish()
        except socket.error, e:
            sys.stderr.write('SOCKET ERROR: '+ str(e)+ '\n')
        # except Exception as e:
        #     sys.stderr.write('ERROR: '+ str(e)+ '\n')
        #     self._finish()
        finally:
            print('Terminando')
            self.sock.close()


if __name__ == '__main__':
    c = Client('127.0.0.1', 51515)
    c.run()