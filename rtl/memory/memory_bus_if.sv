// SPDX-License-Identifier: MIT

`default_nettype none

interface memory_bus_if #(
    parameter int unsigned ADDR_WIDTH = 32,
    parameter int unsigned DATA_WIDTH = 128
);

    localparam int unsigned STROBE_WIDTH = DATA_WIDTH / 8;

    logic                    req_valid;
    logic                    req_ready;
    logic                    req_write;
    logic [ADDR_WIDTH-1:0]   req_addr;
    logic [2:0]              req_size;
    logic [DATA_WIDTH-1:0]   req_wdata;
    logic [STROBE_WIDTH-1:0] req_wstrb;

    logic                  rsp_valid;
    logic                  rsp_ready;
    logic [DATA_WIDTH-1:0] rsp_rdata;
    logic                  rsp_error;

    modport initiator (
        output req_valid,
        input  req_ready,
        output req_write,
        output req_addr,
        output req_size,
        output req_wdata,
        output req_wstrb,
        input  rsp_valid,
        output rsp_ready,
        input  rsp_rdata,
        input  rsp_error
    );

    modport target (
        input  req_valid,
        output req_ready,
        input  req_write,
        input  req_addr,
        input  req_size,
        input  req_wdata,
        input  req_wstrb,
        output rsp_valid,
        input  rsp_ready,
        output rsp_rdata,
        output rsp_error
    );

    modport request_initiator (
        output req_valid,
        input  req_ready,
        output req_write,
        output req_addr,
        output req_size,
        output req_wdata,
        output req_wstrb
    );

    modport response_consumer (
        input  rsp_valid,
        output rsp_ready,
        input  rsp_rdata,
        input  rsp_error
    );

    modport monitor (
        input req_valid,
        input req_ready,
        input req_write,
        input req_addr,
        input req_size,
        input req_wdata,
        input req_wstrb,
        input rsp_valid,
        input rsp_ready,
        input rsp_rdata,
        input rsp_error
    );

endinterface

`default_nettype wire
