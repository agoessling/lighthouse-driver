// lh.cc

#include "lh.hpp"
#include "lighthouse.pb.h"
#include <sstream>
#include <iostream>

lh::Driver::Driver(void){
    host = "localhost";
    port = 1873;
}

lh::Driver::Driver(const std::string &target_host, int target_port){
    host = target_host;
    port = target_port;
}

lh::Driver::~Driver(void){
    delete context;
    delete socket;
}

lh::Reply lh::Driver::init(void){
    //delete context;
    //delete socket;

    // One Thread
    context = new zmq::context_t(1);
    socket = new zmq::socket_t(*context, ZMQ_REQ);

    std::ostringstream stream;
    stream << "tcp://" << host << ":" << port;
    std::string addr = stream.str();
    socket->connect(addr.c_str());

    //TODO: Catch Problems
    lh::Reply reply;
    reply.error = false;

    return reply;
}

lh::Reply lh::Driver::connect(void){
    lh::Reply reply;

    // Ensure Initialization
    reply = is_initted();
    if(reply.error)
        return reply;

    // Create Connect Command
    lh::Command cmd;
    cmd.set_cmd_type(lh::Command::CONNECT); 

    // Serialize Command
    std::string msg;
    cmd.SerializeToString(&msg);

    // Send Command
    zmq::message_t request((void *)msg.data(), msg.length(), NULL);
    socket->send(request);

    // Get Reply
    zmq::message_t zmq_reply;
    socket->recv(&zmq_reply);
    std::string zmq_data = (const char *)zmq_reply.data();

    // Parse Response
    lh::Response resp;
    resp.ParseFromString(zmq_data);

    // Error
    // TODO: Make this more descriptive
    if(resp.has_error()){
        reply.error = true;
        reply.str = "Could not connect.";
        return reply;
    }

    // Success
    reply.error = false;
    reply.str = resp.connect_resp().port();
    return reply;
}

lh::Reply lh::Driver::get_num_brds(void){
    lh::Reply reply;

    // Ensure Initialization
    reply = is_initted();
    if(reply.error)
        return reply;

    // Create NUM_BRDS Command
    lh::Command cmd;
    cmd.set_cmd_type(lh::Command::NUM_BRDS); 

    // Serialize Command
    std::string msg;
    cmd.SerializeToString(&msg);

    // Send Command
    zmq::message_t request((void *)msg.data(), msg.length(), NULL);
    socket->send(request);

    // Get Reply
    zmq::message_t zmq_reply;
    socket->recv(&zmq_reply);
    std::string zmq_data = (const char *)zmq_reply.data();

    // Parse Response
    lh::Response resp;
    resp.ParseFromString(zmq_data);

    // Error
    // TODO: Make this more descriptive
    if(resp.has_error()){
        reply.error = true;
        reply.str = "Could not get number of boards.";
        return reply;
    }

    // Success
    reply.error = false;
    reply.value = resp.num_brds_resp().num_brds();
    return reply;
}

lh::Reply lh::Driver::is_initted(void){
    lh::Reply reply;

    if(context && socket){
        reply.error = false;
        return reply;
    }
    else{
        reply.error = true;
        reply.str = "Driver not initialized.";
        return reply;
    }
}
