`default_nettype none
module branch_unit (
    input wire rv32_pkg::op_t op_i,
    input wire logic [31:0] pc_i, rs1_i, rs2_i, imm_i,
    output logic [31:0] target_o,
    output logic taken_o, misaligned_o, supported_o
);
    import rv32_pkg::*;
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
            if (op_i == OP_JALR) target_o = (rs1_i + imm_i) & 32'hffff_fffe;
            else target_o = pc_i + imm_i;
            misaligned_o = (target_o[1:0] != 2'b00);
        end
    end
endmodule
`default_nettype wire
