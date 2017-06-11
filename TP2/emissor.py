#! /usr/bin/env python

import socket
import sys
import select

from message import Message
from message import MessageType

from client import Client


class EmitterClient(Client):

    def __init__(self, host, port, id):
        super(EmitterClient,self).__init__(host,port,id)
        self.state = 0
        self.prompt = ['[List clients (1)  Send message(2)] > ',
                        '[Id of receiving client (0 to broadcast)] > ',
                        '[Id of receiving client (0 to broadcast)] > ',
                        '[Message] > '
                        ]
        self.destiny = self.server_id


    def _command_loop(self):
        sys.stderr.write(self.prompt[self.state])
        # Wait for input from stdin & socket
        readable, writable, exceptional = select.select([sys.stdin, self.sock],[],[])
        for i in readable:
            if i == sys.stdin:
                data = sys.stdin.readline().strip()
                if data: 
                    print data

                    if self.state == 0:
                        try:
                            next_state = int(data)
                            if 0 < next_state < 3:
                                self.state = next_state
                        except ValueError:
                            print 'Type a number'
                    elif self.state == 3:
                        self._send_msg(self.destiny, self.sequence_number, MessageType.MSG, data)
                        self.state = 0
                    else:
                        try:
                            self.destiny = int(data)
                            if self.state == 1:
                                self._send_msg(self.destiny, self.sequence_number, MessageType.CREQ)
                                self.state = 0
                            elif self.state == 2:
                                self.state = 3
                        except ValueError:
                            print 'Type a number'
            elif i == self.sock:
                self._handle_recv()



if __name__ == "__main__":
    # import sys

    # if len(sys.argv)<2:
    #     sys.exit('Usage: %s chatid host portno' % sys.argv[0])

    # client = Client(sys.argv[1],sys.argv[2], int(sys.argv[3]))
    c = EmitterClient('127.0.0.1', 51515, 1 if len(sys.argv) < 2 else int(sys.argv[1]))
    c.run()
