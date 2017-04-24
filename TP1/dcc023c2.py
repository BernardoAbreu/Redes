#!/usr/bin/env python

import sys
import socket

#from struct import pack
import struct
import time
import queue

import threading

WRONG_CHKSUM = 1

# def carry_around_add(a, b):
#     c = a + b
#     return(c &0xffff)+(c >>16)

# def checksum(msg):
#     s =0
#     for i in range(0, len(msg),2):
#         w = ord(msg[i])+(ord(msg[i+1])<<8)
#         s = carry_around_add(s, w)
#     return~ s&0xffff

def checksum(msg):
    sum = 0

    for c in msg:
        sum += ord(c)
        if (sum & 0xFFFF0000):
            # carry occurred,
            # so wrap around
            sum &= 0xFFFF
            sum+=1
    return ~sum & 0xFFFF


class Server():

    def __init__(self):
        self.HOST = '127.0.0.1'
        self.PORT = 51515
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.HOST,self.PORT))
        self.sock.listen(1)
        self.counter = 0
        self.sync = 0xDCC023C2

        # Queues for sharing data between threads
        self.send_queue = queue.Queue()
        self.ack_recv_queue = queue.Queue()
        self.data_recv_queue = queue.Queue()


        # Locks
        self.final_lock = threading.Lock()
        self.send_lock = threading.Lock()

        self.active = True



    def send_data(data_send):
        try:
            with self.send_lock:
                self.conn.send(data_send)
        except Exception as e:
            sys.stderr.write('ERROR: '+ str(e)+ '\n')


    def recv_data():
        try:
            last_sync = 0

            while self.active:
                # recv sync

                sync_header = self.sock.recv(4)

                current_sync = unpack_sync(sync_header)

                # Check if it is beginning of frame otherwise move on to the next sync
                if current_sync == self.sync and last_sync == self.sync:

                    remaining_header = self.sock.recv(6)

                    chksum, length, frame_id = unpack_header(remaining_header)


                    if length:
                        # recv data file frame
                        data = self.sock.recv(length)

                    error = error_check(sync_header+remaining_header, data)
                    if not error:
                        if length == 0:
                            self.ack_recv_queue.put(frame_id)
                        else:
                            self.data_recv_queue.put((chksum, frame_id, data))

                    current_sync = 0


                last_sync = current_sync

        except Exception as e:
            sys.stderr.write('ERROR: '+ str(e)+ '\n')



    def receptor(self):
        last_frame_id = 1

        with open(self.outfilename, "wb") as output_file:
            while True:

                receptor_data = self.data_recv_queue.get()

                if receptor_data == None:
                    break

                chksum, frame_id, data = receptor_data


                if frame_id == last_frame_id and chksum == last_chksum:
                    # Resend ACK
                    ack_frame = build_frame(frame_id)
                    self.send_data(ack_frame)
                elif frame_id != last_frame_id:
                    last_frame_id = frame_id
                    last_chksum = chksum

                    # Send new ACK
                    ack_frame = build_frame(frame_id)
                    self.send_data(ack_frame)

                    # Write received data
                    output_file.write(data)




    def transmitter(self, arg):
        frame_id = 0

        file_byte_array = bytearray()
        with open(filename, "rb") as f:
            byte = f.read(1)
            count = 1

            while byte != "":
                # Do stuff with byte.
                
                frame = build_frame(frame_id, byte)
                self.send_data(data_frame)
                start_time = time.time()

                while True:
                    try:
                        ack_frame_id = self.ack_recv_queue.get(timeout = 1)

                        if frame_id == ack_frame_id:
                            break
                        else:
                            while True:
                                if (time.time() - start_time) >=1:
                                    break
                            self.send_data(data_frame)
                            start_time = time.time()
                    except queue.Empty:
                        # send again
                        self.send_data(data_frame)
                        start_time = time.time()


                frame_id = 0 if frame_id else 1
                byte = f.read(1)





    # def recv_data_original():

    #     # recv sync

    #     sync_header = self.sock.recv(2)

    #     sync1, sync2 = unpack_sync(sync_header)

    #     if sync1 == self.sync and sync2 == self.sync:

    #         header = self.sock.recv(14)

    #         sync, sync, chksum, length, frame_id = unpack_header(header)

    #         # recv ACK
    #         if length == 0:     #ACK

    #             # TODO error_check
    #             message_acknowledged = True

    #             # Synchronize with send_data thread
    #             while True:
    #                 with self.ack_lock:
    #                     if not self.last_package_acknowledged:
    #                         break

    #             # Send ACK
    #             with self.ack_lock:
    #                 self.last_package_acknowledged = True

    #         else:
    #             # recv data file frame
    #             data = self.sock.recv(length)

    #             # Repeated frame
    #             if frame_id == self.last_id and chksum == self.last_checksum:

    #                 # Send ACK
    #                 with self.resend_lock:
    #                     self.resend = True
    #             else:
    #                 error = error_check(header, data)
    #                 if not error:
    #                     # Synchronize with send_data thread
    #                     while True:
    #                         with self.send_lock:
    #                             if not self.send:
    #                                 break

    #                     #ok
    #                     self.last_checksum = chksum
    #                     self.last_id = frame_id


    #                     # Send ACK
    #                     with self.send_lock:
    #                         self.send = True

    #                     write_to_file(data)



