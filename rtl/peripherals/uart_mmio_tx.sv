`default_nettype none
// Compatibility TX-only interface; canonical UART also serves T042 RX.
module uart_mmio_tx #(parameter int unsigned CLKS_PER_BIT=32'd868)(
    input wire logic clk_i,rst_i,req_valid_i,req_write_i,
    input wire logic [31:0] req_addr_i,
    input wire logic [7:0] req_wdata_i,
    input wire logic [3:0] req_be_i,
    output wire logic req_ready_o,rsp_valid_o,rsp_err_o,
    output wire logic [31:0] rsp_rdata_o,
    input wire logic rsp_ready_i,
    output wire logic tx_o
);
    uart_mmio #(.CLKS_PER_BIT(CLKS_PER_BIT)) combined(
        .clk_i(clk_i),.rst_i(rst_i),.rx_i(1'b1),.req_valid_i(req_valid_i),
        .req_write_i(req_write_i),.req_addr_i(req_addr_i),.req_wdata_i({2'b00,req_wdata_i}),
        .req_be_i(req_be_i),.req_ready_o(req_ready_o),.rsp_valid_o(rsp_valid_o),
        .rsp_err_o(rsp_err_o),.rsp_rdata_o(rsp_rdata_o),.rsp_ready_i(rsp_ready_i),.tx_o(tx_o));
endmodule
`default_nettype wire
