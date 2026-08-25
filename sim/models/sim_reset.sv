// SPDX-License-Identifier: MIT

`default_nettype none

module sim_reset #(
    parameter int unsigned ASSERT_CYCLES = 4
) (
    input  logic clk_i,
    output logic rst_ni
);

    timeunit 1ns;
    timeprecision 1ps;

    initial begin
        if (ASSERT_CYCLES == 32'd0) begin
            $fatal(1, "sim_reset ASSERT_CYCLES must be positive");
        end

        rst_ni = 1'b0;
        repeat (ASSERT_CYCLES) begin
            @(posedge clk_i);
        end
        @(negedge clk_i);
        rst_ni = 1'b1;
    end

endmodule

`default_nettype wire
