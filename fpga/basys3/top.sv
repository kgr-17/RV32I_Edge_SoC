`default_nettype none
// Basys3 SoC boundary. Original diagnostic preserved in diagnostic_top.sv.
module basys3_top (
    input  wire logic        clk,
    input  wire logic        btnC,
    input  wire logic [15:0] sw,
    input  wire logic        RsRx,
    output logic [15:0] led,
    output logic        RsTx
);
    // One oscillator clock; raw inputs enter existing UART/GPIO synchronizers.
    logic rst_s;
    reset_sync reset_boundary(.clk_i(clk),.arst_i(btnC),.rst_o(rst_s));
    edge_soc soc(.clk_i(clk),.rst_i(rst_s),.rx_i(RsRx),.switches_i(sw),.tx_o(RsTx),.leds_o(led),
        .retire_valid_o(),.retire_order_o(),.retire_pc_o(),.retire_next_pc_o(),.retire_insn_o(),
        .retire_rd_write_o(),.retire_rd_o(),.retire_rd_wdata_o(),.retire_mem_valid_o(),.retire_mem_write_o(),
        .retire_mem_addr_o(),.retire_mem_be_o(),.retire_mem_wdata_o(),.retire_mem_rdata_o(),
        .fault_valid_o(),.fault_pc_o(),.fault_insn_o(),.fault_code_o(),.fault_tval_o());
endmodule
`default_nettype wire
