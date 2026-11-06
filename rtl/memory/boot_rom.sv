`default_nettype none
// 64KiB, two synchronous read ports on the one SoC clock. Word addresses.
module boot_rom #(
    parameter string INIT_FILE = "rom_init.mem"
) (
    input wire logic clk_i, rst_i,
    input wire logic a_en_i, b_en_i,
    input wire logic [13:0] a_addr_i, b_addr_i,
    output logic a_valid_o, b_valid_o,
    output logic [31:0] a_data_o, b_data_o
);
    (* rom_style = "block" *) logic [31:0] storage [0:16383];
    initial $readmemh(INIT_FILE, storage);
    always_ff @(posedge clk_i) begin
        if (rst_i) begin
            a_valid_o <= 1'b0; b_valid_o <= 1'b0;
            a_data_o <= 32'h00000000; b_data_o <= 32'h00000000;
        end else begin
            a_valid_o <= a_en_i; b_valid_o <= b_en_i;
            if (a_en_i) a_data_o <= storage[a_addr_i];
            if (b_en_i) b_data_o <= storage[b_addr_i];
        end
    end
endmodule
`default_nettype wire
