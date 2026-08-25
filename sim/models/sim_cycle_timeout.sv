// SPDX-License-Identifier: MIT

`default_nettype none

module sim_cycle_timeout #(
    parameter int unsigned MAX_CYCLES = 32'd0,
    parameter bit FATAL_ON_TIMEOUT = 1'b1
) (
    input  logic        clk_i,
    input  logic        rst_ni,
    output logic        timeout_o,
    output logic [31:0] cycle_count_o
);

    timeunit 1ns;
    timeprecision 1ps;

    always_ff @(posedge clk_i) begin
        if (!rst_ni || (MAX_CYCLES == 32'd0)) begin
            timeout_o     <= 1'b0;
            cycle_count_o <= 32'd0;
        end else if (!timeout_o) begin
            cycle_count_o <= cycle_count_o + 32'd1;
            if (cycle_count_o == (MAX_CYCLES - 32'd1)) begin
                timeout_o <= 1'b1;
                if (FATAL_ON_TIMEOUT) begin
                    $fatal(1, "SIM_TIMEOUT: reached %0d active cycles", MAX_CYCLES);
                end
            end
        end
    end

endmodule

`default_nettype wire
