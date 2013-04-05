#!/usr/bin/python

import argparse
import array
import collections
import lighthouse_pb2 as lh
from google.protobuf.message import EncodeError
import math
import serial
# Don't why this won't import correctly, but this works...
from serial.tools.list_ports import grep as port_grep
import time
from Tkinter import *
import ttk
import zmq

## This is the base class used by the emulator and real (hardware) driver ##
class LightHouseBase():
    # Constants
    _SERIAL_BAUD = 250000

    _PC_SFLAG = 0x7E
    _PC_ESCP = 0x7D
    _PC_ESFLAG = 0x5E
    _PC_EESCP = 0x5D

    _CMD_CONNECT = 0x01
    _CMD_DISCONNECT = 0x02
    _CMD_HELLO = 0x03
    _CMD_ACK = 0x04
    _CMD_EN_LED = 0x05
    _CMD_DIS_LED = 0x06
    _CMD_SEND_DATA = 0x07
    _CMD_LAT_DATA = 0x08
    _CMD_SET_DC = 0x09
    _CMD_NUM_BRDS = 0x0A


    def setup_zmq(self):
        # Setup 0MQ
        context = zmq.Context()

        # Listen For Commands on Port 1873
        # How Far is it to NYC?
        socket = context.socket(zmq.REP)
        socket.bind('tcp://*:1873')

        return socket
        

    def poll_zmq(self, socket):
        # Create and Parse Command
        cmd = lh.Command()

        try:
            cmd.ParseFromString(socket.recv(flags=zmq.NOBLOCK))

        # No Message Ready
        except zmq.ZMQError:
            return True

        # Parse Decode Error
        except EncodeError:
            # Create Response
            resp = lh.Response()
            # Dummy cmd Type
            resp.cmd = lh.Command.HELLO
            resp.error.error_type = lh.Error.UNKWN_CMD
            resp.error.string = 'Unable to parse string as command.'
            # Send Response
            socket.send(resp.SerializeToString())
            # Skip To Next Command Parse
            return False

        # Send Command To Correct Handling Function
        if cmd.cmd_type == lh.Command.CONNECT:
            resp = self.connect(cmd)
        elif cmd.cmd_type == lh.Command.DISCONNECT:
            resp = self.disconnect(cmd)
        elif cmd.cmd_type == lh.Command.HELLO:
            resp = self.hello(cmd)
        elif cmd.cmd_type == lh.Command.EN_LED:
            resp = self.en_led(cmd)
        elif cmd.cmd_type == lh.Command.DIS_LED:
            resp = self.dis_led(cmd)
        elif cmd.cmd_type == lh.Command.SET_DC:
            resp = self.set_dc(cmd)
        elif cmd.cmd_type == lh.Command.SEND_DATA:
            resp = self.send_data(cmd)
        elif cmd.cmd_type == lh.Command.LAT_DATA:
            resp = self.lat_data(cmd)
        elif cmd.cmd_type == lh.Command.NUM_BRDS:
            resp = self.num_brds(cmd)
        # Unrecognized Command
        else:
            # Error Response
            resp = lh.Response()
            resp.cmd = cmd.cmd_type
            resp.error.error_type = lh.Error.UNKWN_CMD
            resp.error.string = 'Unknown command type.'

        # Send Response
        socket.send(resp.SerializeToString())
        return True


    def resp_unformed_cmd(self, cmd, string='Command not fully formed.'):
        resp = lh.Response()
        resp.cmd = cmd.cmd_type
        resp.error.error_type = lh.Error.UNFMD_CMD
        resp.error.string = string

        return resp


