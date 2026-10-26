`default_nettype none
module regfile (
    input wire logic clk_i,
    input wire logic rst_i,
    input wire logic write_en_i,
    input wire logic [4:0] write_addr_i,
    input wire logic [31:0] write_data_i,
    input wire logic [4:0] read_addr_a_i,
    input wire logic [4:0] read_addr_b_i,
    output wire logic [31:0] read_data_a_o,
    output wire logic [31:0] read_data_b_o
);
    // Explicit word/read hierarchy keeps the synthesis netlist partitioned.
    // x0 has no storage; every stored word still uses the same rising clock.
    wire logic [31:0] registers [31:1];
    for (genvar index = 32'd1; index < 32'd32; index = index + 32'd1) begin : g_word
        wire logic selected;
        assign selected = write_en_i && (write_addr_i == index[4:0]);
        rv32_regfile_word word (.clk_i(clk_i), .rst_i(rst_i), .write_en_i(selected),
            .data_i(write_data_i), .data_o(registers[index]));
    end
    rv32_regfile_read port_a (.rst_i(rst_i), .write_en_i(write_en_i),
        .write_addr_i(write_addr_i), .write_data_i(write_data_i),
        .read_addr_i(read_addr_a_i), .registers_i(registers), .read_data_o(read_data_a_o));
    rv32_regfile_read port_b (.rst_i(rst_i), .write_en_i(write_en_i),
        .write_addr_i(write_addr_i), .write_data_i(write_data_i),
        .read_addr_i(read_addr_b_i), .registers_i(registers), .read_data_o(read_data_b_o));
endmodule

module rv32_regfile_word (
    input wire logic clk_i, rst_i, write_en_i,
    input wire logic [31:0] data_i,
    output logic [31:0] data_o
);
    always_ff @(posedge clk_i) begin
        if (rst_i) data_o <= 32'h0000_0000;
        else if (write_en_i) data_o <= data_i;
    end
endmodule

module rv32_regfile_read (
    input wire logic rst_i, write_en_i,
    input wire logic [4:0] write_addr_i,
    input wire logic [31:0] write_data_i,
    input wire logic [4:0] read_addr_i,
    input wire logic [31:0] registers_i [31:1],
    output logic [31:0] read_data_o
);
    // WB-to-ID bypass precedes stored data, but can never override x0/reset.
    always_comb begin
        read_data_o = 32'h0000_0000;
        if (!rst_i && (read_addr_i != 5'd0)) begin
            if (write_en_i && (write_addr_i == read_addr_i)) read_data_o = write_data_i;
            else read_data_o = registers_i[read_addr_i];
        end
    end
endmodule
`default_nettype wire
