// lh.hpp
#ifndef LH_H
#define LH_H

#include <string>

namespace lh{

    class response{
    public:
        int value;
        bool error;
        std::string str;
    };
        
    response connect(void);
    response get_num_brds(void);
    response set_dc(int);
    response send_data(int *);
    response lat_data(void);
    response en_led(void);
    response dis_led(void);

}

#endif
