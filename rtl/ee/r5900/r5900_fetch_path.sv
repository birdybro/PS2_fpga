// SPDX-License-Identifier: MIT

`default_nettype none

module r5900_fetch_path (
    input logic                                     clk_i,
    input logic                                     rst_ni,
    input logic                                     start_i,
    input r5900_types_pkg::r5900_pc_t              pc_i,
    input logic                                     instruction_ready_i,
    memory_bus_if                                   bus,
    output logic                                    start_ready_o,
    output logic                                    request_accepted_o,
    output logic                                    response_accepted_o,
    output logic                                    response_expected_o,
    output logic                                    instruction_valid_o,
    output r5900_types_pkg::r5900_instruction_t    instruction_o,
    output logic                                    fetch_error_o
);

    timeunit 1ns;
    timeprecision 1ps;

    logic request_accepted_q;

    assign start_ready_o = rst_ni
        && !bus.req_valid
        && !request_accepted_q
        && !response_expected_o
        && (!instruction_valid_o || instruction_ready_i);

    always_ff @(posedge clk_i) begin
        if (!rst_ni) begin
            request_accepted_q <= 1'b0;
        end else begin
            request_accepted_q <= request_accepted_o;
        end
    end

    r5900_fetch_request u_request (
        .clk_i,
        .rst_ni,
        .start_i,
        .pc_i,
        .bus(bus),
        .accepted_o(request_accepted_o)
    );

    r5900_fetch_response u_response (
        .clk_i,
        .rst_ni,
        .request_accepted_i(request_accepted_q),
        .instruction_ready_i,
        .bus(bus),
        .response_accepted_o,
        .response_expected_o,
        .instruction_valid_o,
        .instruction_o,
        .fetch_error_o
    );

    property p_fetch_starts_only_when_ready;
        @(posedge clk_i) disable iff (!rst_ni) start_i |-> start_ready_o;
    endproperty

    assert property (p_fetch_starts_only_when_ready)
        else $fatal(1, "R5900_FETCH_BUSY: fetch started while the path was occupied");

endmodule

`default_nettype wire
