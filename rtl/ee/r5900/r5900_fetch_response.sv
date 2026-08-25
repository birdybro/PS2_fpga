// SPDX-License-Identifier: MIT

`default_nettype none

module r5900_fetch_response (
    input logic                                     clk_i,
    input logic                                     rst_ni,
    input logic                                     request_accepted_i,
    input logic                                     instruction_ready_i,
    memory_bus_if.response_consumer                 bus,
    output logic                                    response_accepted_o,
    output logic                                    response_expected_o,
    output logic                                    instruction_valid_o,
    output r5900_types_pkg::r5900_instruction_t     instruction_o,
    output logic                                    fetch_error_o
);

    timeunit 1ns;
    timeprecision 1ps;

    import r5900_types_pkg::*;

    logic               response_expected_q;
    logic               instruction_valid_q;
    r5900_instruction_t instruction_q;
    logic               fetch_error_q;
    logic               instruction_slot_available;

    assign instruction_slot_available = !instruction_valid_q || instruction_ready_i;
    assign bus.rsp_ready = rst_ni
        && (response_expected_q || request_accepted_i)
        && instruction_slot_available;
    assign response_accepted_o = bus.rsp_valid && bus.rsp_ready;
    assign response_expected_o = response_expected_q;
    assign instruction_valid_o = instruction_valid_q;
    assign instruction_o = instruction_q;
    assign fetch_error_o = fetch_error_q;

    always_ff @(posedge clk_i) begin
        if (!rst_ni) begin
            response_expected_q <= 1'b0;
            instruction_valid_q <= 1'b0;
            instruction_q <= 32'd0;
            fetch_error_q <= 1'b0;
        end else begin
            if (instruction_valid_q && instruction_ready_i) begin
                instruction_valid_q <= 1'b0;
            end

            if (request_accepted_i) begin
                response_expected_q <= 1'b1;
            end

            if (response_accepted_o) begin
                assert (!$isunknown({bus.rsp_rdata, bus.rsp_error}))
                else $fatal(1, "R5900_FETCH_RESPONSE_UNKNOWN: response payload is unknown");
                response_expected_q <= 1'b0;
                instruction_valid_q <= 1'b1;
                instruction_q <= bus.rsp_rdata[31:0];
                fetch_error_q <= bus.rsp_error;
            end
        end
    end

    property p_request_does_not_overlap_fetch;
        @(posedge clk_i) disable iff (!rst_ni)
            request_accepted_i |-> (
                !response_expected_q
                && (!instruction_valid_q || instruction_ready_i)
            );
    endproperty

    property p_response_has_fetch_request;
        @(posedge clk_i) disable iff (!rst_ni)
            bus.rsp_valid |-> (response_expected_q || request_accepted_i);
    endproperty

    assert property (p_request_does_not_overlap_fetch)
        else $fatal(1, "R5900_FETCH_RESPONSE_OVERLAP: fetch response state is occupied");

    assert property (p_response_has_fetch_request)
        else $fatal(1, "R5900_FETCH_RESPONSE_UNEXPECTED: response has no fetch request");

endmodule

`default_nettype wire
