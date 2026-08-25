// SPDX-License-Identifier: MIT

`default_nettype none

module r5900_instruction_fields (
    input  r5900_types_pkg::r5900_instruction_t   instruction_i,
    output r5900_types_pkg::r5900_opcode_t        opcode_o,
    output r5900_types_pkg::r5900_gpr_index_t     rs_o,
    output r5900_types_pkg::r5900_gpr_index_t     rt_o,
    output r5900_types_pkg::r5900_gpr_index_t     rd_o,
    output r5900_types_pkg::r5900_shift_amount_t  shift_amount_o,
    output r5900_types_pkg::r5900_function_t      function_o,
    output r5900_types_pkg::r5900_immediate_t     immediate_o,
    output logic [31:0]                           immediate_sign_extended_o,
    output logic [31:0]                           immediate_zero_extended_o,
    output r5900_types_pkg::r5900_target_t        target_o
);

    timeunit 1ns;
    timeprecision 1ps;

    assign opcode_o = instruction_i[31:26];
    assign rs_o = instruction_i[25:21];
    assign rt_o = instruction_i[20:16];
    assign rd_o = instruction_i[15:11];
    assign shift_amount_o = instruction_i[10:6];
    assign function_o = instruction_i[5:0];
    assign immediate_o = instruction_i[15:0];
    assign immediate_sign_extended_o = {{16{instruction_i[15]}}, instruction_i[15:0]};
    assign immediate_zero_extended_o = {16'd0, instruction_i[15:0]};
    assign target_o = instruction_i[25:0];

endmodule

`default_nettype wire
