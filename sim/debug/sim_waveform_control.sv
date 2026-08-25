// SPDX-License-Identifier: MIT

`default_nettype none

module sim_waveform_control #(
    parameter bit WAVE_ENABLE = 1'b0
);

    timeunit 1ns;
    timeprecision 1ps;

    string wave_path;

    initial begin
        if (WAVE_ENABLE) begin
            if (!$value$plusargs("WAVE_FILE=%s", wave_path)) begin
                wave_path = "waves.vcd";
            end
            $dumpfile(wave_path);
            $dumpvars(0);
        end
    end

endmodule

`default_nettype wire
