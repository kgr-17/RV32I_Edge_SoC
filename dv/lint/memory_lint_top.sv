`default_nettype none
module memory_lint_top (
    input wire logic clk_i, rst_i, a_en_i, b_en_i, ram_en_i,
    input wire logic [13:0] a_addr_i, b_addr_i, ram_addr_i,
    input wire logic [3:0] write_be_i,
    input wire logic [31:0] write_data_i,
    output wire logic a_valid_o, b_valid_o, ram_valid_o,
    output wire logic [31:0] a_data_o, b_data_o, ram_data_o
);
    boot_rom rom (.clk_i(clk_i), .rst_i(rst_i), .a_en_i(a_en_i), .b_en_i(b_en_i),
        .a_addr_i(a_addr_i), .b_addr_i(b_addr_i), .a_valid_o(a_valid_o), .b_valid_o(b_valid_o),
        .a_data_o(a_data_o), .b_data_o(b_data_o));
    data_ram ram (.clk_i(clk_i), .rst_i(rst_i), .en_i(ram_en_i), .addr_i(ram_addr_i),
        .write_be_i(write_be_i), .write_data_i(write_data_i), .read_valid_o(ram_valid_o), .read_data_o(ram_data_o));
endmodule
`default_nettype wire
