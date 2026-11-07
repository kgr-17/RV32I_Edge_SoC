`timescale 1ns/1ps
`default_nettype none
module tb_cdc;
    logic clk=1'b0,run_clock=1'b1,arst=1'b0,bit_in=1'b0;
    logic [31:0] data=32'h0;
    wire logic rst,bit_out;
    wire logic [15:0] word_out;
    wire logic [31:0] wide_out;
    reset_sync resetter(.clk_i(clk),.arst_i(arst),.rst_o(rst));
    input_sync #(.WIDTH(32'd1)) scalar(.clk_i(clk),.rst_i(rst),.async_i(bit_in),.sync_o(bit_out));
    input_sync #(.WIDTH(32'd16)) word_input(.clk_i(clk),.rst_i(rst),.async_i(data[15:0]),.sync_o(word_out));
    input_sync #(.WIDTH(32'd32)) wide_input(.clk_i(clk),.rst_i(rst),.async_i(data),.sync_o(wide_out));
    always #5 if(run_clock) clk=~clk;
    integer fd,fields,checked=0,seed,ir,pulse,phase,ibit,prerst,prebit,postrst,postbit;
    logic [31:0] idata,prewide,postwide;
    logic [15:0] preword,postword;
    string vectors;
    function automatic integer read_row;
        read_row=$fscanf(fd,"%h %h %h %h %h %h %h %h %h %h %h %h %h\n",
            ir,pulse,phase,idata,ibit,prerst,preword,prewide,prebit,postrst,postword,postwide,postbit);
    endfunction
    initial begin
        if(!$value$plusargs("SEED=%d",seed)||!$value$plusargs("VECTORS=%s",vectors))$fatal(1,"CDC_ARGUMENTS");
        #1;if(rst!==1'b1)$fatal(1,"CDC_INIT_RESET");
        repeat(6)@(negedge clk);run_clock=1'b0;
        #1;arst=1'b1;#0.2;if(rst!==1'b1)$fatal(1,"CDC_ASYNC_ASSERT");
        #1;arst=1'b0;#13;if(rst!==1'b1)$fatal(1,"CDC_STOPPED_RELEASE");
        run_clock=1'b1;
        fd=$fopen(vectors,"r");if(fd==0)$fatal(1,"CDC_VECTOR_OPEN");fields=read_row();
        while(fields==13) begin
            if(phase<0 || phase>3 || (pulse!=0 && ir!=0))$fatal(1,"CDC_PHASE_CONFIG");
            @(negedge clk);#(phase);arst=(ir!=0);data=idata;bit_in=(ibit!=0);
            #0.2;if(pulse!=0)arst=1'b1;#0.2;arst=(ir!=0);#(3.6-phase);
            if({rst,word_out,wide_out,bit_out} !== {(prerst!=0),preword,prewide,(prebit!=0)})$fatal(1,"CDC_MISMATCH phase=pre checked=%0d",checked);
            @(posedge clk);#1;
            if({rst,word_out,wide_out,bit_out} !== {(postrst!=0),postword,postwide,(postbit!=0)})$fatal(1,"CDC_MISMATCH phase=post checked=%0d",checked);
            checked=checked+1;fields=read_row();
        end
        if(checked==0)$fatal(1,"CDC_EMPTY_VECTORS");
        if(fields>0 || !$feof(fd))$fatal(1,"CDC_MALFORMED_VECTOR");
        $display("CDC_SIM_PASS seed=%0d checked=%0d",seed,checked);$finish;
    end
    initial begin #1000000;$fatal(1,"CDC_TIMEOUT");end
endmodule
module tb_cdc_bad_width;
    logic clk=1'b0;
    wire logic [32:0] result;
    input_sync #(.WIDTH(32'd33)) bad(.clk_i(clk),.rst_i(1'b1),.async_i(33'd0),.sync_o(result));
    initial begin #10;$fatal(1,"CDC_WIDTH_CHECK_MISSING");end
endmodule
`default_nettype wire
