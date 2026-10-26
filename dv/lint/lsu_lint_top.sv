`default_nettype none
module lsu_lint_top (
    input wire logic clk_i, capture_i, result_select_i,
    input wire logic [1:0] operand_i,
    input wire logic [31:0] data_i,
    input wire rv32_pkg::op_t op_i,
    output wire logic [31:0] data_o,
    output wire logic [3:0] byte_enable_o,
    output wire logic write_o, misaligned_o, supported_o
);
    logic [1:0] addr;
    logic [31:0] store_data, read_word;
    wire logic [31:0] load_data, store_word;
    always_ff @(posedge clk_i) begin
        if (capture_i) begin
            case (operand_i)
                2'b00: addr <= data_i[1:0];
                2'b01: store_data <= data_i;
                2'b10: read_word <= data_i;
                default: begin end
            endcase
        end
    end
    lsu dut (.op_i(op_i), .byte_offset_i(addr), .store_data_i(store_data), .read_word_i(read_word),
        .load_data_o(load_data), .store_word_o(store_word), .byte_enable_o(byte_enable_o),
        .write_o(write_o), .misaligned_o(misaligned_o), .supported_o(supported_o));
    assign data_o = result_select_i ? store_word : load_data;
endmodule
`default_nettype wire
