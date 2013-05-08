// lh.hpp
#ifndef LH_H
#define LH_H

#include <string>
#include "zmq.hpp"

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
        Driver(const std::string &host, int port);
        ~Driver(void);
        Reply init(void);
        Reply connect(void);
        Reply get_num_brds(void);
        Reply set_dc(int level);
        Reply send_data(const int *data);
        Reply lat_data(void);
        Reply en_led(void);
        Reply dis_led(void);
    private:
        zmq::context_t *context;
        zmq::socket_t *socket;
        std::string host;
        int port;

        Reply is_initted(void);
    };

}

#endif