def build_frame(frame_id, data):
    #header
    sync = 0xDCC023C2
    # chksum = checksum(data)
    length = len(data)

    sync = struct.pack("!q",sync)
    length = struct.pack("!i",length)
    print 'header: ' + header
    print 'data: '  + data
    print 'header+data: ' + header+data
    chksum = checksum(header+data)
    print "Checksum: 0x%04x" % chksum
    header2 = struct.pack("!qqiii", sync,sync,chksum,length,frame_id)
    # data = struct.pack("!%dB" % len(data), *data)
    print header == header2
    for b in bytearray(header2):
        print '0x%04x '%b,
    print 
    return header,data


def decode_header(header,d):

    sync1,sync2,chksum,length,frame_id = struct.unpack("!qqiii", header)
    data = struct.unpack("!%dB" % length, d)
    print 'sync ' + str(sync1)
    print 'sync ' + str(sync2)
    print "Checksum: 0x%04x" % chksum
    print "length: " + str(length)
    print 'frame_id ' + str(frame_id)
    print data

    new_chksum = checksum(header+d)
    print 'new_chksum: 0x%04x'%new_chksum 
    print (chksum+new_chksum)%0xffff

    # def error_check(self):

def read_file(filename):
    file_byte_array = bytearray()
    with open(filename, "rb") as f:
        byte = f.read(1)
        count = 1
        while byte != "":
            # Do stuff with byte.
            file_byte_array.append(byte)

            main(bytearray(byte),count)

            byte = f.read(1)
            count += 1
    return file_byte_array


def write_file(filename, file_byte_array):

    with open(filename, "wb") as newFile:
        newFile.write(newFileByteArray)


def main(byte, count):
    data = struct.pack("%dB" % len(byte), *byte)
    build_frame(count,data)


if __name__ == '__main__':
    data = "dc c0 23 c2 dc c0 23 c2 00 00 00 04 00 00 01 02 03 04"

    data = data.split()
    # print data
    data = map(lambda x: int(x,16), data)
    # print data
    data = struct.pack("!%dB" % len(data), *data)
    print data
    print ' '.join('%02X' % ord(x) for x in data)
    print "Checksum: 0x%04x" % checksum(data)
    # print "Checksum2: 0x%04x" % checksum2(data)
    print "Checksum: %d" % checksum(data)
    # print "Checksum2: %d" % checksum2(data)


    # sync = 0xDCC023C2
    # print sync
    # d = struct.pack("!QQ", sync,sync)
    # print d
    # dd = struct.unpack('!QQ',d)
    # print dd
    data = 'jello'
    header,d = build_frame(1,data)
    print d == data
    # h = bytearray(header)
    # print len(h)
    # for b in h:
    #     print b
    # # print d
    decode_header(header,d)
    # s = 'jello'
    
    # # s = "ABCD"
    # b = bytearray(s)

    # # if your print whole b, it still displays it as if its original string
    # print b

    # # but print first item from the array to see byte value
    # print b[0]

    # data = struct.pack("!%dB" % len(s), *map(ord, list(s)))
    # length = len(s)
    # print data
    # print ' '.join('%02X' % ord(x) for x in data)
    # print "Checksum: 0x%04x" % checksum(data)
    # struct.unpack("!I%ds" % length, length, data)
    # ba = read_file('copy')