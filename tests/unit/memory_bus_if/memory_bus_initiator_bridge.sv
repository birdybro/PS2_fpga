// SPDX-License-Identifier: MIT

`default_nettype none

module memory_bus_initiator_bridge (
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
    output logic         rsp_error_o,
    memory_bus_if.initiator bus
);

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

endmodule

`default_nettype wire
