#!/usr/bin/python

# Import LightHouse protobuf Schema
import lighthouse_pb2 as lh

# Create Generic Command Wrapper
command = lh.Command()
# Specify It As A Connect Command
command.cmd_type = lh.Command.CONNECT

# Specify Connect Command Details
command.connect.port = '/dev/ttyUSB0'

# Get String To Send Via 0MQ
command_str = command.SerializeToString


# Create Dummy Response To Receive
# You shouldn't have to do this,
# these will come from the lighthouse driver
resp = lh.Response()
resp.cmd = lh.Command.CONNECT
resp.error.error_type = lh.Error.NO_PORT
resp.error.string = 'The port: "/dev/ttyUSB0" is not available.'
resp_str = resp.SerializeToString()

# Receive And Process Response
# Create New Response To Copy Data to from 0MQ
resp = lh.Response()
# Parse Data From 0MQ
resp.ParseFromString(resp_str)

# You Now Have The Response And All Of Its Contents
if resp.HasField('error'):
    print resp.error.string
