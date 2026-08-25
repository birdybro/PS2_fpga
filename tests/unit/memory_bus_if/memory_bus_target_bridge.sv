// SPDX-License-Identifier: MIT

`default_nettype none

module memory_bus_target_bridge (
    output logic         req_valid_o,
    input  logic         req_ready_i,
    output logic         req_write_o,
    output logic [31:0]  req_addr_o,
    output logic [2:0]   req_size_o,
    output logic [127:0] req_wdata_o,
    output logic [15:0]  req_wstrb_o,
    input  logic         rsp_valid_i,
    output logic         rsp_ready_o,
    input  logic [127:0] rsp_rdata_i,
    input  logic         rsp_error_i,
    memory_bus_if.target bus
);

    assign req_valid_o = bus.req_valid;
    assign bus.req_ready = req_ready_i;
    assign req_write_o = bus.req_write;
    assign req_addr_o = bus.req_addr;
    assign req_size_o = bus.req_size;
    assign req_wdata_o = bus.req_wdata;
    assign req_wstrb_o = bus.req_wstrb;
    assign bus.rsp_valid = rsp_valid_i;
    assign rsp_ready_o = bus.rsp_ready;
    assign bus.rsp_rdata = rsp_rdata_i;
    assign bus.rsp_error = rsp_error_i;

endmodule

`default_nettype wire
