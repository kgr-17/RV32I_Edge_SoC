`timescale 1ns/1ps
`default_nettype none
module register_fixture (
    input  wire logic        clk_i,
    input  wire logic        rst_i,
    input  wire logic        enable_i,
    input  wire logic [31:0] data_i,
    output logic [31:0] data_o
);
    logic [31:0] next_data;

    always_comb begin
        next_data = data_o;
        if (enable_i) begin
            next_data = data_i;
        end
    end

    always_ff @(posedge clk_i) begin
        if (rst_i) begin
            data_o <= 32'h0000_0000;
        end else begin
            data_o <= next_data;
        end
    end
endmodule
`default_nettype wire
