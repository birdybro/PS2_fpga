// SPDX-License-Identifier: MIT

`default_nettype none

module r5900_core (
    input logic                                              clk_i,
    input logic                                              rst_ni,
    input logic                                              run_i,
    input r5900_types_pkg::r5900_pc_t                       start_pc_i,
    memory_bus_if                                            bus,
    output r5900_types_pkg::r5900_control_state_t           state_o,
    output r5900_types_pkg::r5900_pc_t                      pc_o,
    output logic                                             fetch_start_ready_o,
    output logic                                             fetch_request_accepted_o,
    output logic                                             fetch_response_accepted_o,
    output logic                                             fetch_response_expected_o,
    output logic                                             fetch_instruction_valid_o,
    output r5900_types_pkg::r5900_instruction_t             fetch_instruction_o,
    output logic                                             fetch_error_o,
    output r5900_types_pkg::r5900_retirement_t              retirement_o,
    output r5900_types_pkg::r5900_reserved_instruction_t    reserved_instruction_o,
    output r5900_types_pkg::r5900_writeback_t               writeback_o,
    output r5900_types_pkg::r5900_gpr_file_t                gprs_o
);

    timeunit 1ns;
    timeprecision 1ps;

    import r5900_types_pkg::*;

    r5900_control_state_t        state;
    r5900_instruction_t          instruction_q;
    r5900_operation_t            operation_q;
    r5900_retirement_t           retirement_q;
    r5900_reserved_instruction_t decoded_reserved_instruction;
    r5900_writeback_t            writeback;
    r5900_gpr_file_t             gprs;
    // The current scalar subset reads only the low 64-bit lane from each source.
    /* verilator lint_off UNUSEDSIGNAL */
    r5900_gpr_t                  source_rs;
    r5900_gpr_t                  source_rt;
    /* verilator lint_on UNUSEDSIGNAL */
    r5900_gpr_index_t            destination_index;
    logic                        fetch_path_start_ready;
    logic                        fetch_path_start;
    logic                        fetch_request_accepted;
    logic                        fetch_instruction_ready;
    logic                        decode_execute_valid;
    r5900_operation_t            decoded_operation;
    logic                        execute_complete;
    logic                        execute_pc_advance;
    logic                        execute_writeback_commit;
    r5900_gpr_index_t            execute_writeback_destination;
    r5900_gpr_t                  execute_writeback_value;
    logic                        execute_write_hi_valid;
    r5900_hilo_t                 execute_write_hi_value;
    logic                        execute_write_lo_valid;
    r5900_hilo_t                 execute_write_lo_value;
    r5900_hilo_t                 hi;
    r5900_hilo_t                 lo;
    r5900_hilo_t                 hi1;
    r5900_hilo_t                 lo1;
    r5900_hilo_state_t           hilo_state;
    r5900_retirement_t           execute_retirement;
    logic                        writeback_pending_q;
    r5900_gpr_index_t            writeback_destination_q;
    r5900_gpr_t                  writeback_value_q;
    logic                        writeback_commit_accepted;
    logic                        gpr_write_enable;
    r5900_gpr_index_t            gpr_write_index;
    r5900_gpr_t                  gpr_write_data;
    logic                        fetch_request_done;
    logic                        fetch_response_done;
    logic                        decode_done;
    logic                        execute_done;
    logic                        writeback_done;

    assign state_o = state;
    assign gprs_o = gprs;
    assign writeback_o = writeback;
    assign fetch_start_ready_o = run_i
        && (state == R5900_FETCH_REQUEST)
        && fetch_path_start_ready;
    assign fetch_path_start = fetch_start_ready_o;
    assign fetch_request_accepted_o = fetch_request_accepted;
    assign fetch_instruction_ready = state == R5900_FETCH_RESPONSE;

    assign fetch_request_done = (state == R5900_FETCH_REQUEST)
        && fetch_request_accepted;
    assign fetch_response_done = (state == R5900_FETCH_RESPONSE)
        && fetch_instruction_valid_o;
    assign decode_done = (state == R5900_DECODE)
        && (decode_execute_valid || decoded_reserved_instruction.valid);
    assign execute_done = (state == R5900_EXECUTE) && execute_complete;
    assign writeback_done = (state == R5900_WRITEBACK)
        && (!writeback_pending_q || writeback_commit_accepted);

    assign destination_index = (instruction_q[31:26] == 6'h00)
        ? instruction_q[15:11]
        : instruction_q[20:16];

    always_comb begin
        retirement_o = '0;
        reserved_instruction_o = '0;
        if (state == R5900_WRITEBACK) begin
            retirement_o = retirement_q;
        end
        if (state == R5900_DECODE) begin
            reserved_instruction_o = decoded_reserved_instruction;
        end
    end

    always_ff @(posedge clk_i) begin
        if (!rst_ni) begin
            instruction_q <= '0;
            operation_q <= R5900_OPERATION_NONE;
            retirement_q <= '0;
            writeback_pending_q <= 1'b0;
            writeback_destination_q <= '0;
            writeback_value_q <= '0;
        end else begin
            if (fetch_response_done) begin
                instruction_q <= fetch_instruction_o;
            end
            if (decode_done) begin
                operation_q <= decoded_operation;
            end
            if (execute_done) begin
                retirement_q <= execute_retirement;
                writeback_pending_q <= execute_writeback_commit;
                writeback_destination_q <= execute_writeback_destination;
                writeback_value_q <= execute_writeback_value;
            end
            if (writeback_done) begin
                retirement_q <= '0;
                writeback_pending_q <= 1'b0;
            end
        end
    end

    r5900_control u_control (
        .clk_i,
        .rst_ni,
        .fetch_request_done_i(fetch_request_done),
        .fetch_response_done_i(fetch_response_done),
        .decode_done_i(decode_done),
        .execute_done_i(execute_done),
        .writeback_done_i(writeback_done),
        .state_o(state)
    );

    r5900_pc u_pc (
        .clk_i,
        .rst_ni,
        .start_pc_i,
        .advance_i(execute_done && execute_pc_advance),
        .redirect_valid_i(1'b0),
        .redirect_pc_i('0),
        .pc_o
    );

    r5900_fetch_path u_fetch_path (
        .clk_i,
        .rst_ni,
        .start_i(fetch_path_start),
        .pc_i(pc_o),
        .instruction_ready_i(fetch_instruction_ready),
        .bus(bus),
        .start_ready_o(fetch_path_start_ready),
        .request_accepted_o(fetch_request_accepted),
        .response_accepted_o(fetch_response_accepted_o),
        .response_expected_o(fetch_response_expected_o),
        .instruction_valid_o(fetch_instruction_valid_o),
        .instruction_o(fetch_instruction_o),
        .fetch_error_o
    );

    r5900_decode_dispatch u_decode_dispatch (
        .decode_valid_i(state == R5900_DECODE),
        .pc_i(pc_o),
        .instruction_i(instruction_q),
        .execute_valid_o(decode_execute_valid),
        .operation_o(decoded_operation),
        .reserved_instruction_o(decoded_reserved_instruction)
    );

    r5900_execute u_execute (
        .execute_valid_i(state == R5900_EXECUTE),
        .operation_i(operation_q),
        .pc_i(pc_o),
        .instruction_i(instruction_q),
        .source_rs_shift_i(source_rs[4:0]),
        .source_rs_scalar_i(source_rs[63:0]),
        .source_rt_scalar_i(source_rt[63:0]),
        .source_hi_i(hi),
        .destination_upper_i(gprs[destination_index][127:64]),
        .complete_o(execute_complete),
        .pc_advance_o(execute_pc_advance),
        .writeback_commit_o(execute_writeback_commit),
        .writeback_destination_o(execute_writeback_destination),
        .writeback_value_o(execute_writeback_value),
        .write_hi_valid_o(execute_write_hi_valid),
        .write_hi_value_o(execute_write_hi_value),
        .write_lo_valid_o(execute_write_lo_valid),
        .write_lo_value_o(execute_write_lo_value),
        .retirement_o(execute_retirement)
    );

    r5900_hilo_state u_hilo_state (
        .clk_i,
        .write_hi_valid_i(execute_write_hi_valid),
        .write_hi_value_i(execute_write_hi_value),
        .write_lo_valid_i(execute_write_lo_valid),
        .write_lo_value_i(execute_write_lo_value),
        .write_hi1_valid_i(1'b0),
        .write_hi1_value_i('0),
        .write_lo1_valid_i(1'b0),
        .write_lo1_value_i('0),
        .hi_o(hi),
        .lo_o(lo),
        .hi1_o(hi1),
        .lo1_o(lo1),
        .state_o(hilo_state)
    );

    r5900_writeback u_writeback (
        .clk_i,
        .rst_ni,
        .commit_i((state == R5900_WRITEBACK) && writeback_pending_q),
        .destination_i(writeback_destination_q),
        .value_i(writeback_value_q),
        .commit_accepted_o(writeback_commit_accepted),
        .gpr_write_enable_o(gpr_write_enable),
        .gpr_write_index_o(gpr_write_index),
        .gpr_write_data_o(gpr_write_data),
        .writeback_o(writeback)
    );

    r5900_gpr_file u_gpr_file (
        .clk_i,
        .read_index_a_i(instruction_q[25:21]),
        .read_value_a_o(source_rs),
        .read_index_b_i(instruction_q[20:16]),
        .read_value_b_o(source_rt),
        .write_valid_i(gpr_write_enable),
        .write_index_i(gpr_write_index),
        .write_value_i(gpr_write_data),
        .state_o(gprs)
    );

    property p_pc_advances_only_after_execution;
        @(posedge clk_i) disable iff (!rst_ni)
            execute_pc_advance |-> (state == R5900_EXECUTE);
    endproperty

    property p_retirement_occurs_only_during_writeback;
        @(posedge clk_i) disable iff (!rst_ni)
            retirement_o.valid |-> (state == R5900_WRITEBACK);
    endproperty

    property p_hilo_views_match;
        @(posedge clk_i) {hi, lo, hi1, lo1} === hilo_state;
    endproperty

    assert property (p_pc_advances_only_after_execution)
        else $fatal(1, "R5900_CORE_PC_ADVANCE_STATE: PC advanced outside execute");

    assert property (p_retirement_occurs_only_during_writeback)
        else $fatal(1, "R5900_CORE_RETIREMENT_STATE: retirement emitted outside writeback");

    assert property (p_hilo_views_match)
        else $fatal(1, "R5900_CORE_HILO_VIEW: packed and individual HI/LO views differ");

endmodule

`default_nettype wire
