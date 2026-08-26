// SPDX-License-Identifier: MIT

`default_nettype none

package r5900_types_pkg;

    timeunit 1ns;
    timeprecision 1ps;

    localparam int unsigned R5900_GPR_COUNT = 32;
    localparam int unsigned R5900_GPR_WIDTH = 128;
    localparam int unsigned R5900_GPR_INDEX_WIDTH = 5;
    localparam int unsigned R5900_PC_WIDTH = 32;
    localparam int unsigned R5900_INSTRUCTION_WIDTH = 32;
    localparam int unsigned R5900_HILO_WIDTH = 64;

    typedef logic [R5900_GPR_WIDTH-1:0] r5900_gpr_t;
    typedef logic [R5900_GPR_INDEX_WIDTH-1:0] r5900_gpr_index_t;
    typedef logic [R5900_PC_WIDTH-1:0] r5900_pc_t;
    typedef logic [R5900_INSTRUCTION_WIDTH-1:0] r5900_instruction_t;
    typedef logic [R5900_HILO_WIDTH-1:0] r5900_hilo_t;
    typedef logic [5:0] r5900_opcode_t;
    typedef logic [4:0] r5900_shift_amount_t;
    typedef logic [5:0] r5900_function_t;
    typedef logic [15:0] r5900_immediate_t;
    typedef logic [25:0] r5900_target_t;
    typedef logic [R5900_GPR_COUNT-1:0][R5900_GPR_WIDTH-1:0] r5900_gpr_file_t;

    typedef struct packed {
        r5900_hilo_t hi;
        r5900_hilo_t lo;
        r5900_hilo_t hi1;
        r5900_hilo_t lo1;
    } r5900_hilo_state_t;

    typedef enum logic [2:0] {
        R5900_FETCH_REQUEST  = 3'd0,
        R5900_FETCH_RESPONSE = 3'd1,
        R5900_DECODE         = 3'd2,
        R5900_EXECUTE        = 3'd3,
        R5900_WRITEBACK      = 3'd4
    } r5900_control_state_t;

    typedef enum logic [5:0] {
        R5900_OPERATION_NONE  = 6'd0,
        R5900_OPERATION_NOP   = 6'd1,
        R5900_OPERATION_SLL   = 6'd2,
        R5900_OPERATION_SRL   = 6'd3,
        R5900_OPERATION_SRA   = 6'd4,
        R5900_OPERATION_SLLV  = 6'd5,
        R5900_OPERATION_SRLV  = 6'd6,
        R5900_OPERATION_SRAV  = 6'd7,
        R5900_OPERATION_LUI   = 6'd8,
        R5900_OPERATION_ORI   = 6'd9,
        R5900_OPERATION_ANDI  = 6'd10,
        R5900_OPERATION_XORI  = 6'd11,
        R5900_OPERATION_ADDIU = 6'd12,
        R5900_OPERATION_ADDU  = 6'd13,
        R5900_OPERATION_SUBU  = 6'd14,
        R5900_OPERATION_AND   = 6'd15,
        R5900_OPERATION_OR    = 6'd16,
        R5900_OPERATION_XOR   = 6'd17,
        R5900_OPERATION_NOR   = 6'd18,
        R5900_OPERATION_SLT   = 6'd19,
        R5900_OPERATION_SLTU  = 6'd20,
        R5900_OPERATION_SLTI  = 6'd21,
        R5900_OPERATION_SLTIU = 6'd22,
        R5900_OPERATION_DSLL  = 6'd23,
        R5900_OPERATION_DSRL  = 6'd24,
        R5900_OPERATION_DSRA  = 6'd25,
        R5900_OPERATION_DSLL32 = 6'd26,
        R5900_OPERATION_DSRL32 = 6'd27,
        R5900_OPERATION_DSRA32 = 6'd28,
        R5900_OPERATION_DSLLV  = 6'd29,
        R5900_OPERATION_DSRLV  = 6'd30,
        R5900_OPERATION_DSRAV  = 6'd31,
        R5900_OPERATION_DADDIU = 6'd32,
        R5900_OPERATION_DADDU  = 6'd33,
        R5900_OPERATION_DSUBU  = 6'd34,
        R5900_OPERATION_MULT   = 6'd35,
        R5900_OPERATION_MULTU  = 6'd36,
        R5900_OPERATION_DIV    = 6'd37,
        R5900_OPERATION_DIVU   = 6'd38,
        R5900_OPERATION_MFHI   = 6'd39,
        R5900_OPERATION_MFLO   = 6'd40,
        R5900_OPERATION_MTHI   = 6'd41,
        R5900_OPERATION_MTLO   = 6'd42,
        R5900_OPERATION_MULT1  = 6'd43,
        R5900_OPERATION_MULTU1 = 6'd44,
        R5900_OPERATION_DIV1   = 6'd45
    } r5900_operation_t;

    typedef struct packed {
        r5900_gpr_file_t   gprs;
        r5900_pc_t         pc;
        r5900_hilo_state_t hilo;
    } r5900_arch_state_t;

    typedef struct packed {
        logic              valid;
        r5900_gpr_index_t destination;
        r5900_gpr_t       value;
    } r5900_writeback_t;

    typedef struct packed {
        logic                valid;
        r5900_pc_t           pc;
        r5900_instruction_t instruction;
    } r5900_reserved_instruction_t;

    typedef struct packed {
        logic                valid;
        r5900_pc_t           pc;
        r5900_instruction_t instruction;
    } r5900_retirement_t;

endpackage

`default_nettype wire
