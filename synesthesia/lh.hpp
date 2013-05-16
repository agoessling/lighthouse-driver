// lh.hpp
#ifndef LH_H
#define LH_H

#include "zmq.hpp"
#include <string>
#include <stdint.h>

namespace lh{

    class Reply{
    public:
        int value;
        bool error;
        std::string str;
    };

    class Driver{
    public:
        Driver(void);
        Driver(const std::string &host, uint32_t port);
        ~Driver(void);
        Reply init(void);
        Reply connect(void);
        Reply get_num_brds(void);
        Reply set_dc(uint32_t level, uint32_t num_brds);
        Reply send_data(const uint32_t *data);
        Reply lat_data(void);
        Reply en_led(void);
        Reply dis_led(void);
    private:
        zmq::context_t *context;
        zmq::socket_t *socket;
        std::string host;
        uint32_t port;

        Reply is_initted(void);
    };

}

#endif
