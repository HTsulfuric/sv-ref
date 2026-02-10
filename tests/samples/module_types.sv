module merge_phase_t1;
    typedef enum logic [1:0] { IDLE=0, QUERY=1, MERGE=2, DONE=3 } merge_state_t;
    typedef struct packed {
        logic [7:0]   addr;
        logic [15:0]  data;
        merge_state_t state;
    } merge_query_data_t;
endmodule
