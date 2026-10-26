`default_nettype none
// Sequential implementation of the reviewed v0.2 core interface. No prefetch.
module reference_core (
    input wire logic clk_i, rst_i,
    output wire logic imem_req_valid_o,
    input wire logic imem_req_ready_i,
    output wire logic [31:0] imem_req_addr_o,
    input wire logic imem_rsp_valid_i,
    output wire logic imem_rsp_ready_o,
    input wire logic [31:0] imem_rsp_rdata_i,
    input wire logic imem_rsp_err_i,
    output wire logic dmem_req_valid_o,
    input wire logic dmem_req_ready_i,
    output wire logic [31:0] dmem_req_addr_o,
    output wire logic dmem_req_write_o,
    output wire logic [31:0] dmem_req_wdata_o,
    output wire logic [3:0] dmem_req_be_o,
    input wire logic dmem_rsp_valid_i,
    output wire logic dmem_rsp_ready_o,
    input wire logic [31:0] dmem_rsp_rdata_i,
    input wire logic dmem_rsp_err_i,
    output logic retire_valid_o,
    output logic [63:0] retire_order_o,
    output logic [31:0] retire_pc_o, retire_next_pc_o, retire_insn_o,
    output logic retire_rd_write_o,
    output logic [4:0] retire_rd_o,
    output logic [31:0] retire_rd_wdata_o,
    output logic retire_mem_valid_o, retire_mem_write_o,
    output logic [31:0] retire_mem_addr_o,
    output logic [3:0] retire_mem_be_o,
    output logic [31:0] retire_mem_wdata_o, retire_mem_rdata_o,
    output logic fault_valid_o,
    output logic [31:0] fault_pc_o, fault_insn_o,
    output logic [3:0] fault_code_o,
    output logic [31:0] fault_tval_o
);
    import rv32_pkg::*;
    typedef enum logic [2:0] {
        FETCH_REQ=3'd0, FETCH_RSP=3'd1, EXECUTE=3'd2,
        DATA_REQ=3'd3, DATA_RSP=3'd4, COMMIT=3'd5, HALTED=3'd6
    } state_t;
    state_t state_q;
    logic [31:0] pc_q, insn_q, next_pc_q, wb_value_q;
    logic [63:0] order_q;
    logic mem_valid_q, mem_write_q;
    logic [31:0] mem_addr_q, mem_wdata_q, mem_rdata_q;
    logic [3:0] mem_be_q;
    decode_t dec;
    wire logic [31:0] a, b, alu_result, branch_target, load_data, store_word;
    wire logic alu_ok, branch_ok, branch_taken, branch_bad, lsu_ok, lsu_bad, lsu_write;
    wire logic [3:0] lsu_be;
    wire logic [31:0] alu_b, effective_addr;
    logic [31:0] exec_value, exec_next, exec_tval;
    logic [3:0] exec_fault;
    wire logic gpr_write;
    assign gpr_write = !rst_i && (state_q == COMMIT) && dec.writes_rd;
    decoder decode (.insn_i(insn_q), .decode_o(dec));
    regfile registers (.clk_i(clk_i), .rst_i(rst_i), .write_en_i(gpr_write),
        .write_addr_i(dec.rd), .write_data_i(wb_value_q),
        .read_addr_a_i(dec.rs1), .read_addr_b_i(dec.rs2), .read_data_a_o(a), .read_data_b_o(b));
    assign alu_b = ((dec.op >= OP_ADDI) && (dec.op <= OP_SRAI)) ? dec.imm : b;
    assign effective_addr = a + dec.imm;
    alu arithmetic (.op_i(dec.op), .a_i(a), .b_i(alu_b), .result_o(alu_result), .supported_o(alu_ok));
    branch_unit branch (.op_i(dec.op), .pc_i(pc_q), .rs1_i(a), .rs2_i(b), .imm_i(dec.imm),
        .target_o(branch_target), .taken_o(branch_taken), .misaligned_o(branch_bad), .supported_o(branch_ok));
    lsu memory_format (.op_i(dec.op), .byte_offset_i(effective_addr[1:0]), .store_data_i(b),
        .read_word_i(dmem_rsp_rdata_i), .load_data_o(load_data), .store_word_o(store_word),
        .byte_enable_o(lsu_be), .write_o(lsu_write), .misaligned_o(lsu_bad), .supported_o(lsu_ok));

    assign imem_req_valid_o = !rst_i && (state_q == FETCH_REQ);
    assign imem_req_addr_o = imem_req_valid_o ? pc_q : 32'd0;
    assign imem_rsp_ready_o = !rst_i && (state_q == FETCH_RSP);
    assign dmem_req_valid_o = !rst_i && (state_q == DATA_REQ);
    assign dmem_req_addr_o = dmem_req_valid_o ? mem_addr_q : 32'd0;
    assign dmem_req_write_o = dmem_req_valid_o && mem_write_q;
    assign dmem_req_be_o = dmem_req_valid_o ? mem_be_q : 4'd0;
    assign dmem_req_wdata_o = dmem_req_valid_o ? mem_wdata_q : 32'd0;
    assign dmem_rsp_ready_o = !rst_i && (state_q == DATA_RSP);

    always_comb begin
        exec_value = 32'd0;
        exec_next = pc_q + 32'd4;
        exec_fault = 4'd0;
        exec_tval = 32'd0;
        if (alu_ok) exec_value = alu_result;
        if (branch_ok && branch_taken) exec_next = branch_target;
        case (dec.op)
            OP_LUI: exec_value = dec.imm;
            OP_AUIPC: exec_value = pc_q + dec.imm;
            OP_JAL, OP_JALR: exec_value = pc_q + 32'd4;
            default: begin end
        endcase
        if (dec.illegal) begin
            exec_fault = 4'd1;
            exec_tval = insn_q;
        end else if (dec.op == OP_ECALL) exec_fault = 4'd8;
        else if (dec.op == OP_EBREAK) exec_fault = 4'd9;
        else if (branch_ok && branch_bad) begin
            exec_fault = 4'd2;
            exec_tval = branch_target;
        end else if (lsu_ok && lsu_bad) begin
            exec_fault = ((dec.op >= OP_SB) && (dec.op <= OP_SW)) ? 4'd6 : 4'd4;
            exec_tval = effective_addr;
        end
    end

    // Inactive trace metadata is zero; sticky faults clear only on reset.
    task automatic clear_trace;
        retire_valid_o <= 1'b0;
        retire_order_o <= 64'd0;
        retire_pc_o <= 32'd0;
        retire_next_pc_o <= 32'd0;
        retire_insn_o <= 32'd0;
        retire_rd_write_o <= 1'b0;
        retire_rd_o <= 5'd0;
        retire_rd_wdata_o <= 32'd0;
        retire_mem_valid_o <= 1'b0;
        retire_mem_write_o <= 1'b0;
        retire_mem_addr_o <= 32'd0;
        retire_mem_be_o <= 4'd0;
        retire_mem_wdata_o <= 32'd0;
        retire_mem_rdata_o <= 32'd0;
    endtask

    always_ff @(posedge clk_i) begin
        clear_trace();
        if (rst_i) begin
            state_q <= FETCH_REQ;
            pc_q <= 32'd0;
            insn_q <= 32'd0;
            next_pc_q <= 32'd0;
            wb_value_q <= 32'd0;
            order_q <= 64'd0;
            mem_valid_q <= 1'b0;
            mem_write_q <= 1'b0;
            mem_addr_q <= 32'd0;
            mem_wdata_q <= 32'd0;
            mem_rdata_q <= 32'd0;
            mem_be_q <= 4'd0;
            fault_valid_o <= 1'b0;
            fault_pc_o <= 32'd0;
            fault_insn_o <= 32'd0;
            fault_code_o <= 4'd0;
            fault_tval_o <= 32'd0;
        end else begin
            case (state_q)
                FETCH_REQ: if (imem_req_ready_i) state_q <= FETCH_RSP;
                FETCH_RSP: if (imem_rsp_valid_i) begin
                    if (imem_rsp_err_i) begin
                        fault_valid_o <= 1'b1;
                        fault_pc_o <= pc_q;
                        fault_insn_o <= 32'd0;
                        fault_code_o <= 4'd3;
                        fault_tval_o <= pc_q;
                        state_q <= HALTED;
                    end else begin
                        insn_q <= imem_rsp_rdata_i;
                        state_q <= EXECUTE;
                    end
                end
                EXECUTE: begin
                    if (exec_fault != 4'd0) begin
                        fault_valid_o <= 1'b1;
                        fault_pc_o <= pc_q;
                        fault_insn_o <= insn_q;
                        fault_code_o <= exec_fault;
                        fault_tval_o <= exec_tval;
                        state_q <= HALTED;
                    end else begin
                        next_pc_q <= exec_next;
                        wb_value_q <= exec_value;
                        mem_valid_q <= lsu_ok;
                        mem_write_q <= lsu_write;
                        mem_addr_q <= lsu_ok ? effective_addr : 32'd0;
                        mem_wdata_q <= store_word;
                        mem_be_q <= lsu_be;
                        mem_rdata_q <= 32'd0;
                        state_q <= lsu_ok ? DATA_REQ : COMMIT;
                    end
                end
                DATA_REQ: if (dmem_req_ready_i) state_q <= DATA_RSP;
                DATA_RSP: if (dmem_rsp_valid_i) begin
                    if (dmem_rsp_err_i) begin
                        fault_valid_o <= 1'b1;
                        fault_pc_o <= pc_q;
                        fault_insn_o <= insn_q;
                        fault_code_o <= mem_write_q ? 4'd7 : 4'd5;
                        fault_tval_o <= mem_addr_q;
                        state_q <= HALTED;
                    end else begin
                        wb_value_q <= mem_write_q ? 32'd0 : load_data;
                        mem_rdata_q <= mem_write_q ? 32'd0 : dmem_rsp_rdata_i;
                        state_q <= COMMIT;
                    end
                end
                COMMIT: begin
                    retire_valid_o <= 1'b1;
                    retire_order_o <= order_q;
                    retire_pc_o <= pc_q;
                    retire_next_pc_o <= next_pc_q;
                    retire_insn_o <= insn_q;
                    retire_rd_write_o <= dec.writes_rd;
                    retire_rd_o <= dec.rd;
                    retire_rd_wdata_o <= dec.writes_rd ? wb_value_q : 32'd0;
                    retire_mem_valid_o <= mem_valid_q;
                    retire_mem_write_o <= mem_write_q;
                    retire_mem_addr_o <= mem_addr_q;
                    retire_mem_be_o <= mem_be_q;
                    retire_mem_wdata_o <= mem_wdata_q;
                    retire_mem_rdata_o <= mem_rdata_q;
                    order_q <= order_q + 64'd1;
                    pc_q <= next_pc_q;
                    state_q <= FETCH_REQ;
                end
                HALTED: begin end
                default: state_q <= HALTED;
            endcase
        end
    end
endmodule
`default_nettype wire
