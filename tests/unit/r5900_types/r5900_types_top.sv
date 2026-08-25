// SPDX-License-Identifier: MIT

`default_nettype none

module r5900_types_top (
    input  logic [31:0]   pc_i,
    input  logic [4095:0] gprs_i,
    input  logic [31:0]   instruction_i,
    input  logic          writeback_valid_i,
    input  logic [4:0]    writeback_destination_i,
    input  logic [127:0]  writeback_value_i,
    input  logic          reserved_valid_i,
    input  logic [31:0]   reserved_pc_i,
    input  logic [31:0]   reserved_instruction_i,
    output logic [31:0]   pc_o,
    output logic [4095:0] gprs_o,
    output logic [127:0]  gpr_zero_o,
    output logic [127:0]  gpr_last_o,
    output logic [31:0]   instruction_o,
    output logic          writeback_valid_o,
    output logic [4:0]    writeback_destination_o,
    output logic [127:0]  writeback_value_o,
    output logic          reserved_valid_o,
    output logic [31:0]   reserved_pc_o,
    output logic [31:0]   reserved_instruction_o
);

    timeunit 1ns;
    timeprecision 1ps;

    import r5900_types_pkg::*;

    r5900_debug_if debug ();

    r5900_debug_driver u_driver (
        .pc_i,
        .gprs_i,
        .instruction_i,
        .writeback_valid_i,
        .writeback_destination_i,
        .writeback_value_i,
        .reserved_valid_i,
        .reserved_pc_i,
        .reserved_instruction_i,
        .debug_o(debug)
    );

    r5900_debug_probe u_probe (
        .debug_i(debug),
        .pc_o,
        .gprs_o,
        .gpr_zero_o,
        .gpr_last_o,
        .instruction_o,
        .writeback_valid_o,
        .writeback_destination_o,
        .writeback_value_o,
        .reserved_valid_o,
        .reserved_pc_o,
        .reserved_instruction_o
    );

    initial begin
        if ($bits(r5900_gpr_t) != 128) begin
            $fatal(1, "R5900_TYPE_GPR_WIDTH");
        end
        if ($bits(r5900_gpr_file_t) != 4096) begin
            $fatal(1, "R5900_TYPE_GPR_FILE_WIDTH");
        end
        if ($bits(r5900_arch_state_t) != 4128) begin
            $fatal(1, "R5900_TYPE_ARCH_STATE_WIDTH");
        end
        if ($bits(r5900_writeback_t) != 134) begin
            $fatal(1, "R5900_TYPE_WRITEBACK_WIDTH");
        end
        if ($bits(r5900_reserved_instruction_t) != 65) begin
            $fatal(1, "R5900_TYPE_RESERVED_WIDTH");
        end
    end

endmodule

`default_nettype wire
