#!/usr/bin/python

import collections
import lighthouse_pb2 as lh
import subprocess
import sys
import zmq

class Torch():

    def __init__(self):
        # Run LightHouse Driver
        self.p = subprocess.Popen(
            #['python', 'lighthouse.py']
            ['python', 'lighthouse.py', '-e', '8x4']
        )

        # Setup 0MQ Communication
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect('tcp://localhost:1873')

        # Constants
        self.dc_level = 20 
        self.num_brds = 1
        

    def run(self):
        # Attempt To Connect
        port = self.connect()
        print 'Connected to: {}'.format(port)

        # Get Number Of Boards
        self.num_brds = self.get_num_brds()
        print 'Talking to {} LightHouse Boards.'.format(self.num_brds)

        # Set DC Level
        self.set_dc(self.dc_level)
        print 'DC level set to {}.'.format(self.dc_level)

        # Send Zero Data
        for x in range(self.num_brds):
            self.send_data([0]*48)
        print 'Sent zero data.'

        # Latch LED Data
        self.lat_data()
        print 'LED data latched.'

        # EN LEDs
        self.en_led()
        print 'LEDs enabled.'

        frame = collections.deque([(1,0,1)]+[(0,0,0)]*31, 32)
        
        try:
            while True:
                self.send_frame(frame)
                self.lat_data()
                frame.rotate()

        except KeyboardInterrupt:
            # DIS LEDs
            self.dis_led()
            print 'LEDs disabled.'

            self.cleanup()


    def cleanup(self):
        self.p.terminate()
        self.socket.close()
        sys.exit(0)


    def send_frame(self, frame):
        if not (len(frame)%16) == 0:
            raise ValueError('Frame length not a multiple of 16.')

        for i in range(len(frame)/16):
            x = []
            for j in range(1,17):
                # Red
                x.append(int(4095*min(1, frame[-(16*i+j)][0])))
                # Green
                x.append(int(4095*min(1, frame[-(16*i+j)][1])))
                # Blue
                x.append(int(4095*min(1, frame[-(16*i+j)][2])))

            self.send_data(x)




    def connect(self):
        cmd = lh.Command()
        cmd.cmd_type = lh.Command.CONNECT

        self.socket.send(cmd.SerializeToString())

        resp = lh.Response()
        resp.ParseFromString(self.socket.recv())

        if resp.HasField('error'):
            print 'Could not connect.'
            print resp.error
            self.cleanup()  

        return resp.connect_resp.port


    def get_num_brds(self):
        cmd = lh.Command()
        cmd.cmd_type = lh.Command.NUM_BRDS

        self.socket.send(cmd.SerializeToString())

        resp = lh.Response()
        resp.ParseFromString(self.socket.recv())

        if resp.HasField('error'):
            print 'Could get number of boards.'
            print resp.error
            self.cleanup()  

        return resp.num_brds_resp.num_brds


    def set_dc(self, level):
        cmd = lh.Command()
        cmd.cmd_type = lh.Command.SET_DC
        cmd.set_dc.level = level
        cmd.set_dc.num_brds = self.num_brds

        self.socket.send(cmd.SerializeToString())

        resp = lh.Response()
        resp.ParseFromString(self.socket.recv())

        if resp.HasField('error'):
            print 'Could not set DC level.'
            print resp.error
            self.cleanup()  


    def send_data(self, data):
        if not len(data) == 48:
            raise ValueError('Data length not 48.')

        cmd = lh.Command()
        cmd.cmd_type = lh.Command.SEND_DATA

        cmd.send_data.data.extend(data)

        self.socket.send(cmd.SerializeToString())

        resp = lh.Response()
        resp.ParseFromString(self.socket.recv())

        if resp.HasField('error'):
            print 'Could not send zero data.'
            print resp.error
            self.cleanup()  


    def lat_data(self):
        cmd = lh.Command()
        cmd.cmd_type = lh.Command.LAT_DATA

        self.socket.send(cmd.SerializeToString())

        resp = lh.Response()
        resp.ParseFromString(self.socket.recv())

        if resp.HasField('error'):
            print 'Could not latch data.'
            print resp.error
            self.cleanup()  


    def en_led(self):
        cmd = lh.Command()
        cmd.cmd_type = lh.Command.EN_LED

        self.socket.send(cmd.SerializeToString())

        resp = lh.Response()
        resp.ParseFromString(self.socket.recv())

        if resp.HasField('error'):
            print 'Could not enable LEDs.'
            print resp.error
            self.cleanup()  


    def dis_led(self):
        cmd = lh.Command()
        cmd.cmd_type = lh.Command.DIS_LED

        self.socket.send(cmd.SerializeToString())

        resp = lh.Response()
        resp.ParseFromString(self.socket.recv())

        if resp.HasField('error'):
            print 'Could not disable LEDs.'
            print resp.error
            self.cleanup()  


if __name__ == '__main__':
    t = Torch()
    t.run()
