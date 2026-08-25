// SPDX-License-Identifier: MIT

`default_nettype none

module r5900_decode (
    input  r5900_types_pkg::r5900_instruction_t instruction_i,
    output logic                                  legal_o,
    output r5900_types_pkg::r5900_operation_t     operation_o
);

    timeunit 1ns;
    timeprecision 1ps;

    import r5900_types_pkg::*;

    always_comb begin
        legal_o = 1'b0;
        operation_o = R5900_OPERATION_NONE;

        if (instruction_i == 32'd0) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_NOP;
        end else if (
            (instruction_i[31:26] == 6'h00)
            && (instruction_i[25:21] == 5'h00)
            && (instruction_i[5:0] == 6'h00)
        ) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_SLL;
        end else if (
            (instruction_i[31:26] == 6'h00)
            && (instruction_i[25:21] == 5'h00)
            && (instruction_i[5:0] == 6'h02)
        ) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_SRL;
        end else if (
            (instruction_i[31:26] == 6'h00)
            && (instruction_i[25:21] == 5'h00)
            && (instruction_i[5:0] == 6'h03)
        ) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_SRA;
        end else if (
            (instruction_i[31:26] == 6'h00)
            && (instruction_i[10:6] == 5'h00)
            && (instruction_i[5:0] == 6'h04)
        ) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_SLLV;
        end else if (
            (instruction_i[31:26] == 6'h00)
            && (instruction_i[10:6] == 5'h00)
            && (instruction_i[5:0] == 6'h06)
        ) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_SRLV;
        end else if (
            (instruction_i[31:26] == 6'h00)
            && (instruction_i[10:6] == 5'h00)
            && (instruction_i[5:0] == 6'h07)
        ) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_SRAV;
        end else if (
            (instruction_i[31:26] == 6'h0f)
            && (instruction_i[25:21] == 5'h00)
        ) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_LUI;
        end
    end

endmodule

`default_nettype wire
