// SPDX-License-Identifier: MIT

`default_nettype none

module architectural_trace_sink_top #(
    parameter bit TRACE_ENABLE = 1'b0
) (
    input logic         clk_i,
    input logic         rst_ni,
    input logic         event_valid_i,
    input logic [7:0]   event_source_i,
    input logic [7:0]   event_kind_i,
    input logic [31:0]  event_pc_i,
    input logic [31:0]  event_instruction_i,
    input logic [15:0]  event_identifier_i,
    input logic [127:0] event_value_i
);

    timeunit 1ns;
    timeprecision 1ps;

    architectural_trace_sink #(
        .TRACE_ENABLE(TRACE_ENABLE)
    ) u_trace (
        .clk_i,
        .rst_ni,
        .event_valid_i,
        .event_source_i,
        .event_kind_i,
        .event_pc_i,
        .event_instruction_i,
        .event_identifier_i,
        .event_value_i
    );

endmodule

`default_nettype wire
