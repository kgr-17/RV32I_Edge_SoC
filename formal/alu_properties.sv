`default_nettype none
module formal_alu (
    input wire rv32_pkg::op_t op_i,
    input wire logic [31:0] a_i,b_i
);
    import rv32_pkg::*;
    wire logic [31:0] result;
    wire logic supported;
    alu dut (.op_i(op_i),.a_i(a_i),.b_i(b_i),.result_o(result),.supported_o(supported));
    // Contract-derived algebraic invariants, not a second copy of the ALU case.
    always_comb begin
        if (op_i==OP_ADD || op_i==OP_ADDI) begin
            assert (supported);
            assert ((result-a_i)==b_i);
        end
        if (op_i==OP_SUB) begin
            assert (supported);
            assert ((result+b_i)==a_i);
        end
        if (op_i==OP_XOR || op_i==OP_XORI) begin
            assert (supported);
            assert ((result^a_i)==b_i);
        end
        if ((op_i==OP_SRA || op_i==OP_SRAI) && supported)
            assert (result[31]==a_i[31]);
        if ((op_i==OP_SLL || op_i==OP_SLLI || op_i==OP_SRL || op_i==OP_SRLI ||
             op_i==OP_SRA || op_i==OP_SRAI) && b_i[4:0]==5'd0) begin
            assert (supported);
            assert (result==a_i);
        end
`ifdef FORMAL_NEGATIVE
        assert (a_i!=a_i); // Deliberate counterexample, never a production change.
`endif
    end
endmodule
`default_nettype wire
