// SPDX-License-Identifier: MIT

`default_nettype none

module r5900_control (
    input  logic                                      clk_i,
    input  logic                                      rst_ni,
    input  logic                                      fetch_request_done_i,
    input  logic                                      fetch_response_done_i,
    input  logic                                      decode_done_i,
    input  logic                                      execute_done_i,
    input  logic                                      writeback_done_i,
    output r5900_types_pkg::r5900_control_state_t    state_o
);

    timeunit 1ns;
    timeprecision 1ps;

    import r5900_types_pkg::*;

    r5900_control_state_t state_q;
    r5900_control_state_t state_d;

    assign state_o = state_q;

    always_comb begin
        state_d = state_q;
        case (state_q)
            R5900_FETCH_REQUEST: begin
                if (fetch_request_done_i) begin
                    state_d = R5900_FETCH_RESPONSE;
                end
            end
            R5900_FETCH_RESPONSE: begin
                if (fetch_response_done_i) begin
                    state_d = R5900_DECODE;
                end
            end
            R5900_DECODE: begin
                if (decode_done_i) begin
                    state_d = R5900_EXECUTE;
                end
            end
            R5900_EXECUTE: begin
                if (execute_done_i) begin
                    state_d = R5900_WRITEBACK;
                end
            end
            R5900_WRITEBACK: begin
                if (writeback_done_i) begin
                    state_d = R5900_FETCH_REQUEST;
                end
            end
            default: begin
                state_d = R5900_FETCH_REQUEST;
            end
        endcase
    end

    always_ff @(posedge clk_i) begin
        if (!rst_ni) begin
            state_q <= R5900_FETCH_REQUEST;
        end else begin
            state_q <= state_d;
        end
    end

    r5900_control_state_checker u_state_checker (
        .clk_i,
        .rst_ni,
        .state_i(state_q)
    );

endmodule

`default_nettype wire
