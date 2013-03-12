lighthouse-driver
=================

Driver which provides an API to LightHouse.

*lighthouse.proto* -- This file describes the API structure used by [protobuf](https://developers.google.com/protocol-buffers/docs/overview).

*lighthouse_protobuf_demo.py* -- This file provides a very simple demonstration of interacting with the LightHouse protobuf API in python.

*lighthouse_zmq_demo.py* -- This file provides a very simple demonstration of using [zeromq](http://www.zeromq.org/) as the transport mechanism for the driver API.

*lighthouse.py* -- This is the actual driver that receives API calls from ZMQ and communicates with the hardware over the serial port.
This will be what the emulator will emulate - accepting commands over ZMQ and updating an on-screen display accordingly.
