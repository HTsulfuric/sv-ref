// Edge case test fixtures for snapshot testing

// Package A: parameterized struct + non-sequential enum
package edge_pkg_a;
    parameter WIDTH = 8;

    typedef enum logic [3:0] {
        ALPHA = 0,
        BETA  = 3,
        GAMMA = 7,
        DELTA = 15
    } sparse_e;

    typedef struct packed {
        logic [WIDTH-1:0] data;
        logic [3:0]       tag;
    } param_t;
endpackage

// Package B: large struct with many fields
package edge_pkg_b;
    typedef struct packed {
        logic [7:0] field_0;
        logic [7:0] field_1;
        logic [7:0] field_2;
        logic [7:0] field_3;
        logic [7:0] field_4;
        logic [7:0] field_5;
        logic [7:0] field_6;
        logic [7:0] field_7;
    } wide_t;
endpackage
