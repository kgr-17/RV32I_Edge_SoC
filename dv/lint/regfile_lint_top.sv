`default_nettype none
// Synthesis probe: both read cones observable through a selected 32-bit port.
// Functional DV instantiates regfile directly and checks both ports together.
module regfile_lint_top (
    input wire logic clk_i, rst_i, write_en_i, read_select_i,
    input wire logic [4:0] write_addr_i, read_addr_a_i, read_addr_b_i,
    input wire logic [31:0] write_data_i,
    output wire logic [31:0] read_data_o
);
    wire logic [31:0] data_a;
    wire logic [31:0] data_b;
    regfile dut (.clk_i(clk_i), .rst_i(rst_i), .write_en_i(write_en_i),
        .write_addr_i(write_addr_i), .write_data_i(write_data_i),
        .read_addr_a_i(read_addr_a_i), .read_addr_b_i(read_addr_b_i),
        .read_data_a_o(data_a), .read_data_b_o(data_b));
    assign read_data_o = read_select_i ? data_b : data_a;
endmodule
`default_nettype wire
