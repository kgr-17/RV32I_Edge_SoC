`default_nettype none
module lsu (
    input wire rv32_pkg::op_t op_i,
    input wire logic [1:0] byte_offset_i,
    input wire logic [31:0] store_data_i, read_word_i,
    output logic [31:0] load_data_o, store_word_o,
    output logic [3:0] byte_enable_o,
    output logic write_o, misaligned_o, supported_o
);
    import rv32_pkg::*;
    logic [15:0] shifted;
    always_comb begin
        case (byte_offset_i)
            2'b00: shifted = read_word_i[15:0];
            2'b01: shifted = read_word_i[23:8];
            2'b10: shifted = read_word_i[31:16];
            2'b11: shifted = {8'b0, read_word_i[31:24]};
            default: shifted = 16'd0;
        endcase
        load_data_o = 32'd0;
        store_word_o = 32'd0;
        byte_enable_o = 4'b0000;
        write_o = 1'b0;
        misaligned_o = 1'b0;
        supported_o = 1'b1;
        case (op_i)
            OP_LB, OP_LBU: begin
                byte_enable_o = 4'b0001 << byte_offset_i;
                if (op_i == OP_LB) load_data_o = {{24{shifted[7]}}, shifted[7:0]};
                else load_data_o = {24'b0, shifted[7:0]};
            end
            OP_LH, OP_LHU: begin
                misaligned_o = byte_offset_i[0];
                byte_enable_o = 4'b0011 << byte_offset_i;
                if (op_i == OP_LH) load_data_o = {{16{shifted[15]}}, shifted[15:0]};
                else load_data_o = {16'b0, shifted[15:0]};
            end
            OP_LW: begin
                misaligned_o = (byte_offset_i != 2'b00);
                byte_enable_o = 4'b1111;
                load_data_o = read_word_i;
            end
            OP_SB: begin
                write_o = 1'b1;
                byte_enable_o = 4'b0001 << byte_offset_i;
                store_word_o = {24'b0, store_data_i[7:0]} << {byte_offset_i, 3'b000};
            end
            OP_SH: begin
                write_o = 1'b1;
                misaligned_o = byte_offset_i[0];
                byte_enable_o = 4'b0011 << byte_offset_i;
                store_word_o = {16'b0, store_data_i[15:0]} << {byte_offset_i, 3'b000};
            end
            OP_SW: begin
                write_o = 1'b1;
                misaligned_o = (byte_offset_i != 2'b00);
                byte_enable_o = 4'b1111;
                store_word_o = store_data_i;
            end
            default: supported_o = 1'b0;
        endcase
        if (misaligned_o) begin
            load_data_o = 32'd0;
            store_word_o = 32'd0;
            byte_enable_o = 4'b0000;
            write_o = 1'b0;
        end
    end
endmodule
`default_nettype wire
