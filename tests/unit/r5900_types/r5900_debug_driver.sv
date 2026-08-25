// SPDX-License-Identifier: MIT

`default_nettype none

module r5900_debug_driver (
    input logic [31:0]   pc_i,
    input logic [4095:0] gprs_i,
    input logic [31:0]   instruction_i,
    input logic          writeback_valid_i,
    input logic [4:0]    writeback_destination_i,
    input logic [127:0]  writeback_value_i,
    input logic          reserved_valid_i,
    input logic [31:0]   reserved_pc_i,
    input logic [31:0]   reserved_instruction_i,
    input logic          retirement_valid_i,
    input logic [31:0]   retirement_pc_i,
    input logic [31:0]   retirement_instruction_i,
    r5900_debug_if.producer debug_o
);

    timeunit 1ns;
    timeprecision 1ps;

    assign debug_o.arch_state.pc = pc_i;
    assign debug_o.arch_state.gprs = gprs_i;
    assign debug_o.instruction = instruction_i;
    assign debug_o.writeback.valid = writeback_valid_i;
    assign debug_o.writeback.destination = writeback_destination_i;
    assign debug_o.writeback.value = writeback_value_i;
    assign debug_o.reserved_instruction.valid = reserved_valid_i;
    assign debug_o.reserved_instruction.pc = reserved_pc_i;
    assign debug_o.reserved_instruction.instruction = reserved_instruction_i;
    assign debug_o.retirement.valid = retirement_valid_i;
    assign debug_o.retirement.pc = retirement_pc_i;
    assign debug_o.retirement.instruction = retirement_instruction_i;

endmodule

`default_nettype wire
