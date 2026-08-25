// SPDX-License-Identifier: MIT

`default_nettype none

module r5900_debug_probe (
    r5900_debug_if.monitor debug_i,
    output logic [31:0]   pc_o,
    output logic [4095:0] gprs_o,
    output logic [127:0]  gpr_zero_o,
    output logic [127:0]  gpr_last_o,
    output logic [31:0]   instruction_o,
    output logic          writeback_valid_o,
    output logic [4:0]    writeback_destination_o,
    output logic [127:0]  writeback_value_o,
    output logic          reserved_valid_o,
    output logic [31:0]   reserved_pc_o,
    output logic [31:0]   reserved_instruction_o
);

    timeunit 1ns;
    timeprecision 1ps;

    assign pc_o = debug_i.arch_state.pc;
    assign gprs_o = debug_i.arch_state.gprs;
    assign gpr_zero_o = debug_i.arch_state.gprs[0];
    assign gpr_last_o = debug_i.arch_state.gprs[31];
    assign instruction_o = debug_i.instruction;
    assign writeback_valid_o = debug_i.writeback.valid;
    assign writeback_destination_o = debug_i.writeback.destination;
    assign writeback_value_o = debug_i.writeback.value;
    assign reserved_valid_o = debug_i.reserved_instruction.valid;
    assign reserved_pc_o = debug_i.reserved_instruction.pc;
    assign reserved_instruction_o = debug_i.reserved_instruction.instruction;

endmodule

`default_nettype wire
