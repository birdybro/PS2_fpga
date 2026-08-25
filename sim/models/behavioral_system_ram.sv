// SPDX-License-Identifier: MIT

`default_nettype none

module behavioral_system_ram #(
    parameter int unsigned ADDR_WIDTH = 32,
    parameter int unsigned SIZE_BYTES = 1024,
    parameter int unsigned INDEX_WIDTH = $clog2(SIZE_BYTES)
) (
    input  logic                  clk_i,
    input  logic                  rst_ni,
    input  logic                  backdoor_write_i,
    input  logic [ADDR_WIDTH-1:0] backdoor_addr_i,
    input  logic [7:0]            backdoor_wdata_i,
    output logic [7:0]            backdoor_rdata_o,
    output logic                  backdoor_in_bounds_o
);

    timeunit 1ns;
    timeprecision 1ps;

    logic [7:0] storage [0:SIZE_BYTES-1];

    initial begin
        if (SIZE_BYTES < 2) begin
            $fatal(1, "behavioral_system_ram SIZE_BYTES must be at least two");
        end
        if (INDEX_WIDTH >= ADDR_WIDTH) begin
            $fatal(1, "behavioral_system_ram ADDR_WIDTH must represent an out-of-bounds address");
        end
    end

    always_comb begin
        backdoor_in_bounds_o = backdoor_addr_i < SIZE_BYTES;
        backdoor_rdata_o = 8'h00;
        if (backdoor_in_bounds_o) begin
            backdoor_rdata_o = storage[backdoor_addr_i[INDEX_WIDTH-1:0]];
        end
    end

    always_ff @(posedge clk_i) begin
        if (rst_ni && backdoor_write_i && backdoor_in_bounds_o) begin
            storage[backdoor_addr_i[INDEX_WIDTH-1:0]] <= backdoor_wdata_i;
        end
    end

endmodule

`default_nettype wire