class LightHouseEmulator(LightHouseBase):
    _CANVAS_BORDER = 10

    def __init__(self, row_num, col_num):
        root = Tk()
        root.title('LightHouse Emulator')

        content = ttk.Frame(root)
        canvas = Canvas(content, width=600, height=600)
        log_frame = ttk.Frame(content)
        log_text = Text(log_frame, height=8, state='disabled')
        log_scroll = ttk.Scrollbar(log_frame,
                            orient=VERTICAL,
                            command=log_text.yview)
        log_text.configure(yscrollcommand=log_scroll.set)

        content.grid(column=0, row=0, sticky=W+E+N+S)
        canvas.grid(column=0, row=0, sticky=W+E+N+S)
        log_frame.grid(column=0, row=1, stick=W+E)
        log_text.grid(column=0, row=0, sticky=W+E)
        log_scroll.grid(column=1, row=0, sticky=N+S)

        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(0, weight=1)

        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)

        canvas.bind('<Configure>', self.redraw_canvas)

        c_width = int(canvas['width'])
        c_height = int(canvas['height'])

        cell_size = min((c_width-2*self._CANVAS_BORDER)/col_num,
                            (c_height-2*self._CANVAS_BORDER)/row_num)

        cells = []

        for row in range(row_num):
            for col in range(col_num):
                cell = canvas.create_rectangle(
                                        cell_size*col+self._CANVAS_BORDER,
                                        cell_size*row+self._CANVAS_BORDER,
                                        cell_size*(col+1)+self._CANVAS_BORDER,
                                        cell_size*(row+1)+self._CANVAS_BORDER,
                                        fill='black',
                                        width=3)
                cells.append(cell)

        self.root = root
        self.canvas = canvas
        self.log_text = log_text

        self.row_num = row_num
        self.col_num = col_num
        self.cells = cells
        self.latched_data = collections.deque([0]*(len(cells)*3),
                                            3*len(cells))
        self.reg_data = collections.deque([0]*(len(cells)*3),
                                            3*len(cells))


    def log(self, text):
        self.log_text.configure(state='normal')
        self.log_text.insert(END, text)
        self.log_text.configure(state='disabled')


    def redraw_canvas(self, event):
        c_width = event.width
        c_height = event.height
        cell_size = min((c_width-2*self._CANVAS_BORDER)/self.col_num,
                            (c_height-2*self._CANVAS_BORDER)/self.row_num)

        i = 0

        for row in range(self.row_num):
            for col in range(self.col_num):
                self.canvas.coords(self.cells[i],
                                cell_size*col+self._CANVAS_BORDER,
                                cell_size*row+self._CANVAS_BORDER,
                                cell_size*(col+1)+self._CANVAS_BORDER,
                                cell_size*(row+1)+self._CANVAS_BORDER)
                i += 1


    def update_cell_color(self, color_list):
        for i in range(len(self.cells)):
            color = '#{:03x}{:03x}{:03x}'.format(color_list[-3*i-3],
                                                 color_list[-3*i-2],
                                                 color_list[-3*i-1])
            self.canvas.itemconfig(self.cells[i], fill=color)

    
    def poll_zmq_wrapper(self):
        self.poll_zmq(self.socket)
        self.root.after(5, self.poll_zmq_wrapper)
        

    def run(self):
        # Setup 0MQ
        self.socket = self.setup_zmq()

        # Schedule 0MQ Polling
        self.root.after(5, self.poll_zmq_wrapper)

        # Run GUI Loop
        self.root.mainloop()


    def connect(self, cmd):
        self.log('Received CONNECT command\n')
        resp = lh.Response()
        resp.cmd = cmd.cmd_type
        resp.connect_resp.port = 'EMULATOR'
        return resp

    def disconnect(self, cmd):
        self.log('Received DISCONNECT command\n')
        resp = lh.Response()
        resp.cmd = cmd.cmd_type
        return resp

    def hello(self, cmd):
        self.log('Received HELLO command\n')
        resp = lh.Response()
        resp.cmd = cmd.cmd_type
        return resp
         
    def en_led(self, cmd):
        self.log('Received EN_LED command\n')
        self.update_cell_color(self.latched_data)
        resp = lh.Response()
        resp.cmd = cmd.cmd_type
        return resp

    def dis_led(self, cmd):
        self.log('Received DIS_LED command\n')
        self.update_cell_color([0]*(3*len(self.cells)))
        resp = lh.Response()
        resp.cmd = cmd.cmd_type
        return resp

    def lat_data(self, cmd):
        self.latched_data = self.reg_data
        self.update_cell_color(self.latched_data)
        resp = lh.Response()
        resp.cmd = cmd.cmd_type
        return resp

    def set_dc(self, cmd):
        # No DC Data
        if not cmd.set_dc:
            return self.resp_unformed_cmd(cmd, 'No DC Data')

        self.log('Received SET_DC command with: {}\n'.format(cmd.set_dc.level))
        resp = lh.Response()
        resp.cmd = cmd.cmd_type
        return resp

    def send_data(self, cmd):
        # No GS Data
        if not cmd.send_data:
            return self.resp_unformed_cmd(cmd, 'No GS Data')

        # Incorrect Data Length
        if not len(cmd.send_data.data) == 48:
            return self.resp_unformed_cmd(cmd, 'Wrong Data Length')

        self.reg_data.extend(cmd.send_data.data)

        resp = lh.Response()
        resp.cmd = cmd.cmd_type
        return resp

    def num_brds(self, cmd):
        num_brds = int(math.ceil(len(self.cells)/16.0))
        self.log('Received NUM_BRDS command sent: {}\n'.format(num_brds))

        resp = lh.Response()
        resp.cmd = cmd.cmd_type
        resp.num_brds_resp.num_brds = num_brds
        return resp


