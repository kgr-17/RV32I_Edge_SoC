`default_nettype none
// Independent captured bus inputs and muxed outputs for bounded-pin synthesis only.
module pipeline_irq_lint_top (
    input wire logic clk_i, rst_i,
    input wire logic [1:0] load_sel_i,
    input wire logic [5:0] observe_sel_i,
    input wire logic [31:0] data_i,
    output logic [31:0] data_o
);
    logic [31:0] instruction_q, read_word_q;
    logic [6:0] control_q;
    always_ff @(posedge clk_i) begin
        if (rst_i) begin
            instruction_q <= 32'd0;
            read_word_q <= 32'd0;
            control_q <= 7'd0;
        end else begin
            case (load_sel_i)
                2'd0: instruction_q <= data_i;
                2'd1: read_word_q <= data_i;
                2'd2: control_q <= data_i[6:0];
                default: begin end
            endcase
        end
    end
    wire logic imem_req_valid_o;
    wire logic [31:0] imem_req_addr_o;
    wire logic imem_rsp_ready_o;
    wire logic dmem_req_valid_o;
    wire logic [31:0] dmem_req_addr_o;
    wire logic dmem_req_write_o;
    wire logic [31:0] dmem_req_wdata_o;
    wire logic [3:0] dmem_req_be_o;
    wire logic dmem_rsp_ready_o;
    wire logic retire_valid_o;
    wire logic [63:0] retire_order_o;
    wire logic [31:0] retire_pc_o;
    wire logic [31:0] retire_next_pc_o;
    wire logic [31:0] retire_insn_o;
    wire logic retire_rd_write_o;
    wire logic [4:0] retire_rd_o;
    wire logic [31:0] retire_rd_wdata_o;
    wire logic retire_mem_valid_o;
    wire logic retire_mem_write_o;
    wire logic [31:0] retire_mem_addr_o;
    wire logic [3:0] retire_mem_be_o;
    wire logic [31:0] retire_mem_wdata_o;
    wire logic [31:0] retire_mem_rdata_o;
    wire logic fault_valid_o;
    wire logic [31:0] fault_pc_o;
    wire logic [31:0] fault_insn_o;
    wire logic [3:0] fault_code_o;
    wire logic [31:0] fault_tval_o;
    wire logic trap_valid_o,retire_csr_valid_o,retire_csr_read_o,retire_csr_write_o;
    wire logic [63:0] trap_order_o;
    wire logic [31:0] trap_pc_o,trap_insn_o,trap_cause_o,trap_tval_o,trap_target_o,retire_csr_rdata_o,retire_csr_wdata_o;
    wire logic [11:0] retire_csr_addr_o;
    pipeline_core #(.ENABLE_TRAPS(1'b1)) dut (.irq_external_i(control_q[6]),
        .clk_i(clk_i),
        .rst_i(rst_i),
        .imem_req_valid_o(imem_req_valid_o),
        .imem_req_ready_i(control_q[0]),
        .imem_req_addr_o(imem_req_addr_o),
        .imem_rsp_valid_i(control_q[1]),
        .imem_rsp_ready_o(imem_rsp_ready_o),
        .imem_rsp_rdata_i(instruction_q),
        .imem_rsp_err_i(control_q[2]),
        .dmem_req_valid_o(dmem_req_valid_o),
        .dmem_req_ready_i(control_q[3]),
        .dmem_req_addr_o(dmem_req_addr_o),
        .dmem_req_write_o(dmem_req_write_o),
        .dmem_req_wdata_o(dmem_req_wdata_o),
        .dmem_req_be_o(dmem_req_be_o),
        .dmem_rsp_valid_i(control_q[4]),
        .dmem_rsp_ready_o(dmem_rsp_ready_o),
        .dmem_rsp_rdata_i(read_word_q),
        .dmem_rsp_err_i(control_q[5]),
        .retire_valid_o(retire_valid_o),
        .retire_order_o(retire_order_o),
        .retire_pc_o(retire_pc_o),
        .retire_next_pc_o(retire_next_pc_o),
        .retire_insn_o(retire_insn_o),
        .retire_rd_write_o(retire_rd_write_o),
        .retire_rd_o(retire_rd_o),
        .retire_rd_wdata_o(retire_rd_wdata_o),
        .retire_mem_valid_o(retire_mem_valid_o),
        .retire_mem_write_o(retire_mem_write_o),
        .retire_mem_addr_o(retire_mem_addr_o),
        .retire_mem_be_o(retire_mem_be_o),
        .retire_mem_wdata_o(retire_mem_wdata_o),
        .retire_mem_rdata_o(retire_mem_rdata_o),
        .fault_valid_o(fault_valid_o),
        .fault_pc_o(fault_pc_o),
        .fault_insn_o(fault_insn_o),
        .fault_code_o(fault_code_o),
        .fault_tval_o(fault_tval_o)
    ,.trap_valid_o(trap_valid_o),.trap_order_o(trap_order_o),.trap_pc_o(trap_pc_o),.trap_insn_o(trap_insn_o),.trap_cause_o(trap_cause_o),.trap_tval_o(trap_tval_o),.trap_target_o(trap_target_o),.retire_csr_valid_o(retire_csr_valid_o),.retire_csr_read_o(retire_csr_read_o),.retire_csr_write_o(retire_csr_write_o),.retire_csr_addr_o(retire_csr_addr_o),.retire_csr_rdata_o(retire_csr_rdata_o),.retire_csr_wdata_o(retire_csr_wdata_o));
    always_comb begin
        data_o = 32'd0;
        case (observe_sel_i)
            6'd0: data_o = {31'd0, imem_req_valid_o};
            6'd1: data_o = imem_req_addr_o;
            6'd2: data_o = {31'd0, imem_rsp_ready_o};
            6'd3: data_o = {31'd0, dmem_req_valid_o};
            6'd4: data_o = dmem_req_addr_o;
            6'd5: data_o = {31'd0, dmem_req_write_o};
            6'd6: data_o = dmem_req_wdata_o;
            6'd7: data_o = {28'd0, dmem_req_be_o};
            6'd8: data_o = {31'd0, dmem_rsp_ready_o};
            6'd9: data_o = {31'd0, retire_valid_o};
            6'd10: data_o = retire_order_o[31:0];
            6'd11: data_o = retire_order_o[63:32];
            6'd12: data_o = retire_pc_o;
            6'd13: data_o = retire_next_pc_o;
            6'd14: data_o = retire_insn_o;
            6'd15: data_o = {31'd0, retire_rd_write_o};
            6'd16: data_o = {27'd0, retire_rd_o};
            6'd17: data_o = retire_rd_wdata_o;
            6'd18: data_o = {31'd0, retire_mem_valid_o};
            6'd19: data_o = {31'd0, retire_mem_write_o};
            6'd20: data_o = retire_mem_addr_o;
            6'd21: data_o = {28'd0, retire_mem_be_o};
            6'd22: data_o = retire_mem_wdata_o;
            6'd23: data_o = retire_mem_rdata_o;
            6'd24: data_o = {31'd0, fault_valid_o};
            6'd25: data_o = fault_pc_o;
            6'd26: data_o = fault_insn_o;
            6'd27: data_o = {28'd0, fault_code_o};
            6'd28: data_o = fault_tval_o;
            6'd29: data_o = {31'd0,trap_valid_o};
            6'd30: data_o = trap_order_o[31:0];
            6'd31: data_o = trap_order_o[63:32];
            6'd32: data_o = trap_pc_o;
            6'd33: data_o = trap_insn_o;
            6'd34: data_o = trap_cause_o;
            6'd35: data_o = trap_tval_o;
            6'd36: data_o = trap_target_o;
            6'd37: data_o = {31'd0,retire_csr_valid_o};
            6'd38: data_o = {31'd0,retire_csr_read_o};
            6'd39: data_o = {31'd0,retire_csr_write_o};
            6'd40: data_o = {20'd0,retire_csr_addr_o};
            6'd41: data_o = retire_csr_rdata_o;
            6'd42: data_o = retire_csr_wdata_o;
            default: data_o = 32'd0;
        endcase
    end
endmodule
`default_nettype wire
