// SPDX-License-Identifier: MIT

`default_nettype none

module sim_fail_fatal_top;

    timeunit 1ns;
    timeprecision 1ps;

    localparam logic [31:0] EXPECTED_FAIL_CODE = 32'hdead_beef;

    logic clk;
    logic rst_n;
    logic pass;
    logic fail;
    logic [31:0] fail_code;
    logic pass_event;
    logic pass_latched;
    logic fail_event;
    logic fail_latched;
    logic [31:0] latched_fail_code;

    sim_termination u_termination (
        .clk_i(clk),
        .rst_ni(rst_n),
        .pass_i(pass),
        .fail_i(fail),
        .fail_code_i(fail_code),
        .pass_event_o(pass_event),
        .pass_latched_o(pass_latched),
        .fail_event_o(fail_event),
        .fail_latched_o(fail_latched),
        .fail_code_o(latched_fail_code)
    );

    initial begin
        clk       = 1'b0;
        rst_n     = 1'b0;
        pass      = 1'b0;
        fail      = 1'b0;
        fail_code = 32'd0;
        forever begin
            #5ns clk = ~clk;
        end
    end

    initial begin
        @(posedge clk);
        #1ns rst_n = 1'b1;
        @(posedge clk);
        #1ns;
        pass      = 1'b1;
        fail      = 1'b1;
        fail_code = EXPECTED_FAIL_CODE;
        @(posedge clk);
        #1ns;
        if (
            pass_event || pass_latched || !fail_event || !fail_latched
            || (latched_fail_code != EXPECTED_FAIL_CODE)
        ) begin
            $fatal(1, "SIM_FAIL priority state was not visible at termination");
        end
        $fatal(1, "SIM_FAIL did not terminate simulation");
    end

    initial begin
        #100ns;
        $fatal(1, "SIM_FAIL standalone test timed out");
    end

endmodule

`default_nettype wire
