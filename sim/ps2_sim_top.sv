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
    parameter bit WAVE_ENABLE = 1'b0,
    parameter bit R5900_FETCH_ENABLE = 1'b0,
    parameter bit R5900_CORE_ENABLE = 1'b0
) (
    output logic         clk_o,
    output logic         rst_no,
    /* verilator lint_off UNUSEDSIGNAL */
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
    input  logic         ee_run_i,
    input  logic [31:0]  ee_start_pc_i,
    input  logic         ee_fetch_start_i,
    input  logic [31:0]  ee_fetch_pc_i,
    input  logic         ee_instruction_ready_i,
    /* verilator lint_on UNUSEDSIGNAL */
    output logic         ee_fetch_start_ready_o,
    output logic         ee_fetch_request_accepted_o,
    output logic         ee_fetch_response_accepted_o,
    output logic         ee_fetch_response_expected_o,
    output logic         ee_instruction_valid_o,
    output logic [31:0]  ee_instruction_o,
    output logic         ee_fetch_error_o,
    output logic [2:0]   ee_control_state_o,
    output logic [31:0]  ee_pc_o,
    output logic         ee_retirement_valid_o,
    output logic [31:0]  ee_retirement_pc_o,
    output logic [31:0]  ee_retirement_instruction_o,
    output logic         ee_reserved_valid_o,
    output logic [31:0]  ee_reserved_pc_o,
    output logic [31:0]  ee_reserved_instruction_o,
    output logic         ee_writeback_valid_o,
    output logic [4:0]   ee_writeback_destination_o,
    output logic [127:0] ee_writeback_value_o,
    output logic [4095:0] ee_gprs_o,
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

    initial begin
        if (R5900_FETCH_ENABLE && R5900_CORE_ENABLE) begin
            $fatal(1, "ps2_sim_top fetch-only and core modes are mutually exclusive");
        end
    end

    memory_bus_if #(
        .ADDR_WIDTH(32),
        .DATA_WIDTH(128)
    ) memory_bus ();

    assign mem_req_ready_o = memory_bus.req_ready;
    assign mem_rsp_valid_o = memory_bus.rsp_valid;
    assign mem_rsp_rdata_o = memory_bus.rsp_rdata;
    assign mem_rsp_error_o = memory_bus.rsp_error;

    generate
        if (R5900_CORE_ENABLE) begin : g_r5900_core
            r5900_types_pkg::r5900_retirement_t           core_retirement;
            r5900_types_pkg::r5900_reserved_instruction_t core_reserved_instruction;
            r5900_types_pkg::r5900_writeback_t            core_writeback;

            r5900_core u_core (
                .clk_i(clk_o),
                .rst_ni(rst_no),
                .run_i(ee_run_i),
                .start_pc_i(ee_start_pc_i),
                .bus(memory_bus),
                .state_o(ee_control_state_o),
                .pc_o(ee_pc_o),
                .fetch_start_ready_o(ee_fetch_start_ready_o),
                .fetch_request_accepted_o(ee_fetch_request_accepted_o),
                .fetch_response_accepted_o(ee_fetch_response_accepted_o),
                .fetch_response_expected_o(ee_fetch_response_expected_o),
                .fetch_instruction_valid_o(ee_instruction_valid_o),
                .fetch_instruction_o(ee_instruction_o),
                .fetch_error_o(ee_fetch_error_o),
                .retirement_o(core_retirement),
                .reserved_instruction_o(core_reserved_instruction),
                .writeback_o(core_writeback),
                .gprs_o(ee_gprs_o)
            );

            assign ee_retirement_valid_o = core_retirement.valid;
            assign ee_retirement_pc_o = core_retirement.pc;
            assign ee_retirement_instruction_o = core_retirement.instruction;
            assign ee_reserved_valid_o = core_reserved_instruction.valid;
            assign ee_reserved_pc_o = core_reserved_instruction.pc;
            assign ee_reserved_instruction_o = core_reserved_instruction.instruction;
            assign ee_writeback_valid_o = core_writeback.valid;
            assign ee_writeback_destination_o = core_writeback.destination;
            assign ee_writeback_value_o = core_writeback.value;
        end else if (R5900_FETCH_ENABLE) begin : g_r5900_fetch
            r5900_fetch_path u_fetch_path (
                .clk_i(clk_o),
                .rst_ni(rst_no),
                .start_i(ee_fetch_start_i),
                .pc_i(ee_fetch_pc_i),
                .instruction_ready_i(ee_instruction_ready_i),
                .bus(memory_bus),
                .start_ready_o(ee_fetch_start_ready_o),
                .request_accepted_o(ee_fetch_request_accepted_o),
                .response_accepted_o(ee_fetch_response_accepted_o),
                .response_expected_o(ee_fetch_response_expected_o),
                .instruction_valid_o(ee_instruction_valid_o),
                .instruction_o(ee_instruction_o),
                .fetch_error_o(ee_fetch_error_o)
            );
            assign ee_control_state_o = 3'd0;
            assign ee_pc_o = 32'd0;
            assign ee_retirement_valid_o = 1'b0;
            assign ee_retirement_pc_o = 32'd0;
            assign ee_retirement_instruction_o = 32'd0;
            assign ee_reserved_valid_o = 1'b0;
            assign ee_reserved_pc_o = 32'd0;
            assign ee_reserved_instruction_o = 32'd0;
            assign ee_writeback_valid_o = 1'b0;
            assign ee_writeback_destination_o = 5'd0;
            assign ee_writeback_value_o = 128'd0;
            assign ee_gprs_o = 4096'd0;
        end else begin : g_external_memory_master
            assign memory_bus.req_valid = mem_req_valid_i;
            assign memory_bus.req_write = mem_req_write_i;
            assign memory_bus.req_addr = mem_req_addr_i;
            assign memory_bus.req_size = mem_req_size_i;
            assign memory_bus.req_wdata = mem_req_wdata_i;
            assign memory_bus.req_wstrb = mem_req_wstrb_i;
            assign memory_bus.rsp_ready = mem_rsp_ready_i;
            assign ee_fetch_start_ready_o = 1'b0;
            assign ee_fetch_request_accepted_o = 1'b0;
            assign ee_fetch_response_accepted_o = 1'b0;
            assign ee_fetch_response_expected_o = 1'b0;
            assign ee_instruction_valid_o = 1'b0;
            assign ee_instruction_o = 32'd0;
            assign ee_fetch_error_o = 1'b0;
            assign ee_control_state_o = 3'd0;
            assign ee_pc_o = 32'd0;
            assign ee_retirement_valid_o = 1'b0;
            assign ee_retirement_pc_o = 32'd0;
            assign ee_retirement_instruction_o = 32'd0;
            assign ee_reserved_valid_o = 1'b0;
            assign ee_reserved_pc_o = 32'd0;
            assign ee_reserved_instruction_o = 32'd0;
            assign ee_writeback_valid_o = 1'b0;
            assign ee_writeback_destination_o = 5'd0;
            assign ee_writeback_value_o = 128'd0;
            assign ee_gprs_o = 4096'd0;
        end
    endgenerate

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
