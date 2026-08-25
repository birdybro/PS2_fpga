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

    typedef enum logic [4:0] {
        R5900_OPERATION_NONE  = 5'd0,
        R5900_OPERATION_NOP   = 5'd1,
        R5900_OPERATION_SLL   = 5'd2,
        R5900_OPERATION_SRL   = 5'd3,
        R5900_OPERATION_SRA   = 5'd4,
        R5900_OPERATION_SLLV  = 5'd5,
        R5900_OPERATION_SRLV  = 5'd6,
        R5900_OPERATION_SRAV  = 5'd7,
        R5900_OPERATION_LUI   = 5'd8,
        R5900_OPERATION_ORI   = 5'd9,
        R5900_OPERATION_ANDI  = 5'd10,
        R5900_OPERATION_XORI  = 5'd11,
        R5900_OPERATION_ADDIU = 5'd12,
        R5900_OPERATION_ADDU  = 5'd13,
        R5900_OPERATION_SUBU  = 5'd14,
        R5900_OPERATION_AND   = 5'd15,
        R5900_OPERATION_OR    = 5'd16,
        R5900_OPERATION_XOR   = 5'd17,
        R5900_OPERATION_NOR   = 5'd18,
        R5900_OPERATION_SLT   = 5'd19,
        R5900_OPERATION_SLTU  = 5'd20,
        R5900_OPERATION_SLTI  = 5'd21,
        R5900_OPERATION_SLTIU = 5'd22
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
