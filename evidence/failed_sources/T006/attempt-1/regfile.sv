`default_nettype none
module regfile (
    input wire logic clk_i,
    input wire logic rst_i,
    input wire logic write_en_i,
    input wire logic [4:0] write_addr_i,
    input wire logic [31:0] write_data_i,
    input wire logic [4:0] read_addr_a_i,
    input wire logic [4:0] read_addr_b_i,
    output logic [31:0] read_data_a_o,
    output logic [31:0] read_data_b_o
);
    // x0 has no storage element. Architectural state changes only on clk_i.
    logic [31:0] registers [31:1];
    always_ff @(posedge clk_i) begin
        if (rst_i) begin
            for (int unsigned index = 32'd1; index < 32'd32; index = index + 32'd1)
                registers[index] <= 32'h0000_0000;
        end else if (write_en_i && (write_addr_i != 5'd0)) begin
            registers[write_addr_i] <= write_data_i;
        end
    end

    // WB-to-ID bypass precedes stored data, but can never override x0/reset.
    always_comb begin
        read_data_a_o = 32'h0000_0000;
        read_data_b_o = 32'h0000_0000;
        if (!rst_i) begin
            if (read_addr_a_i != 5'd0) begin
                if (write_en_i && (write_addr_i == read_addr_a_i))
                    read_data_a_o = write_data_i;
                else
                    read_data_a_o = registers[read_addr_a_i];
            end
            if (read_addr_b_i != 5'd0) begin
                if (write_en_i && (write_addr_i == read_addr_b_i))
                    read_data_b_o = write_data_i;
                else
                    read_data_b_o = registers[read_addr_b_i];
            end
        end
    end
endmodule
`default_nettype wire
