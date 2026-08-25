// SPDX-License-Identifier: MIT

`default_nettype none

module sim_clock #(
    parameter time PERIOD = 10ns
) (
    output logic clk_o
);

    timeunit 1ns;
    timeprecision 1ps;

    localparam time HALF_PERIOD = PERIOD / 2;

    initial begin
        if ((PERIOD <= 0ns) || ((2 * HALF_PERIOD) != PERIOD)) begin
            $fatal(1, "sim_clock PERIOD must be positive and divisible by two timeprecision units");
        end

        clk_o = 1'b0;
        forever begin
            #(HALF_PERIOD) clk_o = ~clk_o;
        end
    end

endmodule

`default_nettype wire
