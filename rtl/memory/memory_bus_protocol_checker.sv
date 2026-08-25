// SPDX-License-Identifier: MIT

`default_nettype none

module memory_bus_protocol_checker #(
    parameter int unsigned ADDR_WIDTH = 32,
    parameter int unsigned DATA_WIDTH = 128
) (
    input logic clk_i,
    input logic rst_ni,
    memory_bus_if.monitor bus,
    output logic outstanding_o
);

    timeunit 1ns;
    timeprecision 1ps;

    localparam int unsigned STROBE_WIDTH = DATA_WIDTH / 8;
    localparam int unsigned REQUEST_PAYLOAD_WIDTH =
        1 + ADDR_WIDTH + 3 + DATA_WIDTH + STROBE_WIDTH;
    localparam int unsigned RESPONSE_PAYLOAD_WIDTH = DATA_WIDTH + 1;

    logic                             outstanding_q;
    logic                             req_stalled_q;
    logic [REQUEST_PAYLOAD_WIDTH-1:0] req_payload_q;
    logic                             rsp_stalled_q;
    logic [RESPONSE_PAYLOAD_WIDTH-1:0] rsp_payload_q;

    logic req_fire;
    logic rsp_fire;

    assign req_fire = bus.req_valid && bus.req_ready;
    assign rsp_fire = bus.rsp_valid && bus.rsp_ready;
    assign outstanding_o = outstanding_q;

    always_ff @(posedge clk_i) begin
        if (!rst_ni) begin
            outstanding_q <= 1'b0;
            req_stalled_q <= 1'b0;
            req_payload_q <= '0;
            rsp_stalled_q <= 1'b0;
            rsp_payload_q <= '0;
        end else begin
            if (bus.req_valid) begin
                assert (bus.req_size <= 3'd4)
                else $fatal(1, "MEMBUS_SIZE: req_size must encode 1 through 16 bytes");
            end

            if (req_stalled_q) begin
                assert (bus.req_valid)
                else $fatal(1, "MEMBUS_REQ_VALID: stalled request valid was withdrawn");
                assert (
                    {bus.req_write, bus.req_addr, bus.req_size, bus.req_wdata, bus.req_wstrb}
                    == req_payload_q
                )
                else $fatal(1, "MEMBUS_REQ_STABLE: stalled request payload changed");
            end

            if (rsp_stalled_q) begin
                assert (bus.rsp_valid)
                else $fatal(1, "MEMBUS_RSP_VALID: stalled response valid was withdrawn");
                assert ({bus.rsp_rdata, bus.rsp_error} == rsp_payload_q)
                else $fatal(1, "MEMBUS_RSP_STABLE: stalled response payload changed");
            end

            assert (!bus.rsp_valid || outstanding_q || req_fire)
            else $fatal(1, "MEMBUS_RSP_CAUSAL: response has no accepted request");

            assert (!(req_fire && outstanding_q && !rsp_fire))
            else $fatal(1, "MEMBUS_OUTSTANDING: accepted a second outstanding request");

            req_stalled_q <= bus.req_valid && !bus.req_ready;
            req_payload_q <= {
                bus.req_write,
                bus.req_addr,
                bus.req_size,
                bus.req_wdata,
                bus.req_wstrb
            };
            rsp_stalled_q <= bus.rsp_valid && !bus.rsp_ready;
            rsp_payload_q <= {bus.rsp_rdata, bus.rsp_error};

            if (req_fire && !rsp_fire) begin
                outstanding_q <= 1'b1;
            end else if (!req_fire && rsp_fire) begin
                outstanding_q <= 1'b0;
            end
        end
    end

endmodule

`default_nettype wire
