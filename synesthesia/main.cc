#include <cstdlib>
#include <iostream>
#include <unistd.h>
#include "lh.hpp"
#include "zmq.hpp"

int main(){
    // Initialize Driver
    lh::Driver driver("localhost", 1873);
    driver.init();

    lh::Reply reply;

    // Connect to Boards
    reply = driver.connect();
    if(reply.error) goto process_error;
    std::cout << "Connected to Port: " << reply.str << std::endl << std::flush;

    // Get Number of Boards
    reply = driver.get_num_brds();
    if(reply.error) goto process_error;
    std::cout << "Connected to " << reply.value << " board(s)." << std::endl
                << std::flush;

    // Set DC
    reply = driver.set_dc(10, 2);
    if(reply.error) goto process_error;
    std::cout << "Set DC" << std::flush;

    // Send Data
    uint32_t data[48];
    reply = driver.send_data(&data[0]);
    if(reply.error) goto process_error;
    std::cout << "Sent dummy data." << std::flush;

    return 0;

process_error:
    std::cout << reply.str << std::flush;
    return -1;
}
