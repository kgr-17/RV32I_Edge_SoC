`default_nettype none
// Single-clock 8N1 transmitter. 100MHz/868 = 115207.37baud (target115200).
module uart_tx #(
    parameter int unsigned CLKS_PER_BIT = 32'd868
) (
    input wire logic clk_i, rst_i, enable_i, data_valid_i,
    input wire logic [7:0] data_i,
    output wire logic data_ready_o, busy_o, tx_o
);
    localparam int unsigned COUNT_W = $clog2(CLKS_PER_BIT);
    localparam logic [COUNT_W-1:0] LAST_COUNT = COUNT_W'(CLKS_PER_BIT - 32'd1);
    logic [COUNT_W-1:0] count_q;
    logic [3:0] bit_q;
    logic [9:0] shift_q;
    logic busy_q;
    if (CLKS_PER_BIT < 32'd2 || CLKS_PER_BIT > 32'd65536) begin : invalid_divisor
        initial $fatal(1, "UART_DIVISOR_RANGE");
    end
    assign data_ready_o = !rst_i && enable_i && !busy_q;
    assign busy_o = busy_q;
    assign tx_o = busy_q ? shift_q[0] : 1'b1;
    always_ff @(posedge clk_i) begin
        if (rst_i) begin
            count_q <= {COUNT_W{1'b0}};
            bit_q <= 4'd0;
            shift_q <= 10'h3ff;
            busy_q <= 1'b0;
        end else if (!busy_q) begin
            if (data_valid_i && enable_i) begin
                shift_q <= {1'b1, data_i, 1'b0};
                count_q <= LAST_COUNT;
                bit_q <= 4'd0;
                busy_q <= 1'b1;
            end
        end else if (count_q != {COUNT_W{1'b0}}) begin
            count_q <= count_q - COUNT_W'(1);
        end else if (bit_q == 4'd9) begin
            busy_q <= 1'b0;
            shift_q <= 10'h3ff;
            bit_q <= 4'd0;
            count_q <= {COUNT_W{1'b0}};
        end else begin
            shift_q <= {1'b1, shift_q[9:1]};
            bit_q <= bit_q + 4'd1;
            count_q <= LAST_COUNT;
        end
    end
endmodule
`default_nettype wire
