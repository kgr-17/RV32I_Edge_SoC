`default_nettype none
module edge_soc #(
    parameter string ROM_INIT_FILE="soc_boot.mem",
    parameter int unsigned UART_CLKS_PER_BIT=32'd868,
    parameter bit ENABLE_TRAPS=1'b0
) (
    input wire logic clk_i,rst_i,rx_i,
    input wire logic [15:0] switches_i,
    output wire logic tx_o,
    output wire logic [15:0] leds_o,
    output wire logic retire_valid_o,
    output wire logic [63:0] retire_order_o,
    output wire logic [31:0] retire_pc_o,retire_next_pc_o,retire_insn_o,
    output wire logic retire_rd_write_o,
    output wire logic [4:0] retire_rd_o,
    output wire logic [31:0] retire_rd_wdata_o,
    output wire logic retire_mem_valid_o,retire_mem_write_o,
    output wire logic [31:0] retire_mem_addr_o,
    output wire logic [3:0] retire_mem_be_o,
    output wire logic [31:0] retire_mem_wdata_o,retire_mem_rdata_o,
    output wire logic fault_valid_o,
    output wire logic [31:0] fault_pc_o,fault_insn_o,
    output wire logic [3:0] fault_code_o,
    output wire logic [31:0] fault_tval_o,
    output wire logic trap_valid_o,
    output wire logic [63:0] trap_order_o,
    output wire logic [31:0] trap_pc_o,trap_insn_o,trap_cause_o,trap_tval_o,trap_target_o,
    output wire logic retire_csr_valid_o,retire_csr_read_o,retire_csr_write_o,
    output wire logic [11:0] retire_csr_addr_o,
    output wire logic [31:0] retire_csr_rdata_o,retire_csr_wdata_o
);
    wire logic iv,ir,is,irdy,ie,dv,dr,dw,ds,dsr,de;
    wire logic [31:0] ia,idata,da,dd,ddata;
    wire logic [3:0] db;
    wire logic irq;
    pipeline_core #(.ENABLE_TRAPS(ENABLE_TRAPS)) cpu(.clk_i(clk_i),.rst_i(rst_i),.irq_external_i(irq),.imem_req_valid_o(iv),.imem_req_ready_i(ir),.imem_req_addr_o(ia),
        .imem_rsp_valid_i(is),.imem_rsp_ready_o(irdy),.imem_rsp_rdata_i(idata),.imem_rsp_err_i(ie),
        .dmem_req_valid_o(dv),.dmem_req_ready_i(dr),.dmem_req_addr_o(da),.dmem_req_write_o(dw),.dmem_req_wdata_o(dd),.dmem_req_be_o(db),
        .dmem_rsp_valid_i(ds),.dmem_rsp_ready_o(dsr),.dmem_rsp_rdata_i(ddata),.dmem_rsp_err_i(de),
        .retire_valid_o(retire_valid_o),.retire_order_o(retire_order_o),.retire_pc_o(retire_pc_o),.retire_next_pc_o(retire_next_pc_o),.retire_insn_o(retire_insn_o),
        .retire_rd_write_o(retire_rd_write_o),.retire_rd_o(retire_rd_o),.retire_rd_wdata_o(retire_rd_wdata_o),
        .retire_mem_valid_o(retire_mem_valid_o),.retire_mem_write_o(retire_mem_write_o),.retire_mem_addr_o(retire_mem_addr_o),.retire_mem_be_o(retire_mem_be_o),
        .retire_mem_wdata_o(retire_mem_wdata_o),.retire_mem_rdata_o(retire_mem_rdata_o),
        .fault_valid_o(fault_valid_o),.fault_pc_o(fault_pc_o),.fault_insn_o(fault_insn_o),.fault_code_o(fault_code_o),.fault_tval_o(fault_tval_o),
        .trap_valid_o(trap_valid_o),.trap_order_o(trap_order_o),.trap_pc_o(trap_pc_o),.trap_insn_o(trap_insn_o),.trap_cause_o(trap_cause_o),.trap_tval_o(trap_tval_o),.trap_target_o(trap_target_o),
        .retire_csr_valid_o(retire_csr_valid_o),.retire_csr_read_o(retire_csr_read_o),.retire_csr_write_o(retire_csr_write_o),.retire_csr_addr_o(retire_csr_addr_o),.retire_csr_rdata_o(retire_csr_rdata_o),.retire_csr_wdata_o(retire_csr_wdata_o));
    soc_fabric #(.ROM_INIT_FILE(ROM_INIT_FILE),.UART_CLKS_PER_BIT(UART_CLKS_PER_BIT),.ENABLE_IRQ(ENABLE_TRAPS)) fabric(
        .clk_i(clk_i),.rst_i(rst_i),.rx_i(rx_i),.switches_i(switches_i),.tx_o(tx_o),.leds_o(leds_o),.irq_o(irq),
        .i_req_valid_i(iv),.i_req_ready_o(ir),.i_req_addr_i(ia),.i_rsp_valid_o(is),.i_rsp_err_o(ie),.i_rsp_rdata_o(idata),.i_rsp_ready_i(irdy),
        .d_req_valid_i(dv),.d_req_write_i(dw),.d_req_ready_o(dr),.d_req_addr_i(da),.d_req_wdata_i(dd),.d_req_be_i(db),
        .d_rsp_valid_o(ds),.d_rsp_err_o(de),.d_rsp_rdata_o(ddata),.d_rsp_ready_i(dsr));
endmodule
`default_nettype wire
