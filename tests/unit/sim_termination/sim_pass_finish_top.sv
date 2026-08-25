// SPDX-License-Identifier: MIT

`default_nettype none

module sim_pass_finish_top;

    timeunit 1ns;
    timeprecision 1ps;

    logic clk;
    logic rst_n;
    logic pass;
    logic pass_event;
    logic pass_latched;

    sim_termination u_termination (
        .clk_i(clk),
        .rst_ni(rst_n),
        .pass_i(pass),
        .pass_event_o(pass_event),
        .pass_latched_o(pass_latched)
    );

    initial begin
        clk   = 1'b0;
        rst_n = 1'b0;
        pass  = 1'b0;
        forever begin
            #5ns clk = ~clk;
        end
    end

    initial begin
        @(posedge clk);
        #1ns rst_n = 1'b1;
        @(posedge clk);
        #1ns pass = 1'b1;
        @(posedge clk);
        #1ns;
        if (!pass_event || !pass_latched) begin
            $fatal(1, "SIM_PASS state was not visible at completion");
        end
        $fatal(1, "SIM_PASS did not terminate simulation");
    end

    initial begin
        #100ns;
        $fatal(1, "SIM_PASS standalone test timed out");
    end

endmodule

`default_nettype wire
