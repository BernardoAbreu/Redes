#!/usr/bin/env python

import sys
import socket

#from struct import pack
import struct
import time
import Queue as queue
import array
import threading

WRONG_CHKSUM = 1

class ChecksumException(Exception):
    pass

SYNC = 0xDCC023C2


def _carry_around_add(a, b):
    c = a + b
    return (c & 0xffff) + (c >> 16)

def checksum(msg):
    s = 0
    if len(msg) % 2 == 1:
            msg += "\0"
    for i in range(0, len(msg),2):
        w = (ord(msg[i]) << 8) + (ord(msg[i+1]))
        s = _carry_around_add(s, w)
    return (~s) & 0xffff



class Server():

    def __init__(self):
        self.HOST = '127.0.0.1'
        self.PORT = 51515
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.HOST,self.PORT))
        self.sock.listen(1)
        self.counter = 0
        self.sync = SYNC

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



def build_frame(frame_id, data = []):
    #header

    length = len(data)
    
    header = struct.pack('!IIHHH', SYNC, SYNC, 0, length, frame_id)
    # print ' '.join('%02X' % ord(x) for x in header)

    data = struct.pack("!%dB" % len(data), *data)

    frame_str = header+data
    # print frame_str

    chcksum = checksum(frame_str)
    # print "Checksum: 0x%04x" % chcksum
    # print "Checksum: %d" % chcksum

    frame = bytearray(frame_str)
    frame[8] = chcksum >> 8
    frame[9] = chcksum & 0xff
    frame_str = str(frame)

    # print frame_str
    # chcksum = checksum(frame_str)
    # print "Checksum: 0x%04x" % chcksum
    # print "Checksum: %d" % chcksum

    return frame_str



def decode_header(syncless_header):
    chksum,length,frame_id = struct.unpack('!HHH',syncless_header)
    return chksum, length, frame_id


def read_file(filename):
    file_byte_array = bytearray()
    with open(filename, "rb") as f:
        byte = f.read(1024)
        while byte != "":
            # Do stuff with byte.
            print(len(byte))
            file_byte_array.extend(byte)
            byte = f.read(1024)


    return file_byte_array



def write_file(filename, file_byte_array):

    with open(filename, "wb") as newFile:
        newFile.write(newFileByteArray)



def recv_valid_synced_frame():
    last_sync = 0
    try:
        while True:
            while current_sync == SYNC and last_sync == SYNC:
                last_sync = current_sync
                current_sync = self.sock.recv(4)

            syncless_header = self.sock.recv(6)

            data = ''
            chksum, length, frame_id = decode_header(syncless_header)

            if length:
                data = self.sock.recv(length)

            frame = last_sync + current_sync + chcksum + length + frame_id + data


            if not checksum(frame):
                return chksum, length, frame_id, data
            else:
                current_sync = 0

    except Exception as e:
        raise e



def main():
    frame_id = 0
    last_frame_id = 1
    last_checksum = 0
    with open(filename, "rb") as f:
        byte = f.read(1)

        current_frame = build_frame(frame_id, byte)
        send_frame(current_frame)
        # Get send time

        while byte != "":
            # TODO Resend data after 1 sec
            try:
                # pass send time and frame
                # store as instance value?
                chksum, length, recv_frame_id, data = recv_valid_synced_frame()
            except Exception as e:
                print e

            if length:  # Data
                if recv_frame_id != last_frame_id or chksum == last_checksum:
                    # New data
                    if recv_frame_id != last_frame_id:
                        last_frame_id = recv_frame_id
                        last_checksum = chksum
                        # Resend ACK
                    
                    ack_frame = build_frame(frame_id)
                    send_frame(ack_frame)

                    # write data
                    # separate thread

            else:  # ACK
                print
                # Check ACK

                # if ACK valid:
                # update frame_id
                # read new byte
                byte = f.read(1024)
                # send new frame
                # get send time




if __name__ == '__main__':
    data = "dc c0 23 c2 dc c0 23 c2 00 00 00 04 00 00 01 02 03 04"
    # data = "dc c0 23 c2 dc c0 23 c2 00 00 00 00 00 00"

    data = data.split()
    # print data
    data = map(lambda x: int(x,16), data)
    # print data
    data = struct.pack("!%dB" % len(data), *data)
    print data
    print ' '.join('%02X' % ord(x) for x in data)
    print "Checksum: 0x%04x" % checksum(data)
    print "Checksum: %d" % checksum(data)
    # first = checksum(data)
    # print checksum(data)
    # print ' '.join(format(ord(x), 'b') for x in data)
    # data = bytearray(data)
    # data[8] = first >> 8
    # data[9] = first & 0xff
    # print "0x%02x"%data[8]
    # print "0x%02x"%data[9]
    # data = str(data)
    # print ' '.join(format(ord(x), 'b') for x in data)
    # print data

    # # data = bytearstruct.pack('!H',checksum(data))
    # # print ' '.join(format(ord(x), 'b') for x in data)
    
    # second = checksum(data)
    # print second
    
    # frame = build_frame(0,bytearray([0x01, 0x02, 0x03, 0x04]))

    # sync1, sync2, chksum,length,frame_id = struct.unpack('!IIHHH',frame[:14])
    # print '%02X' % sync1
    # print '%02X' % sync2
    # print '0x%02x' % chksum
    # print length
    # print frame_id
    # print decode_header(frame[8:14])
    # print checksum(frame)

    # frame = build_frame(0)
    # sync1, sync2, chksum,length,frame_id = struct.unpack('!IIHHH',frame[:14])
    # print '%02X' % sync1
    # print '%02X' % sync2
    # print '0x%02x' % chksum
    # print length
    # print frame_id
    # print decode_header(frame[8:14])
    # print checksum(frame)
    # print ' '.join('%02X' % ord(x) for x in frame)

    # print "{0:b}".format(second)
    # print "{0:b}".format(first)
    # print "{0:b}".format(first+second)

    # print "Checksum: %d" % checksum('\xFA\xFC')
    # print "Checksum: %d" % checksum2('\xFA\xFC')
    # checj('\xFA\xFC')
    # checksum2(data)
    # sync = 0xDCC023C2
    # print sync
    # d = struct.pack("!QQ", sync,sync)
    # print d
    # dd = struct.unpack('!QQ',d)
    # print dd
    # data = 'jello'
    # header,d = build_frame(1,data)
    # print d == data
    # # h = bytearray(header)
    # # print len(h)
    # # for b in h:
    # #     print b
    # # # print d
    # decode_header(header,d)
    # # s = 'jello'
    
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
    ba = read_file('copy')