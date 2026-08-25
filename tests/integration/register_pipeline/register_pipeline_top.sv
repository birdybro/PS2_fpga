// SPDX-License-Identifier: MIT

module register_pipeline_top (
    input  logic        clk_i,
    input  logic        rst_ni,
    input  logic        en_i,
    input  logic [31:0] d_i,
    output logic [31:0] q_o
);

    timeunit 1ns;
    timeprecision 1ps;

    logic [31:0] stage_one;

    register_en #(
        .WIDTH(32)
    ) u_stage_one (
        .clk_i,
        .rst_ni,
        .en_i,
        .d_i,
        .q_o(stage_one)
    );

    register_en #(
        .WIDTH(32)
    ) u_stage_two (
        .clk_i,
        .rst_ni,
        .en_i(1'b1),
        .d_i(stage_one),
        .q_o
    );

endmodule