## This is the class instantiated for real (hardware) interaction ##
class LightHouse(LightHouseBase):
    def __init__(self):
        self._ser = None

    
    def run(self):
        # Setup 0MQ
        socket = self.setup_zmq()

        # Wait For and Process Commands
        while self.poll_zmq(socket):
            pass
        

    def cleanup(self):
        if self._ser:
            self._ser.close()
            self._ser = None


    def connect(self, cmd):
        # Close Port If Open
        self.cleanup()

        # Specific Port
        if cmd.connect and cmd.connect.port:
            try:
                self._ser = serial.Serial(
                    cmd.connect.port,
                    self._SERIAL_BAUD,
                    timeout=0.5
                )
            except (ValueError, serial.SerialException) as e:
                resp = lh.Response()
                resp.cmd = cmd.cmd_type
                resp.error.error_type = lh.Error.NO_PORT
                resp.error.string = 'Unable to connect to port.'
                resp.connect_resp.port = cmd.connect.port
                return resp
            
            # Try To Say Hello
            resp = self.hello(cmd)
            # If LightHouse Board Responds
            if not resp.HasField('error'):
                resp = lh.Response()
                resp.cmd = cmd.cmd_type
                resp.connect_resp.port = cmd.connect.port
                return resp
            # If No Response
            else:
                self.cleanup()
                resp = lh.Response()
                resp.cmd = cmd.cmd_type
                resp.error.error_type = lh.Error.NO_BRD
                resp.error.string = 'No LightHouse boards responded.'
                resp.connect_resp.port = cmd.connect.port
                return resp

        # Auto Find
        else:
            for port_name in port_grep(r'.+(COM|USB|tty\.).+'):
                try:
                    self._ser = serial.Serial(
                        port_name[0],
                        self._SERIAL_BAUD,
                        timeout=0.5
                    )
                except (ValueError, serial.SerialException) as e:
                    # If Problems With Port Continue To Next
                    continue

                # Try To Say Hello
                resp = self.hello(cmd)
                # If LightHouse Board Responds
                if not resp.HasField('error'):
                    resp = lh.Response()
                    resp.cmd = cmd.cmd_type
                    resp.connect_resp.port = port_name[0]
                    return resp

                # No Response
                else:
                    self.cleanup()

            # If Nothing Responds
            resp = lh.Response()
            resp.cmd = cmd.cmd_type
            resp.error.error_type = lh.Error.NO_BRD
            resp.error.string = 'No LightHouse boards responded.'
            return resp


    def disconnect(self, cmd):
        self.cleanup()

        resp = lh.Response()
        resp.cmd = cmd.cmd_type

        return resp


    def hello(self, cmd):
        # Say Hello To Board
        self.send_cmd(self._CMD_HELLO, data=[])
        lh_resp = self.get_resp(self._CMD_HELLO)

        # RX Serial Timeout
        if not lh_resp:
            resp = lh.Response()
            resp.cmd = cmd.cmd_type
            resp.error.error_type = lh.Error.NO_BRD
            resp.error.string = 'Serial Timeout.'
            return resp

        # Success
        else:
            resp = lh.Response()
            resp.cmd = cmd.cmd_type
            return resp


    def en_led(self, cmd):
        self.send_cmd(self._CMD_EN_LED, data=[])
        lh_resp = self.get_resp(self._CMD_EN_LED)

        # RX Serial Timeout
        if not lh_resp:
            resp = lh.Response()
            resp.cmd = cmd.cmd_type
            resp.error.error_type = lh.Error.NO_BRD
            resp.error.string = 'Serial Timeout.'
            return resp

        # Success
        else:
            resp = lh.Response()
            resp.cmd = cmd.cmd_type
            return resp


    def dis_led(self, cmd):
        self.send_cmd(self._CMD_DIS_LED, data=[])
        lh_resp = self.get_resp(self._CMD_DIS_LED)

        # RX Serial Timeout
        if not lh_resp:
            resp = lh.Response()
            resp.cmd = cmd.cmd_type
            resp.error.error_type = lh.Error.NO_BRD
            resp.error.string = 'Serial Timeout.'
            return resp

        # Success
        else:
            resp = lh.Response()
            resp.cmd = cmd.cmd_type
            return resp


    def lat_data(self, cmd):
        self.send_cmd(self._CMD_LAT_DATA, data=[])
        lh_resp = self.get_resp(self._CMD_LAT_DATA)

        # RX Serial Timeout
        if not lh_resp:
            resp = lh.Response()
            resp.cmd = cmd.cmd_type
            resp.error.error_type = lh.Error.NO_BRD
            resp.error.string = 'Serial Timeout.'
            return resp

        # Success
        else:
            resp = lh.Response()
            resp.cmd = cmd.cmd_type
            return resp


    def set_dc(self, cmd):
        # No DC Data
        if not cmd.set_dc:
            return self.resp_unformed_cmd(cmd)
        
        # Level Out Of Bounds
        if cmd.set_dc.level > 63:
            cmd.set_dc.level = 63

        # Send CMD
        self.send_cmd(
            self._CMD_SET_DC,
            data=[cmd.set_dc.level, cmd.set_dc.num_brds]
        )
        lh_resp = self.get_resp(self._CMD_SET_DC)

        # RX Serial Timeout
        if not lh_resp:
            resp = lh.Response()
            resp.cmd = cmd.cmd_type
            resp.error.error_type = lh.Error.NO_BRD
            resp.error.string = 'Serial Timeout.'
            return resp

        # Success
        else:
            resp = lh.Response()
            resp.cmd = cmd.cmd_type
            return resp


    def send_data(self, cmd):
        # No GS Data
        if not cmd.send_data:
            return self.resp_unformed_cmd(cmd, 'No GS Data')

        # Incorrect Data Length
        if not len(cmd.send_data.data) == 48:
            return self.resp_unformed_cmd(cmd, 'Wrong Data Length')

        # Send CMD
        self.send_cmd(
            self._CMD_SEND_DATA,
            data=self.pack_gs_data(cmd.send_data.data)
        )
        lh_resp = self.get_resp(self._CMD_SEND_DATA)

        # RX Serial Timeout
        if not lh_resp:
            resp = lh.Response()
            resp.cmd = cmd.cmd_type
            resp.error.error_type = lh.Error.NO_BRD
            resp.error.string = 'Serial Timeout.'
            return resp

        # Success
        else:
            resp = lh.Response()
            resp.cmd = cmd.cmd_type
            return resp


    def num_brds(self, cmd):
        # Send CMD
        self.send_cmd(self._CMD_NUM_BRDS, data=[])
        lh_resp = self.get_resp(self._CMD_NUM_BRDS)

        # RX Serial Timeout
        if not lh_resp:
            resp = lh.Response()
            resp.cmd = cmd.cmd_type
            resp.error.error_type = lh.Error.NO_BRD
            resp.error.string = 'Serial Timeout.'
            return resp

        # Success
        else:
            resp = lh.Response()
            resp.cmd = cmd.cmd_type
            resp.num_brds_resp.num_brds = lh_resp['data'][1]
            return resp
        

    def pack_gs_data(self, data):
        pkt = array.array('B')

        for (i,val) in enumerate(data):
            # Negative
            if val < 0:
                val = 0
            # Positive
            if val > 4095:
                val = 4095

            if i%2:
                pkt[len(pkt)-1] |= (val>>8)&0x0F
                pkt.append(val&0xFF)
            else:
                pkt.append((val>>4)&0xFF)
                pkt.append((val<<4)&0xF0)

        return pkt
     
            
    def send_cmd(self, cmd, data=[]):
        pkt = array.array('B')
                    
        pkt.append(self._PC_SFLAG)
                                    
        pkt.append(self.escape_byte(cmd))
                                                        
        pkt.append(self.escape_byte(len(data)))
                                                                        
        for byte in data:
            pkt.append(self.escape_byte(byte))

        pkt.append(self._PC_SFLAG)

        self._ser.write(pkt.tostring())


    def escape_byte(self, byte):
        if byte == self._PC_SFLAG:
            return [self._PC_ESCP, self._PC_ESFLAG]
        elif byte == self._PC_ESCP:
            return [self._PC_ESCP, self._PC_EESCP]
        else:
            return byte


    def get_resp(self, cmd):
        got_resp = False
        got_pkt = False
        got_start = False
        pkt = []

        while not got_resp:
            while not got_pkt:
                while not got_start:
                    byte = self.get_unescaped_byte()
                    if byte < 0:
                        return None

                    if byte == self._PC_SFLAG:
                        got_start = True

                byte = self.get_unescaped_byte()
                if byte < 0:
                    return None

                if byte == self._PC_SFLAG:
                    got_pkt = True
                else:
                    pkt.append(byte)

            if len(pkt) >= 3:                   # Packet Long Enough
                if len(pkt) == 2+pkt[1]:        # Length Matches
                    if pkt[0] == self._CMD_ACK: # Is Acknowledge
                        if pkt[2] == cmd:       # Right Command
                            got_resp = True
                            break
            got_pkt = False
            got_start = True

        return {'cmd':pkt[0], 'len':pkt[1], 'data':pkt[2:]}


    def get_byte(self):
        chars = array.array('B', self._ser.read())
        if len(chars)==0:
            return -1
        else:
            return chars[0]


    def get_unescaped_byte(self):
        byte = self.get_byte()
        if byte < 0:
            return -1

        if byte == self._PC_ESCP:
            next_byte = self.get_byte()
            if next_byte < 0:
                return -1

            if next_byte == self._PC_ESFLAG:
                return self._PC_SFLAG
            elif next_byte == self._PC_EESCP:
                return self._PC_ESCP
            else:
                return -1

        else:
            return byte


def col_row_checker(string):
    try:
        row,col = string.split('x',1)
        col = int(col)
        row = int(row)
        return {'col':col, 'row':row}
    except:
        msg = "%r is not in the correct COLxROW format"%string
        raise argparse.ArgumentTypeError(msg)


# Run main() When Run as Script
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--emulator',
                type=col_row_checker,
                help='use on-screen emulator for display'
                        ' - takes ROWxCOL argument.')
    args = parser.parse_args()

    if args.emulator:
        lh_driver = LightHouseEmulator(args.emulator['row'],
                                        args.emulator['col'])
    else:
        lh_driver = LightHouse()

    lh_driver.run()
