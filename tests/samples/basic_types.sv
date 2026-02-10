package test_pkg;
    typedef enum logic [1:0] { IDLE=0, BUSY=1, ERR=2 } state_e;
    typedef struct packed {
        logic [7:0] header;
        state_e status;
        logic [5:0] payload;
    } packet_t;
endpackage
