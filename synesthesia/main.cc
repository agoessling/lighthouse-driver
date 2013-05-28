#include <cstdlib>
#include <iostream>
#include <unistd.h>
#include "lh.hpp"
#include "zmq.hpp"

void rotate(int, uint32_t *, unsigned int);

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
    std::cout << "Set DC" << std::endl << std::flush;

    // Send Data
    uint32_t data[48];

    for(int i=0; i<16; i++){
        data[3*i] = 0;
        data[3*i+1] = 0;
        data[3*i+2] = 0;
    }

    reply = driver.send_data(&data[0]);
    if(reply.error) goto process_error;
    reply = driver.send_data(&data[0]);
    if(reply.error) goto process_error;

    std::cout << "Sent dummy data." << std::endl << std::flush;

    // Latch Data
    reply = driver.lat_data();
    if(reply.error) goto process_error;
    std::cout << "Latched data." << std::endl << std::flush;

    // Enable LEDs
    reply = driver.en_led();
    if(reply.error) goto process_error;
    std::cout << "Enabled LEDs." << std::endl << std::flush;

    return 0;

process_error:
    std::cout << reply.str << std::flush;
    return -1;
}

void rotate(int dir, uint32_t *data, unsigned int len){
    // abs(dir) <= len!!
    unsigned int dir_len = abs(dir);
    uint32_t *temp = new uint32_t[dir_len];

    // Right Shift [1,2,3,4,5] -> [5,1,2,3,4]
    if(dir >= 0){
        memcpy(temp, data+len-dir, (dir)*sizeof(uint32_t));
        memmove(data+dir, data, (len-dir)*sizeof(uint32_t));
        memcpy(data, temp, (dir)*sizeof(uint32_t));    
    }
    // Left Shift [1,2,3,4,5] -> [2,3,4,5,1]
    else{
        memcpy(temp, data, (-dir)*sizeof(uint32_t));
        memmove(data, data-dir, (len+dir)*sizeof(uint32_t));
        memcpy(data+len+dir, temp, (-dir)*sizeof(uint32_t));    
    }

    delete[] temp;
}
