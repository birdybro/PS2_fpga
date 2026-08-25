// SPDX-License-Identifier: MIT

`default_nettype none

module sim_termination #(
    parameter bit FINISH_ON_PASS = 1'b1,
    parameter bit FATAL_ON_FAIL = 1'b1
) (
    input  logic        clk_i,
    input  logic        rst_ni,
    input  logic        pass_i,
    input  logic        fail_i,
    input  logic [31:0] fail_code_i,
    output logic        pass_event_o,
    output logic        pass_latched_o,
    output logic        fail_event_o,
    output logic        fail_latched_o,
    output logic [31:0] fail_code_o
);

    timeunit 1ns;
    timeprecision 1ps;

    always_ff @(posedge clk_i) begin
        if (!rst_ni) begin
            pass_event_o   <= 1'b0;
            pass_latched_o <= 1'b0;
            fail_event_o   <= 1'b0;
            fail_latched_o <= 1'b0;
            fail_code_o    <= 32'd0;
        end else begin
            pass_event_o <= 1'b0;
            fail_event_o <= 1'b0;
            if (fail_i && !pass_latched_o && !fail_latched_o) begin
                fail_event_o   <= 1'b1;
                fail_latched_o <= 1'b1;
                fail_code_o    <= fail_code_i;
                if (FATAL_ON_FAIL) begin
                    $fatal(1, "SIM_FAIL: code=0x%08x", fail_code_i);
                end
            end else if (pass_i && !pass_latched_o && !fail_latched_o) begin
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
