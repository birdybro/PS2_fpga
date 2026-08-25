// SPDX-License-Identifier: MIT

`default_nettype none

module r5900_execute (
    input logic                                      execute_valid_i,
    input r5900_types_pkg::r5900_operation_t        operation_i,
    input r5900_types_pkg::r5900_pc_t               pc_i,
    input r5900_types_pkg::r5900_instruction_t      instruction_i,
    input r5900_types_pkg::r5900_shift_amount_t     source_rs_shift_i,
    input logic [63:0]                               source_rs_scalar_i,
    input logic [31:0]                               source_rt_word_i,
    input logic [63:0]                               destination_upper_i,
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

    logic [31:0] sll_word;
    logic [31:0] srl_word;
    logic signed [31:0] sra_source_word;
    logic [31:0] sra_word;
    logic [31:0] sllv_word;
    logic [31:0] srlv_word;
    logic [31:0] srav_word;
    logic [31:0] addiu_word;

    assign sll_word = source_rt_word_i << instruction_i[10:6];
    assign srl_word = source_rt_word_i >> instruction_i[10:6];
    assign sra_source_word = $signed(source_rt_word_i);
    assign sra_word = sra_source_word >>> instruction_i[10:6];
    assign sllv_word = source_rt_word_i << source_rs_shift_i;
    assign srlv_word = source_rt_word_i >> source_rs_shift_i;
    assign srav_word = sra_source_word >>> source_rs_shift_i;
    assign addiu_word = source_rs_scalar_i[31:0]
        + {{16{instruction_i[15]}}, instruction_i[15:0]};

    always_comb begin
        complete_o = 1'b0;
        pc_advance_o = 1'b0;
        writeback_commit_o = 1'b0;
        writeback_destination_o = '0;
        writeback_value_o = '0;
        retirement_o = '0;

        if (execute_valid_i) begin
            unique case (operation_i)
                R5900_OPERATION_NOP: begin
                    if (instruction_i == 32'd0) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_SLL: begin
                    if (
                        (instruction_i != 32'd0)
                        && (instruction_i[31:26] == 6'h00)
                        && (instruction_i[25:21] == 5'h00)
                        && (instruction_i[5:0] == 6'h00)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {
                            destination_upper_i,
                            {32{sll_word[31]}},
                            sll_word
                        };
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_SRL: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[25:21] == 5'h00)
                        && (instruction_i[5:0] == 6'h02)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {
                            destination_upper_i,
                            {32{srl_word[31]}},
                            srl_word
                        };
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_SRA: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[25:21] == 5'h00)
                        && (instruction_i[5:0] == 6'h03)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {
                            destination_upper_i,
                            {32{sra_word[31]}},
                            sra_word
                        };
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_SLLV: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[10:6] == 5'h00)
                        && (instruction_i[5:0] == 6'h04)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {
                            destination_upper_i,
                            {32{sllv_word[31]}},
                            sllv_word
                        };
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_SRLV: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[10:6] == 5'h00)
                        && (instruction_i[5:0] == 6'h06)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {
                            destination_upper_i,
                            {32{srlv_word[31]}},
                            srlv_word
                        };
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_SRAV: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[10:6] == 5'h00)
                        && (instruction_i[5:0] == 6'h07)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {
                            destination_upper_i,
                            {32{srav_word[31]}},
                            srav_word
                        };
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_LUI: begin
                    if (
                        (instruction_i[31:26] == 6'h0f)
                        && (instruction_i[25:21] == 5'h00)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[20:16];
                        writeback_value_o = {
                            destination_upper_i,
                            {32{instruction_i[15]}},
                            instruction_i[15:0],
                            16'd0
                        };
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_ORI: begin
                    if (instruction_i[31:26] == 6'h0d) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[20:16];
                        writeback_value_o = {
                            destination_upper_i,
                            source_rs_scalar_i | {48'd0, instruction_i[15:0]}
                        };
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_ANDI: begin
                    if (instruction_i[31:26] == 6'h0c) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[20:16];
                        writeback_value_o = {
                            destination_upper_i,
                            source_rs_scalar_i & {48'd0, instruction_i[15:0]}
                        };
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_XORI: begin
                    if (instruction_i[31:26] == 6'h0e) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[20:16];
                        writeback_value_o = {
                            destination_upper_i,
                            source_rs_scalar_i ^ {48'd0, instruction_i[15:0]}
                        };
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_ADDIU: begin
                    if (instruction_i[31:26] == 6'h09) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[20:16];
                        writeback_value_o = {
                            destination_upper_i,
                            {32{addiu_word[31]}},
                            addiu_word
                        };
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                default: begin
                end
            endcase
        end
    end

endmodule

`default_nettype wire
