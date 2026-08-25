// SPDX-License-Identifier: MIT

`default_nettype none

module r5900_writeback_top (
    input  logic          clk_i,
    input  logic          rst_ni,
    input  logic          commit_i,
    input  logic [4:0]    destination_i,
    input  logic [127:0]  value_i,
    input  logic [4:0]    read_index_a_i,
    input  logic [4:0]    read_index_b_i,
    output logic          commit_accepted_o,
    output logic          gpr_write_enable_o,
    output logic [4:0]    gpr_write_index_o,
    output logic [127:0]  gpr_write_data_o,
    output logic          writeback_valid_o,
    output logic [4:0]    writeback_destination_o,
    output logic [127:0]  writeback_value_o,
    output logic [127:0]  read_data_a_o,
    output logic [127:0]  read_data_b_o,
    output logic [4095:0] gprs_o
);

    timeunit 1ns;
    timeprecision 1ps;

    import r5900_types_pkg::*;

    r5900_writeback_t writeback;

    assign writeback_valid_o = writeback.valid;
    assign writeback_destination_o = writeback.destination;
    assign writeback_value_o = writeback.value;

    r5900_writeback u_writeback (
        .clk_i,
        .rst_ni,
        .commit_i,
        .destination_i,
        .value_i,
        .commit_accepted_o,
        .gpr_write_enable_o,
        .gpr_write_index_o,
        .gpr_write_data_o,
        .writeback_o(writeback)
    );

    r5900_gpr_file u_gpr_file (
        .clk_i,
        .write_valid_i(gpr_write_enable_o),
        .write_index_i(gpr_write_index_o),
        .write_value_i(gpr_write_data_o),
        .read_index_a_i,
        .read_index_b_i,
        .read_value_a_o(read_data_a_o),
        .read_value_b_o(read_data_b_o),
        .state_o(gprs_o)
    );

endmodule

`default_nettype wire
