`default_nettype none
module tb_lsu;
    timeunit 1ns;
    timeprecision 1ps;
    logic [5:0] op=6'd0;
    logic [31:0] addr=32'd0, data=32'd0, word_data=32'd0;
    logic [31:0] load_data, store_word, expected_load, expected_store, expected_merge, merged;
    logic [3:0] be, expected_be;
    logic write_en, bad, supported, expected_write, expected_bad, expected_supported;
    integer vector_file, scanned;
    integer checked=0;
    integer unsigned seed, expected_count;
    string vector_path;
    lsu dut (.op_i(rv32_pkg::op_t'(op)), .byte_offset_i(addr[1:0]), .store_data_i(data), .read_word_i(word_data),
        .load_data_o(load_data), .store_word_o(store_word), .byte_enable_o(be),
        .write_o(write_en), .misaligned_o(bad), .supported_o(supported));
    initial begin
        if (!$value$plusargs("SEED=%d",seed)) $fatal(1,"Missing seed");
        if (!$value$plusargs("COUNT=%d",expected_count)) $fatal(1,"Missing count");
        if (expected_count==0) $fatal(1,"Zero tests");
        if (!$value$plusargs("VECTORS=%s",vector_path)) $fatal(1,"Missing vectors");
        vector_file=$fopen(vector_path,"r");
        if (vector_file==0) $fatal(1,"Cannot read vectors");
        while (!$feof(vector_file)) begin
            scanned=$fscanf(vector_file,"%h %h %h %h %h %h %h %h %h %h %h\n",op,addr,data,word_data,
                expected_load,expected_store,expected_be,expected_write,expected_bad,expected_supported,expected_merge);
            if (scanned==11) begin
                #1ns;
                merged=word_data;
                if (supported && write_en && !bad) begin
                    for (int unsigned lane=32'd0;lane<32'd4;lane=lane+32'd1)
                        if (be[lane]) merged[lane*32'd8 +: 8]=store_word[lane*32'd8 +: 8];
                end
                if ({load_data,store_word,be,write_en,bad,supported,merged} !==
                    {expected_load,expected_store,expected_be,expected_write,expected_bad,expected_supported,expected_merge})
                    $fatal(1,"LSU_MISMATCH seed=%0d row=%0d op=%h addr=%h load=%h/%h store=%h/%h be=%h/%h merged=%h/%h",
                        seed,checked,op,addr,load_data,expected_load,store_word,expected_store,be,expected_be,merged,expected_merge);
                checked=checked+1;
            end else if (scanned != -1) $fatal(1,"Malformed LSU vector");
        end
        $fclose(vector_file);
        if (checked!=expected_count) $fatal(1,"Wrong count %0d != %0d",checked,expected_count);
        $display("LSU_SIM_PASS seed=%0d checked=%0d",seed,checked);
        $finish;
    end
endmodule
`default_nettype wire
