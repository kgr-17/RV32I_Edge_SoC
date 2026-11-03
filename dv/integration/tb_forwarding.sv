`default_nettype none
module tb_forwarding;
    timeunit 1ns; timeprecision 1ps;
    logic [7:0] flags;
    logic [4:0] ra,rb,ex_rd,wb_rd;
    logic [31:0] ca,cb,ex_value,wb_value,a,b,ea,eb;
    logic [1:0] sa,sb,esa,esb;
    logic ba,bb,eba,ebb;
    integer vector_file,scanned,checked=0;
    integer unsigned seed,expected_count;
    string vector_path;
    forwarding_unit dut (.valid_i(flags[0]),.uses_a_i(flags[1]),.uses_b_i(flags[2]),
        .rs_a_i(ra),.rs_b_i(rb),.captured_a_i(ca),.captured_b_i(cb),
        .ex_valid_i(flags[3]),.ex_write_i(flags[4]),.ex_load_i(flags[5]),.ex_rd_i(ex_rd),.ex_value_i(ex_value),
        .wb_valid_i(flags[6]),.wb_write_i(flags[7]),.wb_rd_i(wb_rd),.wb_value_i(wb_value),
        .value_a_o(a),.value_b_o(b),.source_a_o(sa),.source_b_o(sb),.blocked_a_o(ba),.blocked_b_o(bb));
    initial begin
        if (!$value$plusargs("SEED=%d",seed)) $fatal(1,"Missing seed");
        if (!$value$plusargs("COUNT=%d",expected_count)||expected_count==0) $fatal(1,"Zero tests");
        if (!$value$plusargs("VECTORS=%s",vector_path)) $fatal(1,"Missing vectors");
        vector_file=$fopen(vector_path,"r");
        if (vector_file==0) $fatal(1,"Cannot read vectors");
        while (!$feof(vector_file)) begin
            scanned=$fscanf(vector_file,"%h %h %h %h %h %h %h %h %h %h %h %h %h %h %h\n",
                flags,ra,rb,ex_rd,wb_rd,ca,cb,ex_value,wb_value,ea,eb,esa,esb,eba,ebb);
            if (scanned==15) begin
                #1ns;
                if ({a,b,sa,sb,ba,bb}!=={ea,eb,esa,esb,eba,ebb})
                    $fatal(1,"FORWARDING_MISMATCH seed=%0d row=%0d flags=%h ra=%d rb=%d ex=%d wb=%d a=%h/%h b=%h/%h src=%h/%h wait=%h/%h",
                        seed,checked,flags,ra,rb,ex_rd,wb_rd,a,ea,b,eb,{sa,sb},{esa,esb},{ba,bb},{eba,ebb});
                checked=checked+1;
            end else if (scanned!=-1) $fatal(1,"Malformed forwarding input");
        end
        $fclose(vector_file);
        if (checked!=expected_count) $fatal(1,"Wrong count %0d != %0d",checked,expected_count);
        $display("FORWARDING_SIM_PASS seed=%0d checked=%0d",seed,checked);
        $finish;
    end
endmodule
`default_nettype wire
