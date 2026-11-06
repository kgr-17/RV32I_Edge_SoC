`default_nettype none
module uart_full_lint_top(
    input wire logic clk_i,rst_i,rx_i,req_valid_i,req_write_i,rsp_ready_i,
    input wire logic [31:0] req_addr_i,payload_i,
    input wire logic [1:0] lane_i,
    input wire logic [3:0] req_be_i,
    output wire logic req_ready_o,rsp_valid_o,rsp_err_o,tx_o,
    output wire logic [31:0] rsp_rdata_o
);
    wire logic [9:0] selected={payload_i[9:8],payload_i[8*lane_i+:8]};
    uart_mmio dut(.clk_i(clk_i),.rst_i(rst_i),.rx_i(rx_i),
        .req_valid_i(req_valid_i),.req_write_i(req_write_i),.req_addr_i(req_addr_i),
        .req_wdata_i(selected),.req_be_i(req_be_i),.req_ready_o(req_ready_o),
        .rsp_valid_o(rsp_valid_o),.rsp_err_o(rsp_err_o),.rsp_rdata_o(rsp_rdata_o),
        .rsp_ready_i(rsp_ready_i),.tx_o(tx_o));
endmodule
`default_nettype wire
