// SPDX-License-Identifier: MIT

`default_nettype none

module r5900_shift_immediate_top (
    input  logic          clk_i,
    input  logic          rst_ni,
    input  logic [31:0]   start_pc_i,
    input  logic          instruction_valid_i,
    input  logic [31:0]   instruction_i,
    input  logic          seed_commit_i,
    input  logic [4:0]    seed_destination_i,
    input  logic [127:0]  seed_value_i,
    output logic [31:0]   pc_o,
    output logic          execute_valid_o,
    output logic [4:0]    operation_o,
    output logic          execute_complete_o,
    output logic          pc_advance_o,
    output logic          execute_writeback_commit_o,
    output logic [4:0]    execute_writeback_destination_o,
    output logic [127:0]  execute_writeback_value_o,
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
    output logic [127:0]  source_rs_value_o,
    output logic [127:0]  source_rt_value_o,
    output logic [127:0]  destination_value_o,
    output logic [4095:0] gprs_o
);

    timeunit 1ns;
    timeprecision 1ps;

    import r5900_types_pkg::*;

    r5900_retirement_t            retirement;
    r5900_reserved_instruction_t reserved_instruction;
    r5900_writeback_t             writeback;
    logic                         execute_writeback_commit;
    r5900_gpr_index_t            execute_writeback_destination;
    r5900_gpr_t                  execute_writeback_value;
    logic                         central_commit;
    r5900_gpr_index_t            central_destination;
    r5900_gpr_t                  central_value;
    logic                         gpr_write_enable;
    r5900_gpr_index_t            gpr_write_index;
    r5900_gpr_t                  gpr_write_data;

    assign central_commit = seed_commit_i || execute_writeback_commit;
    assign central_destination = seed_commit_i
        ? seed_destination_i
        : execute_writeback_destination;
    assign central_value = seed_commit_i ? seed_value_i : execute_writeback_value;

    assign execute_writeback_commit_o = execute_writeback_commit;
    assign execute_writeback_destination_o = execute_writeback_destination;
    assign execute_writeback_value_o = execute_writeback_value;
    assign writeback_valid_o = writeback.valid;
    assign writeback_destination_o = writeback.destination;
    assign writeback_value_o = writeback.value;
    assign retirement_valid_o = retirement.valid;
    assign retirement_pc_o = retirement.pc;
    assign retirement_instruction_o = retirement.instruction;
    assign reserved_valid_o = reserved_instruction.valid;
    assign reserved_pc_o = reserved_instruction.pc;
    assign reserved_instruction_o = reserved_instruction.instruction;
    assign source_rs_value_o = gprs_o[
        (instruction_i[25:21] * R5900_GPR_WIDTH) +: R5900_GPR_WIDTH
    ];

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
        .source_rs_shift_i(source_rs_value_o[4:0]),
        .source_rs_scalar_i(source_rs_value_o[63:0]),
        .source_rt_word_i(source_rt_value_o[31:0]),
        .destination_upper_i(destination_value_o[127:64]),
        .complete_o(execute_complete_o),
        .pc_advance_o,
        .writeback_commit_o(execute_writeback_commit),
        .writeback_destination_o(execute_writeback_destination),
        .writeback_value_o(execute_writeback_value),
        .retirement_o(retirement)
    );

    r5900_pc u_pc (
        .clk_i,
        .rst_ni,
        .start_pc_i,
        .advance_i(pc_advance_o),
        .redirect_valid_i(1'b0),
        .redirect_pc_i(32'd0),
        .pc_o
    );

    r5900_writeback u_writeback (
        .clk_i,
        .rst_ni,
        .commit_i(central_commit),
        .destination_i(central_destination),
        .value_i(central_value),
        .commit_accepted_o,
        .gpr_write_enable_o(gpr_write_enable),
        .gpr_write_index_o(gpr_write_index),
        .gpr_write_data_o(gpr_write_data),
        .writeback_o(writeback)
    );

    r5900_gpr_file u_gpr_file (
        .clk_i,
        .read_index_a_i(instruction_i[20:16]),
        .read_value_a_o(source_rt_value_o),
        .read_index_b_i(
            (instruction_i[31:26] == 6'h0c)
                || (instruction_i[31:26] == 6'h0d)
                || (instruction_i[31:26] == 6'h0e)
                || (instruction_i[31:26] == 6'h0f)
                ? instruction_i[20:16]
                : instruction_i[15:11]
        ),
        .read_value_b_o(destination_value_o),
        .write_valid_i(gpr_write_enable),
        .write_index_i(gpr_write_index),
        .write_value_i(gpr_write_data),
        .state_o(gprs_o)
    );

endmodule

`default_nettype wire
