// SPDX-License-Identifier: MIT

`default_nettype none

module ps2_sim_top #(
    parameter time CLOCK_PERIOD = 10ns,
    parameter int unsigned RESET_CYCLES = 4,
    parameter int unsigned RAM_SIZE_BYTES = 1024,
    parameter int unsigned RAM_RESPONSE_LATENCY_CYCLES = 0,
    parameter int unsigned MAX_CYCLES = 0,
    parameter bit FATAL_ON_TIMEOUT = 1'b1,
    parameter bit FINISH_ON_PASS = 1'b1,
    parameter bit FATAL_ON_FAIL = 1'b1,
    parameter bit MEMORY_TRACE_ENABLE = 1'b0,
    parameter bit ARCH_TRACE_ENABLE = 1'b0,
    parameter bit WAVE_ENABLE = 1'b0
) (
    output logic         clk_o,
    output logic         rst_no,
    input  logic         mem_req_valid_i,
    output logic         mem_req_ready_o,
    input  logic         mem_req_write_i,
    input  logic [31:0]  mem_req_addr_i,
    input  logic [2:0]   mem_req_size_i,
    input  logic [127:0] mem_req_wdata_i,
    input  logic [15:0]  mem_req_wstrb_i,
    output logic         mem_rsp_valid_o,
    input  logic         mem_rsp_ready_i,
    output logic [127:0] mem_rsp_rdata_o,
    output logic         mem_rsp_error_o,
    input  logic         ram_backdoor_write_i,
    input  logic [31:0]  ram_backdoor_addr_i,
    input  logic [7:0]   ram_backdoor_wdata_i,
    output logic [7:0]   ram_backdoor_rdata_o,
    output logic         ram_backdoor_in_bounds_o,
    input  logic         pass_i,
    input  logic         fail_i,
    input  logic [31:0]  fail_code_i,
    output logic         pass_event_o,
    output logic         pass_latched_o,
    output logic         fail_event_o,
    output logic         fail_latched_o,
    output logic [31:0]  fail_code_o,
    output logic         timeout_o,
    output logic [31:0]  cycle_count_o,
    output logic         mem_outstanding_o,
    input  logic         arch_event_valid_i,
    input  logic [7:0]   arch_event_source_i,
    input  logic [7:0]   arch_event_kind_i,
    input  logic [31:0]  arch_event_pc_i,
    input  logic [31:0]  arch_event_instruction_i,
    input  logic [15:0]  arch_event_identifier_i,
    input  logic [127:0] arch_event_value_i
);

    timeunit 1ns;
    timeprecision 1ps;

    memory_bus_if #(
        .ADDR_WIDTH(32),
        .DATA_WIDTH(128)
    ) memory_bus ();

    assign memory_bus.req_valid = mem_req_valid_i;
    assign mem_req_ready_o = memory_bus.req_ready;
    assign memory_bus.req_write = mem_req_write_i;
    assign memory_bus.req_addr = mem_req_addr_i;
    assign memory_bus.req_size = mem_req_size_i;
    assign memory_bus.req_wdata = mem_req_wdata_i;
    assign memory_bus.req_wstrb = mem_req_wstrb_i;
    assign mem_rsp_valid_o = memory_bus.rsp_valid;
    assign memory_bus.rsp_ready = mem_rsp_ready_i;
    assign mem_rsp_rdata_o = memory_bus.rsp_rdata;
    assign mem_rsp_error_o = memory_bus.rsp_error;

    sim_clock #(
        .PERIOD(CLOCK_PERIOD)
    ) u_clock (
        .clk_o
    );

    sim_reset #(
        .ASSERT_CYCLES(RESET_CYCLES)
    ) u_reset (
        .clk_i(clk_o),
        .rst_ni(rst_no)
    );

    behavioral_system_ram #(
        .ADDR_WIDTH(32),
        .DATA_WIDTH(128),
        .SIZE_BYTES(RAM_SIZE_BYTES),
        .RESPONSE_LATENCY_CYCLES(RAM_RESPONSE_LATENCY_CYCLES)
    ) u_ram (
        .clk_i(clk_o),
        .rst_ni(rst_no),
        .backdoor_write_i(ram_backdoor_write_i),
        .backdoor_addr_i(ram_backdoor_addr_i),
        .backdoor_wdata_i(ram_backdoor_wdata_i),
        .backdoor_rdata_o(ram_backdoor_rdata_o),
        .backdoor_in_bounds_o(ram_backdoor_in_bounds_o),
        .bus(memory_bus)
    );

    memory_bus_protocol_checker #(
        .ADDR_WIDTH(32),
        .DATA_WIDTH(128)
    ) u_memory_protocol_checker (
        .clk_i(clk_o),
        .rst_ni(rst_no),
        .bus(memory_bus),
        .outstanding_o(mem_outstanding_o)
    );

    sim_cycle_timeout #(
        .MAX_CYCLES(MAX_CYCLES),
        .FATAL_ON_TIMEOUT(FATAL_ON_TIMEOUT)
    ) u_timeout (
        .clk_i(clk_o),
        .rst_ni(rst_no),
        .timeout_o,
        .cycle_count_o
    );

    sim_termination #(
        .FINISH_ON_PASS(FINISH_ON_PASS),
        .FATAL_ON_FAIL(FATAL_ON_FAIL)
    ) u_termination (
        .clk_i(clk_o),
        .rst_ni(rst_no),
        .pass_i,
        .fail_i,
        .fail_code_i,
        .pass_event_o,
        .pass_latched_o,
        .fail_event_o,
        .fail_latched_o,
        .fail_code_o
    );

    memory_transaction_trace #(
        .TRACE_ENABLE(MEMORY_TRACE_ENABLE)
    ) u_memory_trace (
        .clk_i(clk_o),
        .rst_ni(rst_no),
        .bus(memory_bus)
    );

    architectural_trace_sink #(
        .TRACE_ENABLE(ARCH_TRACE_ENABLE)
    ) u_architectural_trace (
        .clk_i(clk_o),
        .rst_ni(rst_no),
        .event_valid_i(arch_event_valid_i),
        .event_source_i(arch_event_source_i),
        .event_kind_i(arch_event_kind_i),
        .event_pc_i(arch_event_pc_i),
        .event_instruction_i(arch_event_instruction_i),
        .event_identifier_i(arch_event_identifier_i),
        .event_value_i(arch_event_value_i)
    );

    sim_waveform_control #(
        .WAVE_ENABLE(WAVE_ENABLE)
    ) u_waveform_control ();

endmodule

`default_nettype wire
