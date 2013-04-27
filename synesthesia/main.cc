#include <cstdlib>
#include "lh.hpp"
#include "zmq.hpp"

int main(){
    // Start LightHouse Driver
    std::system("python ../lighthouse.py");

    // Setup 0MQ Communication
    // One Thread
    zmq::context_t context(1);
    zmq::socket_t socket(context, ZMQ_REQ);
    socket.bind("tcp://localhost:1873");

    return 0;
}
