// SPDX-License-Identifier: MIT

`default_nettype none

module r5900_fetch_request (
    input logic                                  clk_i,
    input logic                                  rst_ni,
    input logic                                  start_i,
    input r5900_types_pkg::r5900_pc_t           pc_i,
    memory_bus_if.request_initiator              bus,
    output logic                                 accepted_o
);

    timeunit 1ns;
    timeprecision 1ps;

    import r5900_types_pkg::*;

    r5900_pc_t address_q;
    logic      pending_q;

    assign bus.req_valid = pending_q;
    assign bus.req_write = 1'b0;
    assign bus.req_addr = address_q;
    assign bus.req_size = 3'd2;
    assign bus.req_wdata = 128'd0;
    assign bus.req_wstrb = 16'd0;
    assign accepted_o = bus.req_valid && bus.req_ready;

    always_ff @(posedge clk_i) begin
        if (!rst_ni) begin
            address_q <= 32'd0;
            pending_q <= 1'b0;
        end else begin
            if (accepted_o) begin
                pending_q <= 1'b0;
            end
            if (start_i) begin
                address_q <= pc_i;
                pending_q <= 1'b1;
            end
        end
    end

    property p_fetch_start_is_aligned;
        @(posedge clk_i) disable iff (!rst_ni) start_i |-> (pc_i[1:0] == 2'b00);
    endproperty

    property p_fetch_does_not_replace_stalled_request;
        @(posedge clk_i) disable iff (!rst_ni)
            start_i |-> (!pending_q || bus.req_ready);
    endproperty

    assert property (p_fetch_start_is_aligned)
        else $fatal(1, "R5900_FETCH_ALIGN: unaligned instruction fetch");

    assert property (p_fetch_does_not_replace_stalled_request)
        else $fatal(1, "R5900_FETCH_RESTART: request replaced while stalled");

endmodule

`default_nettype wire
