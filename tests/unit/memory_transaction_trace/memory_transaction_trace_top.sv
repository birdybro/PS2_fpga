// SPDX-License-Identifier: MIT

`default_nettype none

module memory_transaction_trace_top #(
    parameter bit TRACE_ENABLE = 1'b0
) (
    input logic         clk_i,
    input logic         rst_ni,
    input logic         req_valid_i,
    input logic         req_ready_i,
    input logic         req_write_i,
    input logic [31:0]  req_addr_i,
    input logic [2:0]   req_size_i,
    input logic [127:0] req_wdata_i,
    input logic [15:0]  req_wstrb_i,
    input logic         rsp_valid_i,
    input logic         rsp_ready_i,
    input logic [127:0] rsp_rdata_i,
    input logic         rsp_error_i
);

    timeunit 1ns;
    timeprecision 1ps;

    memory_bus_if #(
        .ADDR_WIDTH(32),
        .DATA_WIDTH(128)
    ) bus ();

    assign bus.req_valid = req_valid_i;
    assign bus.req_ready = req_ready_i;
    assign bus.req_write = req_write_i;
    assign bus.req_addr = req_addr_i;
    assign bus.req_size = req_size_i;
    assign bus.req_wdata = req_wdata_i;
    assign bus.req_wstrb = req_wstrb_i;
    assign bus.rsp_valid = rsp_valid_i;
    assign bus.rsp_ready = rsp_ready_i;
    assign bus.rsp_rdata = rsp_rdata_i;
    assign bus.rsp_error = rsp_error_i;

    memory_transaction_trace #(
        .TRACE_ENABLE(TRACE_ENABLE)
    ) u_trace (
        .clk_i,
        .rst_ni,
        .bus
    );

endmodule

`default_nettype wire
