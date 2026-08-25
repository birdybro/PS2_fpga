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

    typedef logic [R5900_GPR_WIDTH-1:0] r5900_gpr_t;
    typedef logic [R5900_GPR_INDEX_WIDTH-1:0] r5900_gpr_index_t;
    typedef logic [R5900_PC_WIDTH-1:0] r5900_pc_t;
    typedef logic [R5900_INSTRUCTION_WIDTH-1:0] r5900_instruction_t;
    typedef logic [R5900_GPR_COUNT-1:0][R5900_GPR_WIDTH-1:0] r5900_gpr_file_t;

    typedef struct packed {
        r5900_gpr_file_t gprs;
        r5900_pc_t       pc;
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

endpackage

`default_nettype wire
