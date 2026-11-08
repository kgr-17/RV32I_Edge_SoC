`default_nettype none
module branch_unit #(parameter bit MASK_UNTAKEN_TARGET=1'b1) (
    input wire rv32_pkg::op_t op_i,
    input wire logic [31:0] pc_i, rs1_i, rs2_i, imm_i,
    output logic [31:0] target_o,
    output logic taken_o, misaligned_o, supported_o
);
    import rv32_pkg::*;
    wire logic [31:0] candidate_target=(op_i==OP_JALR) ?
        ((rs1_i+imm_i) & 32'hffff_fffe) : (pc_i+imm_i);
    always_comb begin
        target_o = 32'h0000_0000;
        taken_o = 1'b0;
        misaligned_o = 1'b0;
        supported_o = 1'b1;
        case (op_i)
            OP_BEQ: taken_o = (rs1_i == rs2_i);
            OP_BNE: taken_o = (rs1_i != rs2_i);
            OP_BLT: taken_o = ($signed(rs1_i) < $signed(rs2_i));
            OP_BGE: taken_o = ($signed(rs1_i) >= $signed(rs2_i));
            OP_BLTU: taken_o = (rs1_i < rs2_i);
            OP_BGEU: taken_o = (rs1_i >= rs2_i);
            OP_JAL, OP_JALR: taken_o = 1'b1;
            default: supported_o = 1'b0;
        endcase
        if (taken_o) begin
            target_o = candidate_target;
            misaligned_o = (candidate_target[1:0] != 2'b00);
        end
        // Internal consumers may qualify target use separately, allowing target
        // arithmetic/alignment and branch comparison to evaluate in parallel.
        if (!MASK_UNTAKEN_TARGET) target_o = candidate_target;
    end
endmodule
`default_nettype wire
