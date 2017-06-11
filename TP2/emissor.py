#! /usr/bin/env python

import socket
import sys
import select

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



    def _write_msg(self, dest_id, msg_type, msg2send = ''):
        msg = Message(self.id, dest_id, self.sequence_number)
        msg.set_type(msg_type)
        if msg2send:
            msg.set_msg(msg2send)

        self.sock.send(str(msg))


    def _finish(self):
        msg = Message(self.id, self.server_id, self.sequence_number)
        msg.set_type(MessageType.FLW)
        self.sock.send(str(msg))

        header = self.sock.recv(Message.HEADER_SIZE)

        if not header:
            self.finish = True
            return

        msg_type, source_id, dest_id, sequence_number = Message.decode_header(header)

        if msg_type == MessageType.OK:
            print 'ok'
        elif msg_type == MessageType.ERROR:
            print 'error'


    def _handle_FLW(self):
        self.finish = True
        msg = Message(self.id, self.server_id, self.sequence_number)
        msg.set_type(MessageType.OK)
        self.sock.send(str(msg))
        self.sock.close()


    def _handle_recv(self):
        try:
            header = self.sock.recv(Message.HEADER_SIZE)

            if not header:
                self.finish = True
                return

            msg_type, source_id, dest_id, sequence_number = Message.decode_header(header)

            if msg_type == MessageType.FLW:
                self._handle_FLW()
        except struct.error as e:

            sys.stderr.write('Error unpacking message: '+ str(e)+ '\n')


    def run(self):

        try:
            self.open_connection()
            print('Seu identificador: ' + str(self.id))
            while not self.finish:

                # Wait for input from stdin & socket
                readable, writable, exceptional = select.select([sys.stdin, self.sock],[],[])


                for i in readable:
                    if i == sys.stdin:
                        data = sys.stdin.readline().strip()
                        if data: 
                            print data
                    elif i == self.sock:
                        self._handle_recv()
        except KeyboardInterrupt:
            self._finish()
        except socket.error, e:
            sys.stderr.write('SOCKET ERROR: '+ str(e)+ '\n')
        except Exception as e:
            sys.stderr.write('ERROR: '+ str(e)+ '\n')
            self._finish()
        finally:
            self.sock.close()


if __name__ == "__main__":
    # import sys

    # if len(sys.argv)<2:
    #     sys.exit('Usage: %s chatid host portno' % sys.argv[0])

    # client = Client(sys.argv[1],sys.argv[2], int(sys.argv[3]))
    c = Client('127.0.0.1', 51515, 1 if len(sys.argv) < 2 else int(sys.argv[1]))
    c.run()