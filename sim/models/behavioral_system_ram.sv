// SPDX-License-Identifier: MIT

`default_nettype none

module behavioral_system_ram #(
    parameter int unsigned ADDR_WIDTH = 32,
    parameter int unsigned DATA_WIDTH = 128,
    parameter int unsigned SIZE_BYTES = 1024,
    parameter int unsigned INDEX_WIDTH = $clog2(SIZE_BYTES)
) (
    input  logic                  clk_i,
    input  logic                  rst_ni,
    input  logic                  backdoor_write_i,
    input  logic [ADDR_WIDTH-1:0] backdoor_addr_i,
    input  logic [7:0]            backdoor_wdata_i,
    output logic [7:0]            backdoor_rdata_o,
    output logic                  backdoor_in_bounds_o,
    memory_bus_if.target bus
);

    timeunit 1ns;
    timeprecision 1ps;

    logic [7:0] storage [0:SIZE_BYTES-1];
    logic                  rsp_valid_q;
    logic [DATA_WIDTH-1:0] rsp_rdata_q;
    logic                  rsp_error_q;

    logic read32_request;
    logic write32_request;
    logic supported_request;
    logic response_slot_available;
    logic request_fire;

    localparam int unsigned STROBE_WIDTH = DATA_WIDTH / 8;
    localparam logic [ADDR_WIDTH-1:0] LAST_READ32_ADDR = SIZE_BYTES - 4;
    localparam logic [INDEX_WIDTH-1:0] BYTE_OFFSET_1 = INDEX_WIDTH'(1);
    localparam logic [INDEX_WIDTH-1:0] BYTE_OFFSET_2 = INDEX_WIDTH'(2);
    localparam logic [INDEX_WIDTH-1:0] BYTE_OFFSET_3 = INDEX_WIDTH'(3);
    localparam logic [STROBE_WIDTH-1:0] WRITE32_LANE_MASK = {
        {(STROBE_WIDTH - 4) {1'b0}},
        4'b1111
    };

    initial begin
        if (SIZE_BYTES < 4) begin
            $fatal(1, "behavioral_system_ram SIZE_BYTES must be at least four");
        end
        if (INDEX_WIDTH >= ADDR_WIDTH) begin
            $fatal(1, "behavioral_system_ram ADDR_WIDTH must represent an out-of-bounds address");
        end
        if (DATA_WIDTH < 32) begin
            $fatal(1, "behavioral_system_ram DATA_WIDTH must be at least 32");
        end
    end

    assign read32_request = !bus.req_write
        && (bus.req_size == 3'd2)
        && (bus.req_addr[1:0] == 2'b00)
        && (bus.req_addr <= LAST_READ32_ADDR);
    assign write32_request = bus.req_write
        && (bus.req_size == 3'd2)
        && (bus.req_addr[1:0] == 2'b00)
        && (bus.req_addr <= LAST_READ32_ADDR)
        && ((bus.req_wstrb & ~WRITE32_LANE_MASK) == '0);
    assign supported_request = read32_request || write32_request;
    assign response_slot_available = !rsp_valid_q || bus.rsp_ready;
    assign bus.req_ready = rst_ni && response_slot_available && supported_request;
    assign request_fire = bus.req_valid && bus.req_ready;

    assign bus.rsp_valid = rsp_valid_q;
    assign bus.rsp_rdata = rsp_rdata_q;
    assign bus.rsp_error = rsp_error_q;

    always_comb begin
        backdoor_in_bounds_o = backdoor_addr_i < SIZE_BYTES;
        backdoor_rdata_o = 8'h00;
        if (backdoor_in_bounds_o) begin
            backdoor_rdata_o = storage[backdoor_addr_i[INDEX_WIDTH-1:0]];
        end
    end

    always_ff @(posedge clk_i) begin
        if (!rst_ni) begin
            rsp_valid_q <= 1'b0;
            rsp_rdata_q <= '0;
            rsp_error_q <= 1'b0;
        end else begin
            if (bus.req_valid && bus.req_write) begin
                assert (!$isunknown(bus.req_wdata))
                else $fatal(1, "RAM_WRITE_DATA_UNKNOWN: write data must be known while valid");
                assert (!$isunknown(bus.req_wstrb))
                else $fatal(1, "RAM_WRITE_STROBE_UNKNOWN: write strobes must be known while valid");
            end
            assert (!(backdoor_write_i && request_fire && bus.req_write))
            else $fatal(1, "RAM_WRITE_CONFLICT: backdoor and bus writes must not coincide");

            if (backdoor_write_i && backdoor_in_bounds_o) begin
                storage[backdoor_addr_i[INDEX_WIDTH-1:0]] <= backdoor_wdata_i;
            end

            if (rsp_valid_q && bus.rsp_ready) begin
                rsp_valid_q <= 1'b0;
            end

            if (request_fire) begin
                rsp_valid_q <= 1'b1;
                rsp_error_q <= 1'b0;
                if (bus.req_write) begin
                    if (bus.req_wstrb[0]) begin
                        storage[bus.req_addr[INDEX_WIDTH-1:0]] <= bus.req_wdata[7:0];
                    end
                    if (bus.req_wstrb[1]) begin
                        storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_1]
                            <= bus.req_wdata[15:8];
                    end
                    if (bus.req_wstrb[2]) begin
                        storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_2]
                            <= bus.req_wdata[23:16];
                    end
                    if (bus.req_wstrb[3]) begin
                        storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_3]
                            <= bus.req_wdata[31:24];
                    end
                    rsp_rdata_q <= '0;
                end else begin
                    rsp_rdata_q <= {
                        {(DATA_WIDTH - 32) {1'b0}},
                        storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_3],
                        storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_2],
                        storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_1],
                        storage[bus.req_addr[INDEX_WIDTH-1:0]]
                    };
                end
            end
        end
    end

endmodule

`default_nettype wire
