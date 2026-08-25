// SPDX-License-Identifier: MIT

`default_nettype none

module sim_waveform_control_top #(
    parameter bit WAVE_ENABLE = 1'b0
);

    timeunit 1ns;
    timeprecision 1ps;

    logic probe_q;

    sim_waveform_control #(
        .WAVE_ENABLE(WAVE_ENABLE)
    ) u_waveform_control ();

    initial begin
        probe_q = 1'b0;
        forever begin
            #5ns probe_q = ~probe_q;
        end
    end

    initial begin
        #31ns;
        if (probe_q != 1'b0) begin
            $fatal(1, "waveform probe did not toggle as expected");
        end
        $finish;
    end

endmodule

`default_nettype wire
