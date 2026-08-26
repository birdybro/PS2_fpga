// SPDX-License-Identifier: MIT

`default_nettype none

module r5900_execute (
    input logic                                      execute_valid_i,
    input r5900_types_pkg::r5900_operation_t        operation_i,
    input r5900_types_pkg::r5900_pc_t               pc_i,
    input r5900_types_pkg::r5900_instruction_t      instruction_i,
    input r5900_types_pkg::r5900_shift_amount_t     source_rs_shift_i,
    input logic [63:0]                               source_rs_scalar_i,
    input logic [63:0]                               source_rt_scalar_i,
    input logic [63:0]                               source_hi_i,
    input logic [63:0]                               source_lo_i,
    input logic [63:0]                               source_hi1_i,
    input logic [63:0]                               destination_upper_i,
    output logic                                     complete_o,
    output logic                                     pc_advance_o,
    output logic                                     writeback_commit_o,
    output r5900_types_pkg::r5900_gpr_index_t       writeback_destination_o,
    output r5900_types_pkg::r5900_gpr_t             writeback_value_o,
    output logic                                     write_hi_valid_o,
    output r5900_types_pkg::r5900_hilo_t            write_hi_value_o,
    output logic                                     write_lo_valid_o,
    output r5900_types_pkg::r5900_hilo_t            write_lo_value_o,
    output logic                                     write_hi1_valid_o,
    output r5900_types_pkg::r5900_hilo_t            write_hi1_value_o,
    output logic                                     write_lo1_valid_o,
    output r5900_types_pkg::r5900_hilo_t            write_lo1_value_o,
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
    logic [63:0] dsllv_scalar;
    logic [63:0] dsrlv_scalar;
    logic [63:0] dsrav_scalar;
    logic [63:0] dsll_scalar;
    logic [63:0] dsrl_scalar;
    logic signed [63:0] dsra_source_scalar;
    logic [63:0] dsra_scalar;
    logic [5:0] high_shift_amount;
    logic [63:0] dsll32_scalar;
    logic [63:0] dsrl32_scalar;
    logic [63:0] dsra32_scalar;
    logic [31:0] addiu_word;
    logic [63:0] daddiu_scalar;
    logic [31:0] addu_word;
    logic [63:0] daddu_scalar;
    logic [31:0] subu_word;
    logic [63:0] dsubu_scalar;
    logic signed [31:0] mult_source_rs_word;
    logic signed [31:0] mult_source_rt_word;
    logic signed [63:0] mult_product;
    logic [63:0] mult_hi;
    logic [63:0] mult_lo;
    logic [63:0] multu_product;
    logic [63:0] multu_hi;
    logic [63:0] multu_lo;
    logic signed [31:0] div_dividend;
    logic signed [31:0] div_divisor;
    logic signed [31:0] div_quotient;
    logic signed [31:0] div_remainder;
    logic div_overflow;
    logic [31:0] divu_quotient;
    logic [31:0] divu_remainder;
    logic signed [63:0] slt_source_rs_scalar;
    logic signed [63:0] slt_source_rt_scalar;
    logic slt_result;
    logic sltu_result;
    logic signed [63:0] slti_immediate;
    logic slti_result;
    logic [63:0] sltiu_immediate;
    logic sltiu_result;

    assign sll_word = source_rt_scalar_i[31:0] << instruction_i[10:6];
    assign srl_word = source_rt_scalar_i[31:0] >> instruction_i[10:6];
    assign sra_source_word = $signed(source_rt_scalar_i[31:0]);
    assign sra_word = sra_source_word >>> instruction_i[10:6];
    assign sllv_word = source_rt_scalar_i[31:0] << source_rs_shift_i;
    assign srlv_word = source_rt_scalar_i[31:0] >> source_rs_shift_i;
    assign srav_word = sra_source_word >>> source_rs_shift_i;
    assign dsllv_scalar = source_rt_scalar_i << source_rs_scalar_i[5:0];
    assign dsrlv_scalar = source_rt_scalar_i >> source_rs_scalar_i[5:0];
    assign dsrav_scalar = dsra_source_scalar >>> source_rs_scalar_i[5:0];
    assign dsll_scalar = source_rt_scalar_i << instruction_i[10:6];
    assign dsrl_scalar = source_rt_scalar_i >> instruction_i[10:6];
    assign dsra_source_scalar = $signed(source_rt_scalar_i);
    assign dsra_scalar = dsra_source_scalar >>> instruction_i[10:6];
    assign high_shift_amount = {1'b1, instruction_i[10:6]};
    assign dsll32_scalar = source_rt_scalar_i << high_shift_amount;
    assign dsrl32_scalar = source_rt_scalar_i >> high_shift_amount;
    assign dsra32_scalar = dsra_source_scalar >>> high_shift_amount;
    assign addiu_word = source_rs_scalar_i[31:0]
        + {{16{instruction_i[15]}}, instruction_i[15:0]};
    assign daddiu_scalar = source_rs_scalar_i
        + {{48{instruction_i[15]}}, instruction_i[15:0]};
    assign addu_word = source_rs_scalar_i[31:0] + source_rt_scalar_i[31:0];
    assign daddu_scalar = source_rs_scalar_i + source_rt_scalar_i;
    assign subu_word = source_rs_scalar_i[31:0] - source_rt_scalar_i[31:0];
    assign dsubu_scalar = source_rs_scalar_i - source_rt_scalar_i;
    assign mult_source_rs_word = $signed(source_rs_scalar_i[31:0]);
    assign mult_source_rt_word = $signed(source_rt_scalar_i[31:0]);
    assign mult_product = mult_source_rs_word * mult_source_rt_word;
    assign mult_hi = {{32{mult_product[63]}}, mult_product[63:32]};
    assign mult_lo = {{32{mult_product[31]}}, mult_product[31:0]};
    assign multu_product = source_rs_scalar_i[31:0] * source_rt_scalar_i[31:0];
    assign multu_hi = {{32{multu_product[63]}}, multu_product[63:32]};
    assign multu_lo = {{32{multu_product[31]}}, multu_product[31:0]};
    assign div_dividend = $signed(source_rs_scalar_i[31:0]);
    assign div_divisor = $signed(source_rt_scalar_i[31:0]);
    assign div_overflow = (source_rs_scalar_i[31:0] == 32'h8000_0000)
        && (source_rt_scalar_i[31:0] == 32'hffff_ffff);
    assign slt_source_rs_scalar = $signed(source_rs_scalar_i);
    assign slt_source_rt_scalar = $signed(source_rt_scalar_i);
    assign slt_result = slt_source_rs_scalar < slt_source_rt_scalar;
    assign sltu_result = source_rs_scalar_i < source_rt_scalar_i;
    assign slti_immediate = $signed({{48{instruction_i[15]}}, instruction_i[15:0]});
    assign slti_result = slt_source_rs_scalar < slti_immediate;
    assign sltiu_immediate = {{48{instruction_i[15]}}, instruction_i[15:0]};
    assign sltiu_result = source_rs_scalar_i < sltiu_immediate;

    always_comb begin
        div_quotient = '0;
        div_remainder = '0;
        if ((div_divisor != 32'sd0) && !div_overflow) begin
            div_quotient = div_dividend / div_divisor;
            div_remainder = div_dividend % div_divisor;
        end
    end

    always_comb begin
        divu_quotient = '0;
        divu_remainder = '0;
        if (source_rt_scalar_i[31:0] != 32'd0) begin
            divu_quotient = source_rs_scalar_i[31:0] / source_rt_scalar_i[31:0];
            divu_remainder = source_rs_scalar_i[31:0] % source_rt_scalar_i[31:0];
        end
    end

    always_comb begin
        complete_o = 1'b0;
        pc_advance_o = 1'b0;
        writeback_commit_o = 1'b0;
        writeback_destination_o = '0;
        writeback_value_o = '0;
        write_hi_valid_o = 1'b0;
        write_hi_value_o = '0;
        write_lo_valid_o = 1'b0;
        write_lo_value_o = '0;
        write_hi1_valid_o = 1'b0;
        write_hi1_value_o = '0;
        write_lo1_valid_o = 1'b0;
        write_lo1_value_o = '0;
        retirement_o = '0;

        if (execute_valid_i) begin
            unique case (operation_i)
                R5900_OPERATION_MULT: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[10:6] == 5'h00)
                        && (instruction_i[5:0] == 6'h18)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = instruction_i[15:11] != 5'd0;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {destination_upper_i, mult_lo};
                        write_hi_valid_o = 1'b1;
                        write_hi_value_o = mult_hi;
                        write_lo_valid_o = 1'b1;
                        write_lo_value_o = mult_lo;
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_MULTU: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[10:6] == 5'h00)
                        && (instruction_i[5:0] == 6'h19)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = instruction_i[15:11] != 5'd0;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {destination_upper_i, multu_lo};
                        write_hi_valid_o = 1'b1;
                        write_hi_value_o = multu_hi;
                        write_lo_valid_o = 1'b1;
                        write_lo_value_o = multu_lo;
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_DIV: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[15:6] == 10'h000)
                        && (instruction_i[5:0] == 6'h1a)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        write_hi_valid_o = 1'b1;
                        write_lo_valid_o = 1'b1;
                        if (div_overflow) begin
                            write_hi_value_o = 64'd0;
                            write_lo_value_o = 64'hffff_ffff_8000_0000;
                        end else if (div_divisor == 32'sd0) begin
                            write_hi_value_o = {{32{div_dividend[31]}}, div_dividend};
                            write_lo_value_o = div_dividend[31]
                                ? 64'd1
                                : 64'hffff_ffff_ffff_ffff;
                        end else begin
                            write_hi_value_o = {{32{div_remainder[31]}}, div_remainder};
                            write_lo_value_o = {{32{div_quotient[31]}}, div_quotient};
                        end
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_DIVU: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[15:6] == 10'h000)
                        && (instruction_i[5:0] == 6'h1b)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        write_hi_valid_o = 1'b1;
                        write_lo_valid_o = 1'b1;
                        if (source_rt_scalar_i[31:0] == 32'd0) begin
                            write_hi_value_o = {
                                {32{source_rs_scalar_i[31]}}, source_rs_scalar_i[31:0]
                            };
                            write_lo_value_o = 64'hffff_ffff_ffff_ffff;
                        end else begin
                            write_hi_value_o = {{32{divu_remainder[31]}}, divu_remainder};
                            write_lo_value_o = {{32{divu_quotient[31]}}, divu_quotient};
                        end
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_MFHI: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[25:16] == 10'h000)
                        && (instruction_i[10:6] == 5'h00)
                        && (instruction_i[5:0] == 6'h10)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {destination_upper_i, source_hi_i};
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_MFLO: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[25:16] == 10'h000)
                        && (instruction_i[10:6] == 5'h00)
                        && (instruction_i[5:0] == 6'h12)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {destination_upper_i, source_lo_i};
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_MTHI: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[20:6] == 15'h0000)
                        && (instruction_i[5:0] == 6'h11)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        write_hi_valid_o = 1'b1;
                        write_hi_value_o = source_rs_scalar_i;
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_MTLO: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[20:6] == 15'h0000)
                        && (instruction_i[5:0] == 6'h13)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        write_lo_valid_o = 1'b1;
                        write_lo_value_o = source_rs_scalar_i;
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_MULT1: begin
                    if (
                        (instruction_i[31:26] == 6'h1c)
                        && (instruction_i[10:6] == 5'h00)
                        && (instruction_i[5:0] == 6'h18)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = instruction_i[15:11] != 5'd0;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {destination_upper_i, mult_lo};
                        write_hi1_valid_o = 1'b1;
                        write_hi1_value_o = mult_hi;
                        write_lo1_valid_o = 1'b1;
                        write_lo1_value_o = mult_lo;
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_MULTU1: begin
                    if (
                        (instruction_i[31:26] == 6'h1c)
                        && (instruction_i[10:6] == 5'h00)
                        && (instruction_i[5:0] == 6'h19)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = instruction_i[15:11] != 5'd0;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {destination_upper_i, multu_lo};
                        write_hi1_valid_o = 1'b1;
                        write_hi1_value_o = multu_hi;
                        write_lo1_valid_o = 1'b1;
                        write_lo1_value_o = multu_lo;
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_DIV1: begin
                    if (
                        (instruction_i[31:26] == 6'h1c)
                        && (instruction_i[15:6] == 10'h000)
                        && (instruction_i[5:0] == 6'h1a)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        write_hi1_valid_o = 1'b1;
                        write_lo1_valid_o = 1'b1;
                        if (div_overflow) begin
                            write_hi1_value_o = 64'd0;
                            write_lo1_value_o = 64'hffff_ffff_8000_0000;
                        end else if (div_divisor == 32'sd0) begin
                            write_hi1_value_o = {{32{div_dividend[31]}}, div_dividend};
                            write_lo1_value_o = div_dividend[31]
                                ? 64'd1
                                : 64'hffff_ffff_ffff_ffff;
                        end else begin
                            write_hi1_value_o = {{32{div_remainder[31]}}, div_remainder};
                            write_lo1_value_o = {{32{div_quotient[31]}}, div_quotient};
                        end
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_DIVU1: begin
                    if (
                        (instruction_i[31:26] == 6'h1c)
                        && (instruction_i[15:6] == 10'h000)
                        && (instruction_i[5:0] == 6'h1b)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        write_hi1_valid_o = 1'b1;
                        write_lo1_valid_o = 1'b1;
                        if (source_rt_scalar_i[31:0] == 32'd0) begin
                            write_hi1_value_o = {
                                {32{source_rs_scalar_i[31]}}, source_rs_scalar_i[31:0]
                            };
                            write_lo1_value_o = 64'hffff_ffff_ffff_ffff;
                        end else begin
                            write_hi1_value_o = {{32{divu_remainder[31]}}, divu_remainder};
                            write_lo1_value_o = {{32{divu_quotient[31]}}, divu_quotient};
                        end
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_MFHI1: begin
                    if (
                        (instruction_i[31:26] == 6'h1c)
                        && (instruction_i[25:16] == 10'h000)
                        && (instruction_i[10:6] == 5'h00)
                        && (instruction_i[5:0] == 6'h10)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {destination_upper_i, source_hi1_i};
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
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
                R5900_OPERATION_DSLLV: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[10:6] == 5'h00)
                        && (instruction_i[5:0] == 6'h14)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {destination_upper_i, dsllv_scalar};
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_DSRLV: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[10:6] == 5'h00)
                        && (instruction_i[5:0] == 6'h16)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {destination_upper_i, dsrlv_scalar};
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_DSRAV: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[10:6] == 5'h00)
                        && (instruction_i[5:0] == 6'h17)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {destination_upper_i, dsrav_scalar};
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_DSLL: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[25:21] == 5'h00)
                        && (instruction_i[5:0] == 6'h38)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {destination_upper_i, dsll_scalar};
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_DSRL: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[25:21] == 5'h00)
                        && (instruction_i[5:0] == 6'h3a)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {destination_upper_i, dsrl_scalar};
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_DSRA: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[25:21] == 5'h00)
                        && (instruction_i[5:0] == 6'h3b)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {destination_upper_i, dsra_scalar};
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_DSLL32: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[25:21] == 5'h00)
                        && (instruction_i[5:0] == 6'h3c)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {destination_upper_i, dsll32_scalar};
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_DSRL32: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[25:21] == 5'h00)
                        && (instruction_i[5:0] == 6'h3e)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {destination_upper_i, dsrl32_scalar};
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_DSRA32: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[25:21] == 5'h00)
                        && (instruction_i[5:0] == 6'h3f)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {destination_upper_i, dsra32_scalar};
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
                R5900_OPERATION_DADDIU: begin
                    if (instruction_i[31:26] == 6'h19) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[20:16];
                        writeback_value_o = {destination_upper_i, daddiu_scalar};
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_ADDU: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[10:6] == 5'h00)
                        && (instruction_i[5:0] == 6'h21)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {
                            destination_upper_i,
                            {32{addu_word[31]}},
                            addu_word
                        };
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_DADDU: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[10:6] == 5'h00)
                        && (instruction_i[5:0] == 6'h2d)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {destination_upper_i, daddu_scalar};
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_SUBU: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[10:6] == 5'h00)
                        && (instruction_i[5:0] == 6'h23)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {
                            destination_upper_i,
                            {32{subu_word[31]}},
                            subu_word
                        };
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_DSUBU: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[10:6] == 5'h00)
                        && (instruction_i[5:0] == 6'h2f)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {destination_upper_i, dsubu_scalar};
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_AND: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[10:6] == 5'h00)
                        && (instruction_i[5:0] == 6'h24)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {
                            destination_upper_i,
                            source_rs_scalar_i & source_rt_scalar_i
                        };
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_OR: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[10:6] == 5'h00)
                        && (instruction_i[5:0] == 6'h25)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {
                            destination_upper_i,
                            source_rs_scalar_i | source_rt_scalar_i
                        };
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_XOR: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[10:6] == 5'h00)
                        && (instruction_i[5:0] == 6'h26)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {
                            destination_upper_i,
                            source_rs_scalar_i ^ source_rt_scalar_i
                        };
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_NOR: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[10:6] == 5'h00)
                        && (instruction_i[5:0] == 6'h27)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {
                            destination_upper_i,
                            ~(source_rs_scalar_i | source_rt_scalar_i)
                        };
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_SLT: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[10:6] == 5'h00)
                        && (instruction_i[5:0] == 6'h2a)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {
                            destination_upper_i,
                            63'd0,
                            slt_result
                        };
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_SLTU: begin
                    if (
                        (instruction_i[31:26] == 6'h00)
                        && (instruction_i[10:6] == 5'h00)
                        && (instruction_i[5:0] == 6'h2b)
                    ) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[15:11];
                        writeback_value_o = {
                            destination_upper_i,
                            63'd0,
                            sltu_result
                        };
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_SLTI: begin
                    if (instruction_i[31:26] == 6'h0a) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[20:16];
                        writeback_value_o = {
                            destination_upper_i,
                            63'd0,
                            slti_result
                        };
                        retirement_o.valid = 1'b1;
                        retirement_o.pc = pc_i;
                        retirement_o.instruction = instruction_i;
                    end
                end
                R5900_OPERATION_SLTIU: begin
                    if (instruction_i[31:26] == 6'h0b) begin
                        complete_o = 1'b1;
                        pc_advance_o = 1'b1;
                        writeback_commit_o = 1'b1;
                        writeback_destination_o = instruction_i[20:16];
                        writeback_value_o = {
                            destination_upper_i,
                            63'd0,
                            sltiu_result
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
