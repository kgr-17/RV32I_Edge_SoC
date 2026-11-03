`default_nettype none
module tb_hazard;
    timeunit 1ns;timeprecision 1ps;
    logic [5:0] flags;
    logic [4:0] a,b,dest;
    logic wa,wb,stall,ea,eb,es;
    integer vector_file,scanned,checked=0;
    integer unsigned seed,expected_count;
    string vector_path;
    hazard_unit dut (.consumer_valid_i(flags[0]),.uses_a_i(flags[1]),.uses_b_i(flags[2]),.rs_a_i(a),.rs_b_i(b),
        .load_valid_i(flags[3]),.load_write_i(flags[4]),.load_is_load_i(flags[5]),.load_rd_i(dest),
        .wait_a_o(wa),.wait_b_o(wb),.stall_o(stall));
    initial begin
        if (!$value$plusargs("SEED=%d",seed)) $fatal(1,"Missing seed");
        if (!$value$plusargs("COUNT=%d",expected_count)||expected_count==0) $fatal(1,"Zero tests");
        if (!$value$plusargs("VECTORS=%s",vector_path)) $fatal(1,"Missing vectors");
        vector_file=$fopen(vector_path,"r");if(vector_file==0)$fatal(1,"Cannot read vectors");
        while (!$feof(vector_file)) begin
            scanned=$fscanf(vector_file,"%h %h %h %h %h %h %h\n",flags,a,b,dest,ea,eb,es);
            if(scanned==7)begin
                #1ns;if({wa,wb,stall}!=={ea,eb,es})$fatal(1,"HAZARD_MISMATCH seed=%0d row=%0d",seed,checked);
                checked=checked+1;
            end else if(scanned!=-1)$fatal(1,"Malformed hazard vectors");
        end
        $fclose(vector_file);if(checked!=expected_count)$fatal(1,"Wrong count %0d != %0d",checked,expected_count);
        $display("HAZARD_SIM_PASS seed=%0d checked=%0d",seed,checked);$finish;
    end
endmodule
`default_nettype wire
