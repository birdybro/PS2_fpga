// SPDX-License-Identifier: MIT

`default_nettype none

module memory_bus_if_smoke_top (
    input  logic         initiator_req_valid_i,
    output logic         initiator_req_ready_o,
    input  logic         initiator_req_write_i,
    input  logic [31:0]  initiator_req_addr_i,
    input  logic [2:0]   initiator_req_size_i,
    input  logic [127:0] initiator_req_wdata_i,
    input  logic [15:0]  initiator_req_wstrb_i,
    output logic         initiator_rsp_valid_o,
    input  logic         initiator_rsp_ready_i,
    output logic [127:0] initiator_rsp_rdata_o,
    output logic         initiator_rsp_error_o,
    output logic         target_req_valid_o,
    input  logic         target_req_ready_i,
    output logic         target_req_write_o,
    output logic [31:0]  target_req_addr_o,
    output logic [2:0]   target_req_size_o,
    output logic [127:0] target_req_wdata_o,
    output logic [15:0]  target_req_wstrb_o,
    input  logic         target_rsp_valid_i,
    output logic         target_rsp_ready_o,
    input  logic [127:0] target_rsp_rdata_i,
    input  logic         target_rsp_error_i
);

    memory_bus_if #(
        .ADDR_WIDTH(32),
        .DATA_WIDTH(128)
    ) bus ();

    memory_bus_initiator_bridge u_initiator (
        .req_valid_i(initiator_req_valid_i),
        .req_ready_o(initiator_req_ready_o),
        .req_write_i(initiator_req_write_i),
        .req_addr_i(initiator_req_addr_i),
        .req_size_i(initiator_req_size_i),
        .req_wdata_i(initiator_req_wdata_i),
        .req_wstrb_i(initiator_req_wstrb_i),
        .rsp_valid_o(initiator_rsp_valid_o),
        .rsp_ready_i(initiator_rsp_ready_i),
        .rsp_rdata_o(initiator_rsp_rdata_o),
        .rsp_error_o(initiator_rsp_error_o),
        .bus
    );

    memory_bus_target_bridge u_target (
        .req_valid_o(target_req_valid_o),
        .req_ready_i(target_req_ready_i),
        .req_write_o(target_req_write_o),
        .req_addr_o(target_req_addr_o),
        .req_size_o(target_req_size_o),
        .req_wdata_o(target_req_wdata_o),
        .req_wstrb_o(target_req_wstrb_o),
        .rsp_valid_i(target_rsp_valid_i),
        .rsp_ready_o(target_rsp_ready_o),
        .rsp_rdata_i(target_rsp_rdata_i),
        .rsp_error_i(target_rsp_error_i),
        .bus
    );

endmodule

`default_nettype wire
