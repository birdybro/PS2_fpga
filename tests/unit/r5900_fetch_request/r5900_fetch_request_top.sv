// SPDX-License-Identifier: MIT

`default_nettype none

module r5900_fetch_request_top (
    input  logic         clk_i,
    input  logic         rst_ni,
    input  logic         start_i,
    input  logic [31:0]  pc_i,
    input  logic         req_ready_i,
    output logic         req_valid_o,
    output logic         req_write_o,
    output logic [31:0]  req_addr_o,
    output logic [2:0]   req_size_o,
    output logic [127:0] req_wdata_o,
    output logic [15:0]  req_wstrb_o,
    output logic         rsp_valid_o,
    output logic         rsp_ready_o,
    output logic [127:0] rsp_rdata_o,
    output logic         rsp_error_o,
    output logic         accepted_o
);

    timeunit 1ns;
    timeprecision 1ps;

    memory_bus_if #(
        .ADDR_WIDTH(32),
        .DATA_WIDTH(128)
    ) bus ();

    assign bus.req_ready = req_ready_i;
    assign bus.rsp_valid = 1'b0;
    assign bus.rsp_rdata = 128'd0;
    assign bus.rsp_error = 1'b0;
    assign bus.rsp_ready = 1'b0;

    assign req_valid_o = bus.req_valid;
    assign req_write_o = bus.req_write;
    assign req_addr_o = bus.req_addr;
    assign req_size_o = bus.req_size;
    assign req_wdata_o = bus.req_wdata;
    assign req_wstrb_o = bus.req_wstrb;
    assign rsp_valid_o = bus.rsp_valid;
    assign rsp_ready_o = bus.rsp_ready;
    assign rsp_rdata_o = bus.rsp_rdata;
    assign rsp_error_o = bus.rsp_error;

    r5900_fetch_request u_fetch_request (
        .clk_i,
        .rst_ni,
        .start_i,
        .pc_i,
        .bus,
        .accepted_o
    );

endmodule

`default_nettype wire
