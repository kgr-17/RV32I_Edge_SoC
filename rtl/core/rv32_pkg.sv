`default_nettype none
package rv32_pkg;
    // Stable internal operation IDs; no implied privileged/extension support.
    typedef enum logic [5:0] {
        OP_ILLEGAL = 6'd0,
        OP_LUI = 6'd1, OP_AUIPC = 6'd2, OP_JAL = 6'd3, OP_JALR = 6'd4,
        OP_BEQ = 6'd5, OP_BNE = 6'd6, OP_BLT = 6'd7, OP_BGE = 6'd8,
        OP_BLTU = 6'd9, OP_BGEU = 6'd10,
        OP_LB = 6'd11, OP_LH = 6'd12, OP_LW = 6'd13, OP_LBU = 6'd14, OP_LHU = 6'd15,
        OP_SB = 6'd16, OP_SH = 6'd17, OP_SW = 6'd18,
        OP_ADDI = 6'd19, OP_SLTI = 6'd20, OP_SLTIU = 6'd21,
        OP_XORI = 6'd22, OP_ORI = 6'd23, OP_ANDI = 6'd24,
        OP_SLLI = 6'd25, OP_SRLI = 6'd26, OP_SRAI = 6'd27,
        OP_ADD = 6'd28, OP_SUB = 6'd29, OP_SLL = 6'd30, OP_SLT = 6'd31,
        OP_SLTU = 6'd32, OP_XOR = 6'd33, OP_SRL = 6'd34, OP_SRA = 6'd35,
        OP_OR = 6'd36, OP_AND = 6'd37,
        OP_FENCE = 6'd38, OP_ECALL = 6'd39, OP_EBREAK = 6'd40
    } op_t;

    // Packed MSB->LSB interface, 57 bits. Immediate is already XLEN-wide.
    // Shift immediates contain zero-extended shamt, R/FENCE/SYSTEM contain 0.
    // writes_rd describes a real nonzero GPR destination, not memory effects.
    typedef struct packed {
        op_t op;
        logic [31:0] imm;
        logic [4:0] rs1;
        logic [4:0] rs2;
        logic [4:0] rd;
        logic uses_rs1;
        logic uses_rs2;
        logic writes_rd;
        logic illegal;
    } decode_t;
endpackage
`default_nettype wire
