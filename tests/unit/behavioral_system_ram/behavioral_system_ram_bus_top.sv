// SPDX-License-Identifier: MIT

`default_nettype none

module behavioral_system_ram_bus_top #(
    parameter int unsigned SIZE_BYTES = 256
) (
    input  logic         clk_i,
    input  logic         rst_ni,
    input  logic         backdoor_write_i,
    input  logic [31:0]  backdoor_addr_i,
    input  logic [7:0]   backdoor_wdata_i,
    output logic [7:0]   backdoor_rdata_o,
    output logic         backdoor_in_bounds_o,
    input  logic         req_valid_i,
    output logic         req_ready_o,
    input  logic         req_write_i,
    input  logic [31:0]  req_addr_i,
    input  logic [2:0]   req_size_i,
    input  logic [127:0] req_wdata_i,
    input  logic [15:0]  req_wstrb_i,
    output logic         rsp_valid_o,
    input  logic         rsp_ready_i,
    output logic [127:0] rsp_rdata_o,
    output logic         rsp_error_o
);

    timeunit 1ns;
    timeprecision 1ps;

    memory_bus_if #(
        .ADDR_WIDTH(32),
        .DATA_WIDTH(128)
    ) bus ();

    assign bus.req_valid = req_valid_i;
    assign req_ready_o = bus.req_ready;
    assign bus.req_write = req_write_i;
    assign bus.req_addr = req_addr_i;
    assign bus.req_size = req_size_i;
    assign bus.req_wdata = req_wdata_i;
    assign bus.req_wstrb = req_wstrb_i;
    assign rsp_valid_o = bus.rsp_valid;
    assign bus.rsp_ready = rsp_ready_i;
    assign rsp_rdata_o = bus.rsp_rdata;
    assign rsp_error_o = bus.rsp_error;

    behavioral_system_ram #(
        .ADDR_WIDTH(32),
        .DATA_WIDTH(128),
        .SIZE_BYTES(SIZE_BYTES)
    ) u_ram (
        .clk_i,
        .rst_ni,
        .backdoor_write_i,
        .backdoor_addr_i,
        .backdoor_wdata_i,
        .backdoor_rdata_o,
        .backdoor_in_bounds_o,
        .bus
    );

endmodule

`default_nettype wire
