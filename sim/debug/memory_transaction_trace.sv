// SPDX-License-Identifier: MIT

`default_nettype none

module memory_transaction_trace #(
    parameter bit TRACE_ENABLE = 1'b0
) (
    input logic clk_i,
    input logic rst_ni,
    memory_bus_if.monitor bus
);

    timeunit 1ns;
    timeprecision 1ps;

    integer trace_fd;
    string trace_path;
    logic [31:0] cycle_count_q;

    initial begin
        trace_fd = 0;
        if (TRACE_ENABLE) begin
            if (!$value$plusargs("MEM_TRACE_FILE=%s", trace_path)) begin
                trace_path = "memory_transactions.log";
            end
            trace_fd = $fopen(trace_path, "w");
            if (trace_fd == 0) begin
                $fatal(1, "MEM_TRACE_OPEN: cannot open %s", trace_path);
            end
            $fdisplay(trace_fd, "# PS2_fpga memory transaction trace v1");
        end
    end

    always_ff @(posedge clk_i) begin
        if (!rst_ni) begin
            cycle_count_q <= 32'd0;
        end else begin
            cycle_count_q <= cycle_count_q + 32'd1;
            if (TRACE_ENABLE && bus.req_valid && bus.req_ready) begin
                $fdisplay(
                    trace_fd,
                    "cycle=%08d kind=REQ write=%0d addr=0x%08x size=%0d wdata=0x%032x wstrb=0x%04x",
                    cycle_count_q + 32'd1,
                    bus.req_write,
                    bus.req_addr,
                    bus.req_size,
                    bus.req_wdata,
                    bus.req_wstrb
                );
            end
            if (TRACE_ENABLE && bus.rsp_valid && bus.rsp_ready) begin
                $fdisplay(
                    trace_fd,
                    "cycle=%08d kind=RSP rdata=0x%032x error=%0d",
                    cycle_count_q + 32'd1,
                    bus.rsp_rdata,
                    bus.rsp_error
                );
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
