`timescale 1ns/1ps
`default_nettype none
module tb_csr;
    logic clk=1'b0,rst=1'b1,irq=1'b0,sz=1'b0,rz=1'b0,commit=1'b0,trap=1'b0,mret=1'b0;
    logic [11:0] addr=12'd0;
    logic [2:0] op=3'd0;
    logic [31:0] data=32'd0,pc=32'd0,cause=32'd0,tval=32'd0,npc=32'd0,target=32'd0;
    logic eligible=1'b0,empty=1'b0,synchronous=1'b0,retire=1'b0;
    wire logic rd,wr,err,enabled,draining,block_fetch,irq_commit,boundary;
    wire logic [31:0] rdata,wdata,vector,epc,resume_pc;
    csr_file dut(.clk_i(clk),.rst_i(rst),.irq_external_i(irq),.addr_i(addr),.op_i(op),.operand_i(data),.source_zero_i(sz),.rd_zero_i(rz),.commit_i(commit),
        .trap_i(trap),.mret_i(mret),.trap_pc_i(pc[31:2]),.trap_cause_i(cause),.trap_tval_i(tval),.read_o(rd),.write_o(wr),.error_o(err),.rdata_o(rdata),.wdata_o(wdata),.mtvec_o(vector),.mepc_o(epc),.irq_enabled_o(enabled));
    trap_control control(.clk_i(clk),.rst_i(rst),.eligible_i(eligible),.empty_i(empty),.sync_trap_i(synchronous),.retire_i(retire),.retire_next_pc_i(npc),.trap_target_i(target),
        .draining_o(draining),.block_fetch_o(block_fetch),.irq_commit_o(irq_commit),.boundary_o(boundary),.resume_pc_o(resume_pc));
    always #5 clk=~clk;
    integer fd,fields,checked=0,seed,values[0:44];
    string vectors;
    function automatic integer read_row;
        read_row=$fscanf(fd,"%h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h\n",
            values[0],values[1],values[2],values[3],values[4],values[5],values[6],values[7],values[8],values[9],values[10],values[11],values[12],values[13],values[14],values[15],values[16],values[17],values[18],
            values[19],values[20],values[21],values[22],values[23],values[24],values[25],values[26],values[27],values[28],values[29],values[30],values[31],values[32],values[33],values[34],values[35],values[36],values[37],values[38],values[39],values[40],values[41],values[42],values[43],values[44]);
    endfunction
    task automatic check_outputs(input integer offset,input string phase);
        if({rd,wr,err,rdata,wdata,vector,epc,enabled,draining,block_fetch,irq_commit,boundary,resume_pc} !==
           {(values[offset]!=0),(values[offset+1]!=0),(values[offset+2]!=0),values[offset+3],values[offset+4],values[offset+5],values[offset+6],(values[offset+7]!=0),(values[offset+8]!=0),(values[offset+9]!=0),(values[offset+10]!=0),(values[offset+11]!=0),values[offset+12]})
            $fatal(1,"CSR_MISMATCH phase=%s checked=%0d",phase,checked);
    endtask
    initial begin
        if(!$value$plusargs("SEED=%d",seed)||!$value$plusargs("VECTORS=%s",vectors))$fatal(1,"CSR_ARGUMENTS");
        fd=$fopen(vectors,"r");if(fd==0)$fatal(1,"CSR_VECTOR_OPEN");fields=read_row();
        while(fields==45) begin
            @(negedge clk);rst=(values[0]!=0);irq=(values[1]!=0);addr=values[2][11:0];op=values[3][2:0];data=values[4];
            sz=(values[5]!=0);rz=(values[6]!=0);commit=(values[7]!=0);trap=(values[8]!=0);mret=(values[9]!=0);pc=values[10];cause=values[11];tval=values[12];
            eligible=(values[13]!=0);empty=(values[14]!=0);synchronous=(values[15]!=0);retire=(values[16]!=0);npc=values[17];target=values[18];
            #4;check_outputs(19,"pre");@(posedge clk);#1;check_outputs(32,"post");checked=checked+1;fields=read_row();
        end
        if(checked==0)$fatal(1,"CSR_EMPTY_VECTORS");if(fields>0 || !$feof(fd))$fatal(1,"CSR_MALFORMED_VECTOR");
        $display("CSR_SIM_PASS seed=%0d checked=%0d",seed,checked);$finish;
    end
    initial begin #10000000;$fatal(1,"CSR_TIMEOUT");end
endmodule
`default_nettype wire
