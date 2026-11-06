`default_nettype none
// Probe the real peripheral with a byte-selecting payload adapter. Every probe
// input bit has a meaningful use; reserved UART write bits remain constant0.
// Full32-bit ignored/reserved behavior is checked directly by tb_uart, unchanged.
module uart_lint_top (
    input wire logic clk_i, rst_i, req_valid_i, req_write_i, rsp_ready_i,
    input wire logic [31:0] req_addr_i, payload_word_i,
    input wire logic [1:0] payload_lane_i,
    input wire logic [3:0] req_be_i,
    output wire logic req_ready_o, rsp_valid_o, rsp_err_o, tx_o,
    output wire logic [31:0] rsp_rdata_o
);
    wire logic [7:0] byte_payload = payload_word_i[payload_lane_i*8 +: 8];
    uart_mmio_tx dut (.clk_i(clk_i),.rst_i(rst_i),.req_valid_i(req_valid_i),.req_write_i(req_write_i),
        .req_addr_i(req_addr_i),.req_wdata_i(byte_payload),.req_be_i(req_be_i),
        .rsp_ready_i(rsp_ready_i),.req_ready_o(req_ready_o),.rsp_valid_o(rsp_valid_o),
        .rsp_err_o(rsp_err_o),.rsp_rdata_o(rsp_rdata_o),.tx_o(tx_o));
endmodule
`default_nettype wire
