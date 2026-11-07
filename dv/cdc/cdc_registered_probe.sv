`default_nettype none
// Analysis-only off-chip launch registers. This source domain is never part of
// the production single-clock target. It makes actual CDC paths explicit.
module cdc_registered_probe(
    input wire logic clk_i,clk_external_i,source_rst_i,source_rx_i,
    input wire logic [15:0] source_sw_i,
    output wire logic rst_o,
    output wire logic [15:0] switches_o,
    output wire logic rx_valid_o,rx_error_o,rx_busy_o,
    output wire logic [7:0] rx_data_o
);
    logic source_rst_q,source_rx_q;
    logic [15:0] source_sw_q;
    always_ff @(posedge clk_external_i) begin
        source_rst_q<=source_rst_i;source_rx_q<=source_rx_i;source_sw_q<=source_sw_i;
    end
    cdc_probe boundary(.clk_i(clk_i),.arst_i(source_rst_q),.rx_i(source_rx_q),.switches_i(source_sw_q),
        .rst_o(rst_o),.switches_o(switches_o),.rx_valid_o(rx_valid_o),.rx_error_o(rx_error_o),.rx_busy_o(rx_busy_o),.rx_data_o(rx_data_o));
endmodule
`default_nettype wire
