// SPDX-License-Identifier: MIT

`default_nettype none

module r5900_control_state_checker (
    input logic                                      clk_i,
    input logic                                      rst_ni,
    input r5900_types_pkg::r5900_control_state_t    state_i
);

    timeunit 1ns;
    timeprecision 1ps;

    import r5900_types_pkg::*;

    property p_control_state_is_legal;
        @(posedge clk_i) disable iff (!rst_ni)
            (state_i == R5900_FETCH_REQUEST)
            || (state_i == R5900_FETCH_RESPONSE)
            || (state_i == R5900_DECODE)
            || (state_i == R5900_EXECUTE)
            || (state_i == R5900_WRITEBACK);
    endproperty

    assert property (p_control_state_is_legal)
        else $fatal(1, "R5900_CONTROL_STATE: illegal state");

endmodule

`default_nettype wire
