`default_nettype none
// 64KiB read-first synchronous RAM. The future fabric must gate writes at the
// successful RESPONSE handshake; these are primitive ports, not the local bus.
module data_ram (
    input wire logic clk_i, rst_i, en_i,
    input wire logic [13:0] addr_i,
    input wire logic [3:0] write_be_i,
    input wire logic [31:0] write_data_i,
    output logic read_valid_o,
    output logic [31:0] read_data_o
);
    // Explicit depth banking retains native byte enables at this address width.
    // This is a mapping choice; routed timing/power remain separate evidence.
    (* ram_style = "block", ram_decomp = "power" *) logic [31:0] storage [0:16383];
    integer word_index;
    initial begin
        for (word_index = 0; word_index < 16384; word_index = word_index + 1)
            storage[word_index] = 32'h00000000;
    end
    always_ff @(posedge clk_i) begin
        if (rst_i) begin
            read_valid_o <= 1'b0;
            read_data_o <= 32'h00000000;
        end else begin
            read_valid_o <= en_i;
            if (en_i) begin
                read_data_o <= storage[addr_i];
                for (integer lane = 0; lane < 4; lane = lane + 1)
                    if (write_be_i[lane]) storage[addr_i][lane*8 +: 8] <= write_data_i[lane*8 +: 8];
            end
        end
    end
endmodule
`default_nettype wire
