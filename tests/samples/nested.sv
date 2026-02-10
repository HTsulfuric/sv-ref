package test_pkg;
    typedef struct packed { logic [7:0] a; logic [7:0] b; } inner_t;
    typedef struct packed { inner_t data; logic [15:0] extra; } outer_t;
endpackage
