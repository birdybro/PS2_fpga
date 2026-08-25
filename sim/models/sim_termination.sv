// SPDX-License-Identifier: MIT

`default_nettype none

module sim_termination #(
    parameter bit FINISH_ON_PASS = 1'b1
) (
    input  logic clk_i,
    input  logic rst_ni,
    input  logic pass_i,
    output logic pass_event_o,
    output logic pass_latched_o
);

    timeunit 1ns;
    timeprecision 1ps;

    always_ff @(posedge clk_i) begin
        if (!rst_ni) begin
            pass_event_o   <= 1'b0;
            pass_latched_o <= 1'b0;
        end else begin
            pass_event_o <= 1'b0;
            if (pass_i && !pass_latched_o) begin
                pass_event_o   <= 1'b1;
                pass_latched_o <= 1'b1;
                if (FINISH_ON_PASS) begin
                    $display("SIM_PASS: completion requested");
                    $finish;
                end
            end
        end
    end

endmodule

`default_nettype wire
