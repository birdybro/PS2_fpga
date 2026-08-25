// SPDX-License-Identifier: MIT

`default_nettype none

module r5900_fetch_response_top (
    input  logic         clk_i,
    input  logic         rst_ni,
    input  logic         request_accepted_i,
    input  logic         instruction_ready_i,
    input  logic         rsp_valid_i,
    input  logic [127:0] rsp_rdata_i,
    input  logic         rsp_error_i,
    output logic         rsp_ready_o,
    output logic         response_accepted_o,
    output logic         response_expected_o,
    output logic         instruction_valid_o,
    output logic [31:0]  instruction_o,
    output logic         fetch_error_o,
    output logic         req_valid_o,
    output logic         req_ready_o,
    output logic         req_write_o,
    output logic [31:0]  req_addr_o,
    output logic [2:0]   req_size_o,
    output logic [127:0] req_wdata_o,
    output logic [15:0]  req_wstrb_o
);

    timeunit 1ns;
    timeprecision 1ps;

    memory_bus_if #(
        .ADDR_WIDTH(32),
        .DATA_WIDTH(128)
    ) bus ();

    assign bus.req_valid = 1'b0;
    assign bus.req_ready = 1'b0;
    assign bus.req_write = 1'b0;
    assign bus.req_addr = 32'd0;
    assign bus.req_size = 3'd0;
    assign bus.req_wdata = 128'd0;
    assign bus.req_wstrb = 16'd0;
    assign bus.rsp_valid = rsp_valid_i;
    assign bus.rsp_rdata = rsp_rdata_i;
    assign bus.rsp_error = rsp_error_i;

    assign rsp_ready_o = bus.rsp_ready;
    assign req_valid_o = bus.req_valid;
    assign req_ready_o = bus.req_ready;
    assign req_write_o = bus.req_write;
    assign req_addr_o = bus.req_addr;
    assign req_size_o = bus.req_size;
    assign req_wdata_o = bus.req_wdata;
    assign req_wstrb_o = bus.req_wstrb;

    r5900_fetch_response u_fetch_response (
        .clk_i,
        .rst_ni,
        .request_accepted_i,
        .instruction_ready_i,
        .bus,
        .response_accepted_o,
        .response_expected_o,
        .instruction_valid_o,
        .instruction_o,
        .fetch_error_o
    );

endmodule

`default_nettype wire
