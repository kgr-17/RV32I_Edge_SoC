`timescale 1ns/1ps
`default_nettype none
module tb_memories;
    logic clk=1'b0, rst=1'b1, ae=1'b0, be=1'b0, re=1'b0;
    logic [13:0] aa=14'h0, ba=14'h0, ra=14'h0;
    logic [3:0] mask=4'h0;
    logic [31:0] data=32'h0;
    wire pav,pbv,bav,bbv,rv;
    wire [31:0] pa,pb,boot_a,boot_b,ram_data;
    boot_rom #(.INIT_FILE("rom_pattern.mem")) pattern_rom (.clk_i(clk),.rst_i(rst),.a_en_i(ae),.b_en_i(be),.a_addr_i(aa),.b_addr_i(ba),.a_valid_o(pav),.b_valid_o(pbv),.a_data_o(pa),.b_data_o(pb));
    boot_rom actual_rom (.clk_i(clk),.rst_i(rst),.a_en_i(ae),.b_en_i(be),.a_addr_i(aa),.b_addr_i(ba),.a_valid_o(bav),.b_valid_o(bbv),.a_data_o(boot_a),.b_data_o(boot_b));
    data_ram ram (.clk_i(clk),.rst_i(rst),.en_i(re),.addr_i(ra),.write_be_i(mask),.write_data_i(data),.read_valid_o(rv),.read_data_o(ram_data));
    always #5 clk=~clk;
    integer fd,fields,checked=0,seed;
    integer r,xa,xb,xr,va,vb,vr;
    logic [13:0] ia,ib,ir;
    logic [3:0] imask;
    logic [31:0] idata,epa,epb,eba,ebb,eram;
    logic [162:0] prior_outputs;
    string vectors;
    initial begin
        if (!$value$plusargs("SEED=%d",seed) || !$value$plusargs("VECTORS=%s",vectors)) $fatal(1,"MEMORY_ARGUMENTS");
        fd=$fopen(vectors,"r");if(fd==0)$fatal(1,"MEMORY_VECTOR_OPEN");
        fields=$fscanf(fd,"%h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h\n",r,xa,ia,xb,ib,xr,ir,imask,idata,epa,epb,eba,ebb,eram,va,vb,vr);
        while(fields==17) begin
            @(negedge clk);
            rst=(r!=0);ae=(xa!=0);aa=ia;be=(xb!=0);ba=ib;re=(xr!=0);ra=ir;mask=imask;data=idata;
            #1;
            if(checked>0 && {pa,pb,boot_a,boot_b,ram_data,pav,pbv,rv} !== prior_outputs)
                $fatal(1,"MEMORY_NOT_SYNCHRONOUS checked=%0d",checked);
            @(posedge clk);#1;
            if({pa,pb,boot_a,boot_b,ram_data} !== {epa,epb,eba,ebb,eram} ||
                pav !== (va!=0) || pbv !== (vb!=0) || rv !== (vr!=0) || bav !== pav || bbv !== pbv)
                $fatal(1,"MEMORY_MISMATCH checked=%0d",checked);
            prior_outputs={pa,pb,boot_a,boot_b,ram_data,pav,pbv,rv};
            checked=checked+1;
            fields=$fscanf(fd,"%h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h\n",r,xa,ia,xb,ib,xr,ir,imask,idata,epa,epb,eba,ebb,eram,va,vb,vr);
        end
        if(checked==0)$fatal(1,"MEMORY_EMPTY_VECTORS");
        if(fields>0 || !$feof(fd))$fatal(1,"MEMORY_MALFORMED_VECTOR");
        $display("MEMORY_SIM_PASS seed=%0d checked=%0d",seed,checked);$finish;
    end
    initial begin #1000000; $fatal(1,"MEMORY_TEST_TIMEOUT"); end
endmodule
`default_nettype wire
