#!/usr/bin/env python

import select
import socket
import sys
import Queue


from message import Message
from message import MessageType
from id_pool import IdPool

class Server(object):


    def __init__(self, host, port, max_connections = 1):
        self.id = 65535
        self.server_address = (host, port)
        self.MAX_CONNECTIONS = max_connections
        
        # Create a TCP/IP socket
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.setblocking(0)

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
        self.next_to_remove = []

        self.id_pool = IdPool()



    def _handle_OI(self, s, source_id, sequence_number):
        print 'OI'
        error = False

        next_id = self.id_pool.get_next_emitter_id() if source_id else self.id_pool.get_next_exhibitor_id()

        if source_id > 4095:
            self.id_pool.associate_clients(next_id, source_id)

        msg = Message(self.id, next_id, sequence_number)
        msg.set_type(MessageType.OK)

        self._write_data(s, str(msg))


    def _handle_FLW(self, s, source_id, sequence_number):
        print 'FLW'
        #TODO check id
        self.id_pool.remove_id(source_id)

        msg = Message(self.id, source_id, sequence_number)

        msg.set_type(MessageType.OK)

        self._write_data(s, str(msg))

        self.next_to_remove.append(s)

        # self._remove_connection(s)


    def _handle_MSG(self):
        print 'MSG'


    def _handle_CREQ(self):
        print 'CREQ'


    def _handle_message(self, s, header):
        # A readable client socket has data
                    
        sys.stderr.write('received "%s" from %s\n' % (header, s.getpeername()))

        msg_type, source_id, dest_id, sequence_number = Message.decode_header(header)
        print msg_type, source_id, dest_id, sequence_number


        if(msg_type == MessageType.OI):
            self._handle_OI(s, source_id, sequence_number)
        elif(msg_type == MessageType.FLW):
            self._handle_FLW(s, source_id, sequence_number)
        print self.id_pool.get_all_clients()



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
        connection.setblocking(0)
        self.inputs.append(connection)

        # Give the connection a queue for data we want to send
        self.message_queues[connection] = Queue.Queue()



    def _remove_connection(self, s):
        # Stop listening for input on the connection
        self.inputs.remove(s)

        if s in self.outputs:
            self.outputs.remove(s)

        if s in self.next_to_remove:
            self.next_to_remove.remove(s)

        s.close()

        # Remove message queue
        del self.message_queues[s]



    def _handle_input(self, readable):
        # Handle inputs
        for s in readable:

            if s is self.server:
                self._create_connection(s)
            else:
                header = s.recv(Message.HEADER_SIZE)

                if header:
                    self._handle_message(s, header)
                else:
                    # Interpret empty result as closed connection
                    sys.stderr.write('closing %s after reading no data\n'%str(s.getpeername()))
                    self._remove_connection(s)


    def _handle_ouput(self, writable):
        # Handle outputs
        for s in writable:
            try:
                next_msg = self.message_queues[s].get_nowait()
            except Queue.Empty:
                # No messages waiting so stop checking for writability.
                sys.stderr.write('output queue for %s is empty\n'%str(s.getpeername()))
                self.outputs.remove(s)
                if s in self.next_to_remove:
                    self._remove_connection(s)
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
                print 'Finishing'
                self.inputs.remove(self.server)
                for s in self.inputs:
                    msg = Message(self.id, 0, 0)
                    msg.set_type(MessageType.FLW)
                    self._write_data(s, str(msg))

            except Exception as e:
                sys.stderr.write(str(e)+ '\n')
                self.server.close()
                break

        self.server.close()


if __name__ == '__main__':
    s = Server('127.0.0.1', 51515,2)
    s.run()