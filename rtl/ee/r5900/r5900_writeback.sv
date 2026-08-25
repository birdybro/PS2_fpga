// SPDX-License-Identifier: MIT

`default_nettype none

module r5900_writeback (
    input logic                                     clk_i,
    input logic                                     rst_ni,
    input logic                                     commit_i,
    input r5900_types_pkg::r5900_gpr_index_t       destination_i,
    input r5900_types_pkg::r5900_gpr_t             value_i,
    output logic                                    commit_accepted_o,
    output logic                                    gpr_write_enable_o,
    output r5900_types_pkg::r5900_gpr_index_t      gpr_write_index_o,
    output r5900_types_pkg::r5900_gpr_t            gpr_write_data_o,
    output r5900_types_pkg::r5900_writeback_t      writeback_o
);

    timeunit 1ns;
    timeprecision 1ps;

    import r5900_types_pkg::*;

    logic commit_seen_q;

    assign commit_accepted_o = rst_ni && commit_i && !commit_seen_q;

    always_comb begin
        writeback_o = '0;
        if (commit_accepted_o && (destination_i != R5900_GPR_INDEX_WIDTH'(0))) begin
            writeback_o.valid = 1'b1;
            writeback_o.destination = destination_i;
            writeback_o.value = value_i;
        end
    end

    assign gpr_write_enable_o = writeback_o.valid;
    assign gpr_write_index_o = writeback_o.destination;
    assign gpr_write_data_o = writeback_o.value;

    always_ff @(posedge clk_i) begin
        if (!rst_ni) begin
            commit_seen_q <= 1'b0;
        end else begin
            if (commit_i) begin
                assert (!$isunknown({destination_i, value_i}))
                else $fatal(1, "R5900_WRITEBACK_UNKNOWN: commit payload is unknown");
                commit_seen_q <= 1'b1;
            end else begin
                commit_seen_q <= 1'b0;
            end
        end
    end

    property p_writeback_never_targets_zero;
        @(posedge clk_i) disable iff (!rst_ni)
            gpr_write_enable_o |-> (gpr_write_index_o != R5900_GPR_INDEX_WIDTH'(0));
    endproperty

    assert property (p_writeback_never_targets_zero)
        else $fatal(1, "R5900_WRITEBACK_ZERO: architectural writeback targeted GPR zero");

endmodule

`default_nettype wire
