`default_nettype none
// Basys3 SoC boundary. Original diagnostic preserved in diagnostic_top.sv.
module basys3_top #(
    parameter bit ENABLE_TRAPS=1'b1,
    parameter string ROM_INIT_FILE="irq_boot.mem"
) (
    input  wire logic        clk,
    input  wire logic        btnC,
    input  wire logic [15:0] sw,
    input  wire logic        RsRx,
    output logic [15:0] led,
    output logic        RsTx
);
    // One oscillator clock; raw inputs enter existing UART/GPIO synchronizers.
    logic rst_s=1'b1;
    logic reset_release;
    reset_sync #(.ASYNC_ASSERT(1'b0)) reset_boundary(.clk_i(clk),.arst_i(btnC),.rst_o(reset_release));
    // Both raw button transitions pass two fully clocked synchronizer stages.
    // The distribution copy is fed by a synchronous signal, so an asynchronous
    // assertion cannot metastabilize the high-fanout shared reset register.
    always_ff @(posedge clk) rst_s<=reset_release;
    edge_soc #(.ENABLE_TRAPS(ENABLE_TRAPS),.ROM_INIT_FILE(ROM_INIT_FILE)) soc(.clk_i(clk),.rst_i(rst_s),.rx_i(RsRx),.switches_i(sw),.tx_o(RsTx),.leds_o(led),
        .retire_valid_o(),.retire_order_o(),.retire_pc_o(),.retire_next_pc_o(),.retire_insn_o(),
        .retire_rd_write_o(),.retire_rd_o(),.retire_rd_wdata_o(),.retire_mem_valid_o(),.retire_mem_write_o(),
        .retire_mem_addr_o(),.retire_mem_be_o(),.retire_mem_wdata_o(),.retire_mem_rdata_o(),
        .fault_valid_o(),.fault_pc_o(),.fault_insn_o(),.fault_code_o(),.fault_tval_o(),.trap_valid_o(),.trap_order_o(),.trap_pc_o(),.trap_insn_o(),.trap_cause_o(),.trap_tval_o(),.trap_target_o(),.retire_csr_valid_o(),.retire_csr_read_o(),.retire_csr_write_o(),.retire_csr_addr_o(),.retire_csr_rdata_o(),.retire_csr_wdata_o());
endmodule
`default_nettype wire
