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
            (instruction_i[31:26] == 6'h00)
            && (instruction_i[10:6] == 5'h00)
            && (instruction_i[5:0] == 6'h14)
        ) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_DSLLV;
        end else if (
            (instruction_i[31:26] == 6'h00)
            && (instruction_i[10:6] == 5'h00)
            && (instruction_i[5:0] == 6'h16)
        ) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_DSRLV;
        end else if (
            (instruction_i[31:26] == 6'h00)
            && (instruction_i[10:6] == 5'h00)
            && (instruction_i[5:0] == 6'h21)
        ) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_ADDU;
        end else if (
            (instruction_i[31:26] == 6'h00)
            && (instruction_i[10:6] == 5'h00)
            && (instruction_i[5:0] == 6'h23)
        ) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_SUBU;
        end else if (
            (instruction_i[31:26] == 6'h00)
            && (instruction_i[10:6] == 5'h00)
            && (instruction_i[5:0] == 6'h24)
        ) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_AND;
        end else if (
            (instruction_i[31:26] == 6'h00)
            && (instruction_i[10:6] == 5'h00)
            && (instruction_i[5:0] == 6'h25)
        ) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_OR;
        end else if (
            (instruction_i[31:26] == 6'h00)
            && (instruction_i[10:6] == 5'h00)
            && (instruction_i[5:0] == 6'h26)
        ) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_XOR;
        end else if (
            (instruction_i[31:26] == 6'h00)
            && (instruction_i[10:6] == 5'h00)
            && (instruction_i[5:0] == 6'h27)
        ) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_NOR;
        end else if (
            (instruction_i[31:26] == 6'h00)
            && (instruction_i[10:6] == 5'h00)
            && (instruction_i[5:0] == 6'h2a)
        ) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_SLT;
        end else if (
            (instruction_i[31:26] == 6'h00)
            && (instruction_i[10:6] == 5'h00)
            && (instruction_i[5:0] == 6'h2b)
        ) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_SLTU;
        end else if (
            (instruction_i[31:26] == 6'h00)
            && (instruction_i[25:21] == 5'h00)
            && (instruction_i[5:0] == 6'h38)
        ) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_DSLL;
        end else if (
            (instruction_i[31:26] == 6'h00)
            && (instruction_i[25:21] == 5'h00)
            && (instruction_i[5:0] == 6'h3a)
        ) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_DSRL;
        end else if (
            (instruction_i[31:26] == 6'h00)
            && (instruction_i[25:21] == 5'h00)
            && (instruction_i[5:0] == 6'h3b)
        ) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_DSRA;
        end else if (
            (instruction_i[31:26] == 6'h00)
            && (instruction_i[25:21] == 5'h00)
            && (instruction_i[5:0] == 6'h3c)
        ) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_DSLL32;
        end else if (
            (instruction_i[31:26] == 6'h00)
            && (instruction_i[25:21] == 5'h00)
            && (instruction_i[5:0] == 6'h3e)
        ) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_DSRL32;
        end else if (
            (instruction_i[31:26] == 6'h00)
            && (instruction_i[25:21] == 5'h00)
            && (instruction_i[5:0] == 6'h3f)
        ) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_DSRA32;
        end else if (
            (instruction_i[31:26] == 6'h0f)
            && (instruction_i[25:21] == 5'h00)
        ) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_LUI;
        end else if (instruction_i[31:26] == 6'h0d) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_ORI;
        end else if (instruction_i[31:26] == 6'h0c) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_ANDI;
        end else if (instruction_i[31:26] == 6'h0e) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_XORI;
        end else if (instruction_i[31:26] == 6'h09) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_ADDIU;
        end else if (instruction_i[31:26] == 6'h0a) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_SLTI;
        end else if (instruction_i[31:26] == 6'h0b) begin
            legal_o = 1'b1;
            operation_o = R5900_OPERATION_SLTIU;
        end
    end

endmodule

`default_nettype wire
