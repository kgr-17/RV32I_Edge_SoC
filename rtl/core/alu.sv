`default_nettype none
module alu (
    input wire rv32_pkg::op_t op_i,
    input wire logic [31:0] a_i,
    input wire logic [31:0] b_i,
    output logic [31:0] result_o,
    output logic supported_o
);
    import rv32_pkg::*;

    // Operand selection belongs to the caller; both register/immediate forms
    // share arithmetic. Shift amounts always use the low five operand bits.
    always_comb begin
        result_o = 32'h0000_0000;
        supported_o = 1'b1;
        case (op_i)
            OP_ADD, OP_ADDI: result_o = a_i + b_i;
            OP_SUB: result_o = a_i - b_i;
            OP_SLL, OP_SLLI: result_o = a_i << b_i[4:0];
            OP_SLT, OP_SLTI: result_o = {31'b0, ($signed(a_i) < $signed(b_i))};
            OP_SLTU, OP_SLTIU: result_o = {31'b0, (a_i < b_i)};
            OP_XOR, OP_XORI: result_o = a_i ^ b_i;
            OP_SRL, OP_SRLI: result_o = a_i >> b_i[4:0];
            OP_SRA, OP_SRAI: result_o = $signed(a_i) >>> b_i[4:0];
            OP_OR, OP_ORI: result_o = a_i | b_i;
            OP_AND, OP_ANDI: result_o = a_i & b_i;
            default: supported_o = 1'b0;
        endcase
    end
endmodule
`default_nettype wire
