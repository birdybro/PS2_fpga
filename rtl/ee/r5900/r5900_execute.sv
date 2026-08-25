// SPDX-License-Identifier: MIT

`default_nettype none

module r5900_execute (
    input logic                                      execute_valid_i,
    input r5900_types_pkg::r5900_operation_t        operation_i,
    input r5900_types_pkg::r5900_pc_t               pc_i,
    input r5900_types_pkg::r5900_instruction_t      instruction_i,
    output logic                                     complete_o,
    output logic                                     pc_advance_o,
    output logic                                     writeback_commit_o,
    output r5900_types_pkg::r5900_gpr_index_t       writeback_destination_o,
    output r5900_types_pkg::r5900_gpr_t             writeback_value_o,
    output r5900_types_pkg::r5900_retirement_t      retirement_o
);

    timeunit 1ns;
    timeprecision 1ps;

    import r5900_types_pkg::*;

    always_comb begin
        complete_o = 1'b0;
        pc_advance_o = 1'b0;
        writeback_commit_o = 1'b0;
        writeback_destination_o = '0;
        writeback_value_o = '0;
        retirement_o = '0;

        if (
            execute_valid_i
            && (operation_i == R5900_OPERATION_NOP)
            && (instruction_i == 32'd0)
        ) begin
            complete_o = 1'b1;
            pc_advance_o = 1'b1;
            retirement_o.valid = 1'b1;
            retirement_o.pc = pc_i;
            retirement_o.instruction = instruction_i;
        end
    end

endmodule

`default_nettype wire
