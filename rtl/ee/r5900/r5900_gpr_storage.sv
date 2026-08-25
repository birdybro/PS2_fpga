// SPDX-License-Identifier: MIT

`default_nettype none

module r5900_gpr_storage (
    input  logic                                  clk_i,
    input  r5900_types_pkg::r5900_gpr_index_t    read_index_a_i,
    output r5900_types_pkg::r5900_gpr_t          read_value_a_o,
    input  r5900_types_pkg::r5900_gpr_index_t    read_index_b_i,
    output r5900_types_pkg::r5900_gpr_t          read_value_b_o,
    input  logic                                  write_valid_i,
    input  r5900_types_pkg::r5900_gpr_index_t    write_index_i,
    input  r5900_types_pkg::r5900_gpr_t          write_value_i,
    output r5900_types_pkg::r5900_gpr_file_t     state_o
);

    timeunit 1ns;
    timeprecision 1ps;

    import r5900_types_pkg::*;

    r5900_gpr_file_t gprs_q;

    assign read_value_a_o = gprs_q[read_index_a_i];
    assign read_value_b_o = gprs_q[read_index_b_i];
    assign state_o = gprs_q;

    always_ff @(posedge clk_i) begin
        if (write_valid_i) begin
            gprs_q[write_index_i] <= write_value_i;
        end
    end

endmodule

`default_nettype wire
