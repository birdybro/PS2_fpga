// SPDX-License-Identifier: MIT

module register_en #(
    parameter int unsigned WIDTH = 32,
    parameter logic [WIDTH-1:0] RESET_VALUE = '0
) (
    input  logic             clk_i,
    input  logic             rst_ni,
    input  logic             en_i,
    input  logic [WIDTH-1:0] d_i,
    output logic [WIDTH-1:0] q_o
);

    always_ff @(posedge clk_i) begin
        if (!rst_ni) begin
            q_o <= RESET_VALUE;
        end else if (en_i) begin
            q_o <= d_i;
        end
    end

endmodule
