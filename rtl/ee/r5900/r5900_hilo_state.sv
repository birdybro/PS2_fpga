// SPDX-License-Identifier: MIT

`default_nettype none

module r5900_hilo_state (
    input  logic                                      clk_i,
    input  logic                                      write_hi_valid_i,
    input  r5900_types_pkg::r5900_hilo_t             write_hi_value_i,
    input  logic                                      write_lo_valid_i,
    input  r5900_types_pkg::r5900_hilo_t             write_lo_value_i,
    input  logic                                      write_hi1_valid_i,
    input  r5900_types_pkg::r5900_hilo_t             write_hi1_value_i,
    input  logic                                      write_lo1_valid_i,
    input  r5900_types_pkg::r5900_hilo_t             write_lo1_value_i,
    output r5900_types_pkg::r5900_hilo_t             hi_o,
    output r5900_types_pkg::r5900_hilo_t             lo_o,
    output r5900_types_pkg::r5900_hilo_t             hi1_o,
    output r5900_types_pkg::r5900_hilo_t             lo1_o,
    output r5900_types_pkg::r5900_hilo_state_t       state_o
);

    timeunit 1ns;
    timeprecision 1ps;

    import r5900_types_pkg::*;

    r5900_hilo_state_t state_q;

    assign hi_o = state_q.hi;
    assign lo_o = state_q.lo;
    assign hi1_o = state_q.hi1;
    assign lo1_o = state_q.lo1;
    assign state_o = state_q;

    always_ff @(posedge clk_i) begin
        if (write_hi_valid_i) begin
            state_q.hi <= write_hi_value_i;
        end
        if (write_lo_valid_i) begin
            state_q.lo <= write_lo_value_i;
        end
        if (write_hi1_valid_i) begin
            state_q.hi1 <= write_hi1_value_i;
        end
        if (write_lo1_valid_i) begin
            state_q.lo1 <= write_lo1_value_i;
        end
    end

endmodule

`default_nettype wire
