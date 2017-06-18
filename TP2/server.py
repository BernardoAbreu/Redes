#!/usr/bin/env python

import select
import socket
import sys
import Queue


from message import Message
from message import MessageType
from id_pool import IdPool

class Server(object):


    def __init__(self, port, max_connections = 255):
        self.id = 65535
        self.server_address = ('', port)
        self.MAX_CONNECTIONS = max_connections
        
        # Create a TCP/IP socket
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind the socket to the port
        self.server.bind(self.server_address)

        sys.stderr.write('starting up on %s port %s\n' % self.server_address)

        # Listen for incoming connections
        self.server.listen(self.MAX_CONNECTIONS)


        # Sockets from which we expect to read
        self.inputs = [ self.server ]

        # Sockets to which we expect to write
        self.outputs = [ ]

        # Outgoing message queues (socket:Queue)
        self.message_queues = {}

        # Connections that need to send data before being removed
        # self.next_to_remove = []

        self.id_pool = IdPool()


        self._handlers = [  0,
                            self._handle_OK,
                            self._handle_ERRO,
                            self._handle_OI,
                            self._handle_FLW,
                            self._handle_MSG,
                            self._handle_CREQ,
                            self._handle_CLIST,
                        ]


    def _write_msg(self, s, source_id, dest_id, sequence_number, msg_type, msg = ''):
        new_msg = Message(source_id, dest_id, sequence_number)
        new_msg.set_type(msg_type)
        if msg:
            if msg_type == MessageType.CLIST:
                new_msg.set_list(msg)
            else:
                new_msg.set_msg(msg)

        self._write_data(s, str(new_msg))


    def _redirect_msg(self, s, source_id, dest_id, sequence_number, msg, msg_type):
        error = False

        if not dest_id:
            exhibitors = self.id_pool.get_all_exhibitors()
            for e in exhibitors:
                self._write_msg(self.id_pool.get_sock(e), source_id, 0,
                                sequence_number, msg_type, msg)

        elif self.id_pool.id_exists(dest_id):
            if dest_id < 4096:
                associate = self.id_pool.get_associate(dest_id)
                if not associate:
                    error = True
                    print >>sys.stderr,'Nenhum exibidor associado a esse emissor'
                else:
                    self._write_msg(self.id_pool.get_sock(associate), source_id,
                                dest_id, sequence_number, msg_type, msg)
            else:
                self._write_msg(self.id_pool.get_sock(dest_id), source_id,
                                dest_id, sequence_number, msg_type, msg)
        else:
            error = True

        if error:
            sys.stderr.write('Enviando mensagem de erro para %d em %s\n' %
                                (source_id, str(s.getpeername())))
            self._write_msg(s, self.id, source_id, 
                                        sequence_number, MessageType.ERRO)


    def _handle_OK(self, s, source_id, dest_id, sequence_number):
        print >>sys.stderr,'OK'


    def _handle_ERRO(self, s, source_id, dest_id, sequence_number):
        print >>sys.stderr,'\nMensagem de erro recebida'


    def _handle_OI(self, s, source_id, dest_id, sequence_number):
        print >>sys.stderr,'OI'

        next_id = 0


        if not source_id:
            next_id = self.id_pool.get_next_exhibitor_id(s)
        elif source_id < 4096 or self.id_pool.id_exists(source_id):
            next_id = self.id_pool.get_next_emitter_id(s)
            if source_id > 4095:
                self.id_pool.associate_clients(next_id, source_id)

        self._write_msg(s, self.id, next_id, sequence_number, 
            MessageType.OK if next_id else MessageType.ERRO)


    def _handle_FLW(self, s, source_id, dest_id, sequence_number):
        print >>sys.stderr,'FLW'
        #TODO check id

        if source_id < 4096:
            associate = self.id_pool.get_associate(source_id)

            if associate:
                associate_sock = self.id_pool.get_sock(associate)
                new_msg = Message(self.id, associate, sequence_number)
                new_msg.set_type(MessageType.FLW)
                associate_sock.send(str(new_msg))
                header = associate_sock.recv(Message.HEADER_SIZE)
                self.id_pool.remove_id(associate)
                self._remove_connection(associate_sock)

        new_msg = Message(self.id, source_id, sequence_number)
        new_msg.set_type(MessageType.OK)

        s.send(str(new_msg))
        self.id_pool.remove_id(source_id)
        self._remove_connection(s)


    def _handle_MSG(self, s, source_id, dest_id, sequence_number):
        error = False

        print >>sys.stderr,'MSG'

        msg_length = Message.decode_msg_size(s.recv(Message.MSG_SIZE))

        msg = s.recv(msg_length)

        self._redirect_msg(s, source_id, dest_id, sequence_number, msg, 
                        MessageType.MSG)

        self._write_msg(s, self.id, source_id, sequence_number, MessageType.OK)


    def _handle_CREQ(self, s, source_id, dest_id, sequence_number):
        print >>sys.stderr,'CREQ'
        client_list = self.id_pool.get_all_clients()

        self._redirect_msg(s, source_id, dest_id, sequence_number, client_list, 
                        MessageType.CLIST)
        self._write_msg(s, self.id, source_id, sequence_number, MessageType.OK)        


    def _handle_CLIST(self, s, source_id, dest_id, sequence_number):
        msg_length = Message.decode_msg_size(s.recv(Message.MSG_SIZE))
        msg = s.recv(msg_length*2)
        self._write_msg(s, self.id, source_id,sequence_number, MessageType.ERRO)


    def _handle_message(self, s, header):
        # A readable client socket has data
        error = False
        sys.stderr.write('received "%s" from %s\n' % (header, s.getpeername()))

        msg_type, source_id, dest_id, sequence_number = Message.decode_header(header)
        print >>sys.stderr,msg_type, source_id, dest_id, sequence_number

        if msg_type != MessageType.OI:

            if not self.id_pool.id_exists(source_id):
                error = True
            elif s is not self.id_pool.get_sock(source_id):
                error = True

        if msg_type > len(self._handlers) or msg_type == 0 or error:

            if msg_type == MessageType.MSG:
                msg_length = Message.decode_msg_size(s.recv(Message.MSG_SIZE))
                msg = s.recv(msg_length)
            elif msg_type == MessageType.CLIST:
                msg_length = Message.decode_msg_size(s.recv(Message.MSG_SIZE))
                msg = s.recv(msg_length*2)

            self._write_msg(s, self.id, source_id,sequence_number, MessageType.ERRO)

        else:
            self._handlers[msg_type](s, source_id, dest_id, sequence_number)


    def _write_data(self, s, data):
         # A readable client socket has data
        self.message_queues[s].put(data)
        # Add output channel for response
        if s not in self.outputs:
            self.outputs.append(s)


    def _create_connection(self,s):
        # A "readable" server socket is ready to accept a connection
        connection, client_address = s.accept()

        sys.stderr.write('new connection from ' + str(client_address)+ '\n')
        self.inputs.append(connection)

        # Give the connection a queue for data we want to send
        self.message_queues[connection] = Queue.Queue()


    def _remove_connection(self, s):
        print >>sys.stderr,'Removing connection ' + str(s.getpeername())
        self.id_pool.remove_socket_if_exists(s)

        # Stop listening for input on the connection
        self.inputs.remove(s)

        if s in self.outputs:
            self.outputs.remove(s)

        # Remove message queue
        del self.message_queues[s]
        
        s.close()
        print >>sys.stderr,'Connection removed'


    def _handle_input(self, readable):
        # Handle inputs
        for s in readable:
            if s is self.server:
                self._create_connection(s)
            else:
                print >>sys.stderr,'receiving from',s.getpeername()
                try:
                    header = s.recv(Message.HEADER_SIZE)

                    if header:
                        self._handle_message(s, header)
                    else:
                        # Interpret empty result as closed connection
                        sys.stderr.write('closing %s after reading no data\n'%str(s.getpeername()))
                        self._remove_connection(s)
                except Exception as e:
                    print >>sys.stderr,e


    def _handle_ouput(self, writable):
        # Handle outputs
        for s in writable:
            try:
                next_msg = self.message_queues[s].get_nowait()
            except Queue.Empty:
                # No messages waiting so stop checking for writability.
                sys.stderr.write('output queue for %s is empty\n'%str(s.getpeername()))
                self.outputs.remove(s)
            except Exception,e:
                print >>sys.stderr,e
            else:
                sys.stderr.write('sending "%s" to %s\n' % (next_msg, s.getpeername()))
                s.send(next_msg)


    def _handle_exceptional(self, exceptional):
        # Handle "exceptional conditions"
        for s in exceptional:
            sys.stderr.write('handling exceptional condition for %s\n'%str(s.getpeername()))
            self._remove_connection(s)


    def run(self):
        while self.inputs:
            try:
                # Wait for at least one of the sockets to be ready for processing
                sys.stderr.write('\nwaiting for the next event\n')

                readable, writable, exceptional = select.select(self.inputs,
                                                                self.outputs,
                                                                self.inputs)
                self._handle_input(readable)
                self._handle_ouput(writable)
                self._handle_exceptional(exceptional)
            except KeyboardInterrupt:
                if self.server in self.inputs:
                    self.inputs.remove(self.server)
                for s in self.inputs:
                    msg = Message(self.id, 0, 0)
                    msg.set_type(MessageType.FLW)
                    self._write_data(s, str(msg))
            except Exception, e:
                sys.stderr.write(str(e)+ '\n')
                # self.server.close()
                if self.server in self.inputs:
                    self.inputs.remove(self.server)
                for s in self.inputs:
                    msg = Message(self.id, 0, 0)
                    msg.set_type(MessageType.FLW)
                    self._write_data(s, str(msg))


        print >>sys.stderr,'Terminando'
        self.server.close()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('Argumentos insuficientes.\nUso: porto')
    else:
        s = Server(int(sys.argv[1]))
        s.run()