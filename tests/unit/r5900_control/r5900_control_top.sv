// SPDX-License-Identifier: MIT

`default_nettype none

module r5900_control_top (
    input  logic       clk_i,
    input  logic       rst_ni,
    input  logic       fetch_request_done_i,
    input  logic       fetch_response_done_i,
    input  logic       decode_done_i,
    input  logic       execute_done_i,
    input  logic       writeback_done_i,
    input  logic       inject_illegal_i,
    output logic [2:0] state_o
);

    timeunit 1ns;
    timeprecision 1ps;

    import r5900_types_pkg::*;

    r5900_control_state_t typed_state;
    r5900_control_state_t injected_state;

    assign state_o = typed_state;
    assign injected_state = inject_illegal_i ? r5900_control_state_t'(3'b111) : typed_state;

    r5900_control u_control (
        .clk_i,
        .rst_ni,
        .fetch_request_done_i,
        .fetch_response_done_i,
        .decode_done_i,
        .execute_done_i,
        .writeback_done_i,
        .state_o(typed_state)
    );

    r5900_control_state_checker u_injection_checker (
        .clk_i,
        .rst_ni,
        .state_i(injected_state)
    );

    initial begin
        if ($bits(r5900_control_state_t) != 3) begin
            $fatal(1, "R5900_CONTROL_TYPE_WIDTH");
        end
    end

endmodule

`default_nettype wire
