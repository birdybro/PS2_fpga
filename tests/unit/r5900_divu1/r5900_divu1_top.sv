// SPDX-License-Identifier: MIT

`default_nettype none

module r5900_divu1_top (
    input  logic          clk_i,
    input  logic          rst_ni,
    input  logic [31:0]   start_pc_i,
    input  logic          instruction_valid_i,
    input  logic [31:0]   instruction_i,
    input  logic          seed_gpr_commit_i,
    input  logic [4:0]    seed_gpr_destination_i,
    input  logic [127:0]  seed_gpr_value_i,
    input  logic          seed_hilo_commit_i,
    input  logic [63:0]   seed_hi_i,
    input  logic [63:0]   seed_lo_i,
    input  logic [63:0]   seed_hi1_i,
    input  logic [63:0]   seed_lo1_i,
    output logic [31:0]   pc_o,
    output logic          execute_valid_o,
    output logic [5:0]    operation_o,
    output logic          execute_complete_o,
    output logic          pc_advance_o,
    output logic          execute_writeback_commit_o,
    output logic [4:0]    execute_writeback_destination_o,
    output logic [127:0]  execute_writeback_value_o,
    output logic          execute_write_hi_valid_o,
    output logic [63:0]   execute_write_hi_value_o,
    output logic          execute_write_lo_valid_o,
    output logic [63:0]   execute_write_lo_value_o,
    output logic          execute_write_hi1_valid_o,
    output logic [63:0]   execute_write_hi1_value_o,
    output logic          execute_write_lo1_valid_o,
    output logic [63:0]   execute_write_lo1_value_o,
    output logic          commit_accepted_o,
    output logic          writeback_valid_o,
    output logic [4:0]    writeback_destination_o,
    output logic [127:0]  writeback_value_o,
    output logic          retirement_valid_o,
    output logic [31:0]   retirement_pc_o,
    output logic [31:0]   retirement_instruction_o,
    output logic          reserved_valid_o,
    output logic [31:0]   reserved_pc_o,
    output logic [31:0]   reserved_instruction_o,
    output logic [63:0]   hi_o,
    output logic [63:0]   lo_o,
    output logic [63:0]   hi1_o,
    output logic [63:0]   lo1_o,
    output logic [255:0]  hilo_state_o,
    output logic [4095:0] gprs_o
);

    timeunit 1ns;
    timeprecision 1ps;

    import r5900_types_pkg::*;

    r5900_retirement_t            retirement;
    r5900_reserved_instruction_t reserved_instruction;
    r5900_writeback_t             writeback;
    r5900_gpr_file_t              gprs;
    r5900_gpr_t                   source_rs;
    r5900_gpr_t                   source_rt;
    logic                         gpr_write_enable;
    r5900_gpr_index_t            gpr_write_index;
    r5900_gpr_t                  gpr_write_data;
    logic                         hilo_write_hi_valid;
    r5900_hilo_t                 hilo_write_hi_value;
    logic                         hilo_write_lo_valid;
    r5900_hilo_t                 hilo_write_lo_value;
    logic                         hilo_write_hi1_valid;
    r5900_hilo_t                 hilo_write_hi1_value;
    logic                         hilo_write_lo1_valid;
    r5900_hilo_t                 hilo_write_lo1_value;

    assign writeback_valid_o = writeback.valid;
    assign writeback_destination_o = writeback.destination;
    assign writeback_value_o = writeback.value;
    assign retirement_valid_o = retirement.valid;
    assign retirement_pc_o = retirement.pc;
    assign retirement_instruction_o = retirement.instruction;
    assign reserved_valid_o = reserved_instruction.valid;
    assign reserved_pc_o = reserved_instruction.pc;
    assign reserved_instruction_o = reserved_instruction.instruction;
    assign gprs_o = gprs;
    assign hilo_write_hi_valid = seed_hilo_commit_i || execute_write_hi_valid_o;
    assign hilo_write_hi_value = seed_hilo_commit_i ? seed_hi_i : execute_write_hi_value_o;
    assign hilo_write_lo_valid = seed_hilo_commit_i || execute_write_lo_valid_o;
    assign hilo_write_lo_value = seed_hilo_commit_i ? seed_lo_i : execute_write_lo_value_o;
    assign hilo_write_hi1_valid = seed_hilo_commit_i || execute_write_hi1_valid_o;
    assign hilo_write_hi1_value = seed_hilo_commit_i ? seed_hi1_i : execute_write_hi1_value_o;
    assign hilo_write_lo1_valid = seed_hilo_commit_i || execute_write_lo1_valid_o;
    assign hilo_write_lo1_value = seed_hilo_commit_i ? seed_lo1_i : execute_write_lo1_value_o;

    r5900_decode_dispatch u_decode_dispatch (
        .decode_valid_i(instruction_valid_i),
        .pc_i(pc_o),
        .instruction_i,
        .execute_valid_o,
        .operation_o,
        .reserved_instruction_o(reserved_instruction)
    );

    r5900_execute u_execute (
        .execute_valid_i(execute_valid_o),
        .operation_i(operation_o),
        .pc_i(pc_o),
        .instruction_i,
        .source_rs_shift_i(source_rs[4:0]),
        .source_rs_scalar_i(source_rs[63:0]),
        .source_rt_scalar_i(source_rt[63:0]),
        .source_hi_i(hi_o),
        .source_lo_i(lo_o),
        .source_hi1_i(hi1_o),
        .destination_upper_i(gprs[instruction_i[15:11]][127:64]),
        .complete_o(execute_complete_o),
        .pc_advance_o,
        .writeback_commit_o(execute_writeback_commit_o),
        .writeback_destination_o(execute_writeback_destination_o),
        .writeback_value_o(execute_writeback_value_o),
        .write_hi_valid_o(execute_write_hi_valid_o),
        .write_hi_value_o(execute_write_hi_value_o),
        .write_lo_valid_o(execute_write_lo_valid_o),
        .write_lo_value_o(execute_write_lo_value_o),
        .write_hi1_valid_o(execute_write_hi1_valid_o),
        .write_hi1_value_o(execute_write_hi1_value_o),
        .write_lo1_valid_o(execute_write_lo1_valid_o),
        .write_lo1_value_o(execute_write_lo1_value_o),
        .retirement_o(retirement)
    );

    r5900_pc u_pc (
        .clk_i,
        .rst_ni,
        .start_pc_i,
        .advance_i(pc_advance_o),
        .redirect_valid_i(1'b0),
        .redirect_pc_i('0),
        .pc_o
    );

    r5900_writeback u_writeback (
        .clk_i,
        .rst_ni,
        .commit_i(seed_gpr_commit_i || execute_writeback_commit_o),
        .destination_i(
            seed_gpr_commit_i ? seed_gpr_destination_i : execute_writeback_destination_o
        ),
        .value_i(seed_gpr_commit_i ? seed_gpr_value_i : execute_writeback_value_o),
        .commit_accepted_o,
        .gpr_write_enable_o(gpr_write_enable),
        .gpr_write_index_o(gpr_write_index),
        .gpr_write_data_o(gpr_write_data),
        .writeback_o(writeback)
    );

    r5900_gpr_file u_gpr_file (
        .clk_i,
        .read_index_a_i(instruction_i[25:21]),
        .read_value_a_o(source_rs),
        .read_index_b_i(instruction_i[20:16]),
        .read_value_b_o(source_rt),
        .write_valid_i(gpr_write_enable),
        .write_index_i(gpr_write_index),
        .write_value_i(gpr_write_data),
        .state_o(gprs)
    );

    r5900_hilo_state u_hilo_state (
        .clk_i,
        .write_hi_valid_i(hilo_write_hi_valid),
        .write_hi_value_i(hilo_write_hi_value),
        .write_lo_valid_i(hilo_write_lo_valid),
        .write_lo_value_i(hilo_write_lo_value),
        .write_hi1_valid_i(hilo_write_hi1_valid),
        .write_hi1_value_i(hilo_write_hi1_value),
        .write_lo1_valid_i(hilo_write_lo1_valid),
        .write_lo1_value_i(hilo_write_lo1_value),
        .hi_o,
        .lo_o,
        .hi1_o,
        .lo1_o,
        .state_o(hilo_state_o)
    );

endmodule

`default_nettype wire
