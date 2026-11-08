`default_nettype none
module timer_irq_lint_top(
    input wire logic clk_i,rst_i,req_valid_i,req_write_i,
    input wire logic [31:0] req_addr_i,req_wdata_i,
    input wire logic [3:0] req_be_i,
    output wire logic req_ready_o,rsp_valid_o,rsp_err_o,
    output wire logic [31:0] rsp_rdata_o,
    input wire logic rsp_ready_i,
    output wire logic irq_o
);
    timer #(.ENABLE_IRQ(1'b1)) dut(.clk_i(clk_i),.rst_i(rst_i),.req_valid_i(req_valid_i),.req_write_i(req_write_i),.req_addr_i(req_addr_i),.req_wdata_i(req_wdata_i),.req_be_i(req_be_i),.req_ready_o(req_ready_o),.rsp_valid_o(rsp_valid_o),.rsp_err_o(rsp_err_o),.rsp_rdata_o(rsp_rdata_o),.rsp_ready_i(rsp_ready_i),.irq_o(irq_o));
endmodule
`default_nettype wire
