`default_nettype none
// Analysis-only wrapper around actual production primitives, one target clock.
module cdc_probe(
    input wire logic clk_i,arst_i,rx_i,
    input wire logic [15:0] switches_i,
    output wire logic rst_o,
    output wire logic [15:0] switches_o,
    output wire logic rx_valid_o,rx_error_o,rx_busy_o,
    output wire logic [7:0] rx_data_o
);
    reset_sync reset_boundary(.clk_i(clk_i),.arst_i(arst_i),.rst_o(rst_o));
    input_sync #(.WIDTH(32'd16)) switches(.clk_i(clk_i),.rst_i(rst_o),.async_i(switches_i),.sync_o(switches_o));
    uart_rx receiver(.clk_i(clk_i),.rst_i(rst_o),.enable_i(1'b1),.rx_i(rx_i),
        .data_valid_o(rx_valid_o),.frame_error_o(rx_error_o),.data_o(rx_data_o),.busy_o(rx_busy_o));
endmodule
`default_nettype wire
