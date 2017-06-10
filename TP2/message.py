import struct

class MessageType(object):

    OK = 1
    ERRO = 2
    OI = 3
    FLW = 4
    MSG = 5
    CREQ = 6
    CLIST = 7


class Message(object):

    def __init__(self, source_id, dest_id, sequence_number):

        self.msg_type = ''
        self.source_id = source_id
        self.dest_id = dest_id
        self.sequence_number = sequence_number
        self.msg = ''
        self.client_list = []


    def set_type(self, msg_type):
        self.msg_type = msg_type


    def set_msg(self, msg):
        self.msg_type


    def set_client_list(self, client_list):
        self.client_list = list(client_list)

    def _encode():
        header = struct.pack('!HHHH', self.msg_type, self.source_id,
                                        self.dest_id, self.sequence_number)

        if self.msg_type == MessageType.CLIST:
            length = len(self.client_list)
            data = struct.pack("!H%dB"%length, length, *self.client_list)
        elif self.msg_type == MessageType.MSG:
            data = struct.pack("!H%dB"%len(self.msg), len(self.msg), *self.msg)

        return header + data