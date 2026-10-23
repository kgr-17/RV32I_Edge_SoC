`default_nettype none
module decoder (
    input wire logic [31:0] insn_i,
    output rv32_pkg::decode_t decode_o
);
    import rv32_pkg::*;

    always_comb begin
        decode_o = '0;
        decode_o.op = OP_ILLEGAL;
        case (insn_i[6:0])
            7'h37: decode_o.op = OP_LUI;
            7'h17: decode_o.op = OP_AUIPC;
            7'h6f: decode_o.op = OP_JAL;
            7'h67: if (insn_i[14:12] == 3'b000) decode_o.op = OP_JALR;
            7'h63: begin
                case (insn_i[14:12])
                    3'b000: decode_o.op = OP_BEQ;
                    3'b001: decode_o.op = OP_BNE;
                    3'b100: decode_o.op = OP_BLT;
                    3'b101: decode_o.op = OP_BGE;
                    3'b110: decode_o.op = OP_BLTU;
                    3'b111: decode_o.op = OP_BGEU;
                    default: decode_o.op = OP_ILLEGAL;
                endcase
            end
            7'h03: begin
                case (insn_i[14:12])
                    3'b000: decode_o.op = OP_LB;
                    3'b001: decode_o.op = OP_LH;
                    3'b010: decode_o.op = OP_LW;
                    3'b100: decode_o.op = OP_LBU;
                    3'b101: decode_o.op = OP_LHU;
                    default: decode_o.op = OP_ILLEGAL;
                endcase
            end
            7'h23: begin
                case (insn_i[14:12])
                    3'b000: decode_o.op = OP_SB;
                    3'b001: decode_o.op = OP_SH;
                    3'b010: decode_o.op = OP_SW;
                    default: decode_o.op = OP_ILLEGAL;
                endcase
            end
            7'h13: begin
                case (insn_i[14:12])
                    3'b000: decode_o.op = OP_ADDI;
                    3'b010: decode_o.op = OP_SLTI;
                    3'b011: decode_o.op = OP_SLTIU;
                    3'b100: decode_o.op = OP_XORI;
                    3'b110: decode_o.op = OP_ORI;
                    3'b111: decode_o.op = OP_ANDI;
                    3'b001: if (insn_i[31:25] == 7'h00) decode_o.op = OP_SLLI;
                    3'b101: begin
                        case (insn_i[31:25])
                            7'h00: decode_o.op = OP_SRLI;
                            7'h20: decode_o.op = OP_SRAI;
                            default: decode_o.op = OP_ILLEGAL;
                        endcase
                    end
                    default: decode_o.op = OP_ILLEGAL;
                endcase
            end
            7'h33: begin
                case ({insn_i[31:25], insn_i[14:12]})
                    10'b0000000_000: decode_o.op = OP_ADD;
                    10'b0100000_000: decode_o.op = OP_SUB;
                    10'b0000000_001: decode_o.op = OP_SLL;
                    10'b0000000_010: decode_o.op = OP_SLT;
                    10'b0000000_011: decode_o.op = OP_SLTU;
                    10'b0000000_100: decode_o.op = OP_XOR;
                    10'b0000000_101: decode_o.op = OP_SRL;
                    10'b0100000_101: decode_o.op = OP_SRA;
                    10'b0000000_110: decode_o.op = OP_OR;
                    10'b0000000_111: decode_o.op = OP_AND;
                    default: decode_o.op = OP_ILLEGAL;
                endcase
            end
            // Ignore every non-funct3 FENCE field; downstream must full-drain.
            7'h0f: if (insn_i[14:12] == 3'b000) decode_o.op = OP_FENCE;
            7'h73: begin
                case (insn_i)
                    32'h0000_0073: decode_o.op = OP_ECALL;
                    32'h0010_0073: decode_o.op = OP_EBREAK;
                    default: decode_o.op = OP_ILLEGAL;
                endcase
            end
            default: decode_o.op = OP_ILLEGAL;
        endcase

        decode_o.illegal = (decode_o.op == OP_ILLEGAL);
        // Only legal operations can expose operands or a destination.
        case (decode_o.op)
            OP_LUI, OP_AUIPC: begin
                decode_o.imm = {insn_i[31:12], 12'b0};
                decode_o.writes_rd = (insn_i[11:7] != 5'd0);
            end
            OP_JAL: begin
                decode_o.imm = {{11{insn_i[31]}}, insn_i[31], insn_i[19:12],
                                insn_i[20], insn_i[30:21], 1'b0};
                decode_o.writes_rd = (insn_i[11:7] != 5'd0);
            end
            OP_JALR, OP_LB, OP_LH, OP_LW, OP_LBU, OP_LHU,
            OP_ADDI, OP_SLTI, OP_SLTIU, OP_XORI, OP_ORI, OP_ANDI,
            OP_SLLI, OP_SRLI, OP_SRAI: begin
                decode_o.uses_rs1 = 1'b1;
                decode_o.writes_rd = (insn_i[11:7] != 5'd0);
                if ((decode_o.op == OP_SLLI) || (decode_o.op == OP_SRLI) ||
                    (decode_o.op == OP_SRAI))
                    decode_o.imm = {27'b0, insn_i[24:20]};
                else
                    decode_o.imm = {{20{insn_i[31]}}, insn_i[31:20]};
            end
            OP_BEQ, OP_BNE, OP_BLT, OP_BGE, OP_BLTU, OP_BGEU: begin
                decode_o.uses_rs1 = 1'b1;
                decode_o.uses_rs2 = 1'b1;
                decode_o.imm = {{19{insn_i[31]}}, insn_i[31], insn_i[7],
                                insn_i[30:25], insn_i[11:8], 1'b0};
            end
            OP_SB, OP_SH, OP_SW: begin
                decode_o.uses_rs1 = 1'b1;
                decode_o.uses_rs2 = 1'b1;
                decode_o.imm = {{20{insn_i[31]}}, insn_i[31:25], insn_i[11:7]};
            end
            OP_ADD, OP_SUB, OP_SLL, OP_SLT, OP_SLTU, OP_XOR, OP_SRL,
            OP_SRA, OP_OR, OP_AND: begin
                decode_o.uses_rs1 = 1'b1;
                decode_o.uses_rs2 = 1'b1;
                decode_o.writes_rd = (insn_i[11:7] != 5'd0);
            end
            default: begin end
        endcase
        if (decode_o.uses_rs1) decode_o.rs1 = insn_i[19:15];
        if (decode_o.uses_rs2) decode_o.rs2 = insn_i[24:20];
        if (decode_o.writes_rd) decode_o.rd = insn_i[11:7];
    end
endmodule
`default_nettype wire
