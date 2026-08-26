// SPDX-License-Identifier: MIT

`default_nettype none

module r5900_decode_dispatch_top (
    input  logic         decode_valid_i,
    input  logic [31:0]  pc_i,
    input  logic [31:0]  instruction_i,
    output logic         execute_valid_o,
    output logic [5:0]   operation_o,
    output logic         reserved_valid_o,
    output logic [31:0]  reserved_pc_o,
    output logic [31:0]  reserved_instruction_o
);

    timeunit 1ns;
    timeprecision 1ps;

    import r5900_types_pkg::*;

    r5900_reserved_instruction_t reserved_instruction;

    assign reserved_valid_o = reserved_instruction.valid;
    assign reserved_pc_o = reserved_instruction.pc;
    assign reserved_instruction_o = reserved_instruction.instruction;

    r5900_decode_dispatch u_decode_dispatch (
        .decode_valid_i,
        .pc_i,
        .instruction_i,
        .execute_valid_o,
        .operation_o,
        .reserved_instruction_o(reserved_instruction)
    );

endmodule

`default_nettype wire
