`default_nettype none
module tb_branch;
    timeunit 1ns;
    timeprecision 1ps;
    logic [5:0] op=6'd0;
    logic [31:0] pc=32'd0, rs1=32'd0, rs2=32'd0, imm=32'd0;
    logic [31:0] target, expected_target;
    logic taken, bad, supported, expected_taken, expected_bad, expected_supported;
    integer vector_file, scanned;
    integer checked=0;
    integer unsigned seed, expected_count;
    string vector_path;
    branch_unit dut (.op_i(rv32_pkg::op_t'(op)), .pc_i(pc), .rs1_i(rs1), .rs2_i(rs2), .imm_i(imm),
        .target_o(target), .taken_o(taken), .misaligned_o(bad), .supported_o(supported));
    initial begin
        if (!$value$plusargs("SEED=%d",seed)) $fatal(1,"Missing seed");
        if (!$value$plusargs("COUNT=%d",expected_count)) $fatal(1,"Missing count");
        if (expected_count==0) $fatal(1,"Zero tests");
        if (!$value$plusargs("VECTORS=%s",vector_path)) $fatal(1,"Missing vectors");
        vector_file=$fopen(vector_path,"r");
        if (vector_file==0) $fatal(1,"Cannot read vectors");
        while (!$feof(vector_file)) begin
            scanned=$fscanf(vector_file,"%h %h %h %h %h %h %h %h %h\n",op,pc,rs1,rs2,imm,
                            expected_target,expected_taken,expected_bad,expected_supported);
            if (scanned==9) begin
                #1ns;
                if ({target,taken,bad,supported} !== {expected_target,expected_taken,expected_bad,expected_supported})
                    $fatal(1,"BRANCH_MISMATCH seed=%0d row=%0d op=%h target=%h/%h taken=%b/%b bad=%b/%b support=%b/%b",
                        seed,checked,op,target,expected_target,taken,expected_taken,bad,expected_bad,supported,expected_supported);
                checked=checked+1;
            end else if (scanned != -1) $fatal(1,"Malformed branch vector");
        end
        $fclose(vector_file);
        if (checked!=expected_count) $fatal(1,"Wrong count %0d != %0d",checked,expected_count);
        $display("BRANCH_SIM_PASS seed=%0d checked=%0d",seed,checked);
        $finish;
    end
endmodule
`default_nettype wire
