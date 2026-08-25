// SPDX-License-Identifier: MIT

`default_nettype none

module r5900_pc (
    input  logic                              clk_i,
    input  logic                              rst_ni,
    input  r5900_types_pkg::r5900_pc_t       start_pc_i,
    input  logic                              advance_i,
    input  logic                              redirect_valid_i,
    input  r5900_types_pkg::r5900_pc_t       redirect_pc_i,
    output r5900_types_pkg::r5900_pc_t       pc_o
);

    timeunit 1ns;
    timeprecision 1ps;

    import r5900_types_pkg::*;

    r5900_pc_t pc_q;

    assign pc_o = pc_q;

    always_ff @(posedge clk_i) begin
        if (!rst_ni) begin
            pc_q <= start_pc_i;
        end else if (redirect_valid_i) begin
            pc_q <= redirect_pc_i;
        end else if (advance_i) begin
            pc_q <= pc_q + 32'd4;
        end
    end

endmodule

`default_nettype wire
