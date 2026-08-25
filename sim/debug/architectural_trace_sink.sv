// SPDX-License-Identifier: MIT

`default_nettype none

module architectural_trace_sink #(
    parameter bit TRACE_ENABLE = 1'b0
) (
    input logic         clk_i,
    input logic         rst_ni,
    input logic         event_valid_i,
    input logic [7:0]   event_source_i,
    input logic [7:0]   event_kind_i,
    input logic [31:0]  event_pc_i,
    input logic [31:0]  event_instruction_i,
    input logic [15:0]  event_identifier_i,
    input logic [127:0] event_value_i
);

    timeunit 1ns;
    timeprecision 1ps;

    integer trace_fd;
    string trace_path;
    logic [31:0] cycle_count_q;
    logic [63:0] sequence_q;

    initial begin
        trace_fd = 0;
        if (TRACE_ENABLE) begin
            if (!$value$plusargs("ARCH_TRACE_FILE=%s", trace_path)) begin
                trace_path = "architectural_trace.log";
            end
            trace_fd = $fopen(trace_path, "w");
            if (trace_fd == 0) begin
                $fatal(1, "ARCH_TRACE_OPEN: cannot open %s", trace_path);
            end
            $fdisplay(trace_fd, "# PS2_fpga architectural event trace v1");
        end
    end

    always_ff @(posedge clk_i) begin
        if (!rst_ni) begin
            cycle_count_q <= 32'd0;
            sequence_q <= 64'd0;
        end else begin
            cycle_count_q <= cycle_count_q + 32'd1;
            if (TRACE_ENABLE && event_valid_i) begin
                $fdisplay(
                    trace_fd,
                    "cycle=%08d sequence=%016x source=0x%02x kind=0x%02x pc=0x%08x instruction=0x%08x identifier=0x%04x value=0x%032x",
                    cycle_count_q + 32'd1,
                    sequence_q,
                    event_source_i,
                    event_kind_i,
                    event_pc_i,
                    event_instruction_i,
                    event_identifier_i,
                    event_value_i
                );
                sequence_q <= sequence_q + 64'd1;
            end
        end
    end

    final begin
        if (trace_fd != 0) begin
            $fclose(trace_fd);
        end
    end

endmodule

`default_nettype wire
