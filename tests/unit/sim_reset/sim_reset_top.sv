// SPDX-License-Identifier: MIT

`default_nettype none

module sim_reset_top (
    output logic clk_o,
    output logic rst_no
);

    timeunit 1ns;
    timeprecision 1ps;

    sim_clock #(
        .PERIOD(10ns)
    ) u_clock (
        .clk_o
    );

    sim_reset #(
        .ASSERT_CYCLES(4)
    ) u_reset (
        .clk_i(clk_o),
        .rst_ni(rst_no)
    );

endmodule

`default_nettype wire
