// SPDX-License-Identifier: MIT

`default_nettype none

module r5900_decode_dispatch (
    input logic                                              decode_valid_i,
    input r5900_types_pkg::r5900_pc_t                       pc_i,
    input r5900_types_pkg::r5900_instruction_t              instruction_i,
    output logic                                             execute_valid_o,
    output r5900_types_pkg::r5900_operation_t               operation_o,
    output r5900_types_pkg::r5900_reserved_instruction_t    reserved_instruction_o
);

    timeunit 1ns;
    timeprecision 1ps;

    import r5900_types_pkg::*;

    logic              decoded_legal;
    r5900_operation_t decoded_operation;

    r5900_decode u_decode (
        .instruction_i,
        .legal_o(decoded_legal),
        .operation_o(decoded_operation)
    );

    always_comb begin
        execute_valid_o = 1'b0;
        operation_o = R5900_OPERATION_NONE;
        reserved_instruction_o = '0;

        if (decode_valid_i) begin
            if (decoded_legal) begin
                execute_valid_o = 1'b1;
                operation_o = decoded_operation;
            end else begin
                reserved_instruction_o.valid = 1'b1;
                reserved_instruction_o.pc = pc_i;
                reserved_instruction_o.instruction = instruction_i;
            end
        end
    end

endmodule

`default_nettype wire
