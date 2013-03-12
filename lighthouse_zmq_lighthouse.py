#!/usr/bin/python

import zmq
import lighthouse_pb2 as lh
import subprocess
import sys

def cleanup(p):
    p.terminate()
    sys.exit(0)

# Run LightHouse Driver
p = subprocess.Popen(['python', 'lighthouse.py'])

# Setup 0MQ Communication
context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect('tcp://localhost:1873')

# Create & Populate Command
cmd = lh.Command()
cmd.cmd_type = lh.Command.CONNECT

# Send Command
socket.send(cmd.SerializeToString())

# Get Response
resp = lh.Response()
resp.ParseFromString(socket.recv())

# Check For Error
if resp.HasField('error'):
    print 'Could not connect.'
    cleanup(p)

print 'Connected to {}.'.format(resp.connect_resp.port)

# Get Number of Boards
cmd = lh.Command()
cmd.cmd_type = lh.Command.NUM_BRDS

socket.send(cmd.SerializeToString())

resp = lh.Response()
resp.ParseFromString(socket.recv())

if resp.HasField('error'):
    print 'NUM BRDS Error'
    cleanup(p)

num_brds = resp.num_brds_resp.num_brds
print '{} LightHouse boards connected.'.format(num_brds)

# Set DC = 10
cmd = lh.Command()
cmd.cmd_type = lh.Command.SET_DC
cmd.set_dc.level = 10
cmd.set_dc.num_brds = num_brds

socket.send(cmd.SerializeToString())

resp = lh.Response()
resp.ParseFromString(socket.recv())

if resp.HasField('error'):
    print 'SET DC Error'
    cleanup(p)

print 'Set DC level to 10.'

# Send Data 0x7FF0
cmd = lh.Command()
cmd.cmd_type = lh.Command.SEND_DATA
cmd.send_data.data.extend([2048]*48)

socket.send(cmd.SerializeToString())

resp = lh.Response()
resp.ParseFromString(socket.recv())

if resp.HasField('error'):
    print 'SEND DATA Error'
    cleanup(p)

print 'Sent 2048 dummy data.'

# Latch Data
cmd = lh.Command()
cmd.cmd_type = lh.Command.LAT_DATA

socket.send(cmd.SerializeToString())

resp = lh.Response()
resp.ParseFromString(socket.recv())

if resp.HasField('error'):
    print 'LAT DATA Error'
    cleanup(p)

print 'Latched dummy data.'

# Enable LEDs
cmd = lh.Command()
cmd.cmd_type = lh.Command.EN_LED

socket.send(cmd.SerializeToString())

resp = lh.Response()
resp.ParseFromString(socket.recv())

if resp.HasField('error'):
    print 'EN_LED Error'
    cleanup(p)

print 'LEDs Enabled'

# Don't Forget To End Driver Process!
cleanup(p)
