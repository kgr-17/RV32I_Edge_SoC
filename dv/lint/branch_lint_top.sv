`default_nettype none
// Capture four independent operand words through one test port, reducing the
// physical I/O of this synthesis probe without constraining DUT input values.
module branch_lint_top (
    input wire logic clk_i, capture_i,
    input wire logic [1:0] operand_i,
    input wire logic [31:0] data_i,
    input wire rv32_pkg::op_t op_i,
    output wire logic [31:0] target_o,
    output wire logic taken_o, misaligned_o, supported_o
);
    logic [31:0] pc, rs1, rs2, imm;
    always_ff @(posedge clk_i) begin
        if (capture_i) begin
            case (operand_i)
                2'b00: pc <= data_i;
                2'b01: rs1 <= data_i;
                2'b10: rs2 <= data_i;
                2'b11: imm <= data_i;
                default: begin end
            endcase
        end
    end
    branch_unit dut (.op_i(op_i), .pc_i(pc), .rs1_i(rs1), .rs2_i(rs2), .imm_i(imm),
        .target_o(target_o), .taken_o(taken_o), .misaligned_o(misaligned_o), .supported_o(supported_o));
endmodule
`default_nettype wire
