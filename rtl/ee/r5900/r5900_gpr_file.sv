// SPDX-License-Identifier: MIT

`default_nettype none

module r5900_gpr_file (
    input  logic                                  clk_i,
    input  r5900_types_pkg::r5900_gpr_index_t    read_index_a_i,
    output r5900_types_pkg::r5900_gpr_t          read_value_a_o,
    input  r5900_types_pkg::r5900_gpr_index_t    read_index_b_i,
    output r5900_types_pkg::r5900_gpr_t          read_value_b_o,
    input  logic                                  write_valid_i,
    input  r5900_types_pkg::r5900_gpr_index_t    write_index_i,
    input  r5900_types_pkg::r5900_gpr_t          write_value_i,
    output r5900_types_pkg::r5900_gpr_file_t     state_o
);

    timeunit 1ns;
    timeprecision 1ps;

    import r5900_types_pkg::*;

    r5900_gpr_t      physical_read_a;
    r5900_gpr_t      physical_read_b;
    r5900_gpr_file_t physical_state;
    logic            physical_write_valid;

    assign physical_write_valid = write_valid_i && (write_index_i != '0);
    assign read_value_a_o = (read_index_a_i == '0) ? '0 : physical_read_a;
    assign read_value_b_o = (read_index_b_i == '0) ? '0 : physical_read_b;

    always_comb begin
        state_o = physical_state;
        state_o[0] = '0;
    end

    r5900_gpr_storage u_storage (
        .clk_i,
        .read_index_a_i,
        .read_value_a_o(physical_read_a),
        .read_index_b_i,
        .read_value_b_o(physical_read_b),
        .write_valid_i(physical_write_valid),
        .write_index_i,
        .write_value_i,
        .state_o(physical_state)
    );

    property p_register_zero_is_immutable;
        @(posedge clk_i) state_o[0] == 128'd0;
    endproperty

    assert property (p_register_zero_is_immutable)
        else $fatal(1, "R5900_GPR_ZERO: register zero changed");

endmodule

`default_nettype wire
