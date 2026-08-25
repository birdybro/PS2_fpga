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
    logic read64_request;
    logic read128_request;
    logic write32_request;
    logic write64_request;
    logic supported_request;
    logic response_slot_available;
    logic request_fire;

    localparam int unsigned STROBE_WIDTH = DATA_WIDTH / 8;
    localparam logic [ADDR_WIDTH-1:0] LAST_READ32_ADDR = SIZE_BYTES - 4;
    localparam logic [ADDR_WIDTH-1:0] LAST_READ64_ADDR = SIZE_BYTES - 8;
    localparam logic [ADDR_WIDTH-1:0] LAST_READ128_ADDR = SIZE_BYTES - 16;
    localparam logic [INDEX_WIDTH-1:0] BYTE_OFFSET_1 = INDEX_WIDTH'(1);
    localparam logic [INDEX_WIDTH-1:0] BYTE_OFFSET_2 = INDEX_WIDTH'(2);
    localparam logic [INDEX_WIDTH-1:0] BYTE_OFFSET_3 = INDEX_WIDTH'(3);
    localparam logic [INDEX_WIDTH-1:0] BYTE_OFFSET_4 = INDEX_WIDTH'(4);
    localparam logic [INDEX_WIDTH-1:0] BYTE_OFFSET_5 = INDEX_WIDTH'(5);
    localparam logic [INDEX_WIDTH-1:0] BYTE_OFFSET_6 = INDEX_WIDTH'(6);
    localparam logic [INDEX_WIDTH-1:0] BYTE_OFFSET_7 = INDEX_WIDTH'(7);
    localparam logic [INDEX_WIDTH-1:0] BYTE_OFFSET_8 = INDEX_WIDTH'(8);
    localparam logic [INDEX_WIDTH-1:0] BYTE_OFFSET_9 = INDEX_WIDTH'(9);
    localparam logic [INDEX_WIDTH-1:0] BYTE_OFFSET_10 = INDEX_WIDTH'(10);
    localparam logic [INDEX_WIDTH-1:0] BYTE_OFFSET_11 = INDEX_WIDTH'(11);
    localparam logic [INDEX_WIDTH-1:0] BYTE_OFFSET_12 = INDEX_WIDTH'(12);
    localparam logic [INDEX_WIDTH-1:0] BYTE_OFFSET_13 = INDEX_WIDTH'(13);
    localparam logic [INDEX_WIDTH-1:0] BYTE_OFFSET_14 = INDEX_WIDTH'(14);
    localparam logic [INDEX_WIDTH-1:0] BYTE_OFFSET_15 = INDEX_WIDTH'(15);
    localparam logic [STROBE_WIDTH-1:0] WRITE32_LANE_MASK = {
        {(STROBE_WIDTH - 4) {1'b0}},
        4'b1111
    };
    localparam logic [STROBE_WIDTH-1:0] WRITE64_LANE_MASK = {
        {(STROBE_WIDTH - 8) {1'b0}},
        8'hff
    };

    initial begin
        if (SIZE_BYTES < 16) begin
            $fatal(1, "behavioral_system_ram SIZE_BYTES must be at least sixteen");
        end
        if (INDEX_WIDTH >= ADDR_WIDTH) begin
            $fatal(1, "behavioral_system_ram ADDR_WIDTH must represent an out-of-bounds address");
        end
        if (DATA_WIDTH < 128) begin
            $fatal(1, "behavioral_system_ram DATA_WIDTH must be at least 128");
        end
    end

    assign read32_request = !bus.req_write
        && (bus.req_size == 3'd2)
        && (bus.req_addr[1:0] == 2'b00)
        && (bus.req_addr <= LAST_READ32_ADDR);
    assign read64_request = !bus.req_write
        && (bus.req_size == 3'd3)
        && (bus.req_addr[2:0] == 3'b000)
        && (bus.req_addr <= LAST_READ64_ADDR);
    assign read128_request = !bus.req_write
        && (bus.req_size == 3'd4)
        && (bus.req_addr[3:0] == 4'b0000)
        && (bus.req_addr <= LAST_READ128_ADDR);
    assign write32_request = bus.req_write
        && (bus.req_size == 3'd2)
        && (bus.req_addr[1:0] == 2'b00)
        && (bus.req_addr <= LAST_READ32_ADDR)
        && ((bus.req_wstrb & ~WRITE32_LANE_MASK) == '0);
    assign write64_request = bus.req_write
        && (bus.req_size == 3'd3)
        && (bus.req_addr[2:0] == 3'b000)
        && (bus.req_addr <= LAST_READ64_ADDR)
        && ((bus.req_wstrb & ~WRITE64_LANE_MASK) == '0);
    assign supported_request = read32_request
        || read64_request
        || read128_request
        || write32_request
        || write64_request;
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
                    if (write64_request) begin
                        if (bus.req_wstrb[4]) begin
                            storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_4]
                                <= bus.req_wdata[39:32];
                        end
                        if (bus.req_wstrb[5]) begin
                            storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_5]
                                <= bus.req_wdata[47:40];
                        end
                        if (bus.req_wstrb[6]) begin
                            storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_6]
                                <= bus.req_wdata[55:48];
                        end
                        if (bus.req_wstrb[7]) begin
                            storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_7]
                                <= bus.req_wdata[63:56];
                        end
                    end
                    rsp_rdata_q <= '0;
                end else begin
                    if (read128_request) begin
                        rsp_rdata_q <= {
                            {(DATA_WIDTH - 128) {1'b0}},
                            storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_15],
                            storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_14],
                            storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_13],
                            storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_12],
                            storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_11],
                            storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_10],
                            storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_9],
                            storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_8],
                            storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_7],
                            storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_6],
                            storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_5],
                            storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_4],
                            storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_3],
                            storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_2],
                            storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_1],
                            storage[bus.req_addr[INDEX_WIDTH-1:0]]
                        };
                    end else if (read64_request) begin
                        rsp_rdata_q <= {
                            {(DATA_WIDTH - 64) {1'b0}},
                            storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_7],
                            storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_6],
                            storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_5],
                            storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_4],
                            storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_3],
                            storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_2],
                            storage[bus.req_addr[INDEX_WIDTH-1:0] + BYTE_OFFSET_1],
                            storage[bus.req_addr[INDEX_WIDTH-1:0]]
                        };
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
    end

endmodule

`default_nettype wire
