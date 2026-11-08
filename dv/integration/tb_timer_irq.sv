`timescale 1ns/1ps
`default_nettype none
module tb_timer_irq;
    logic clk=1'b0,rst=1'b1;
    logic [15:0] switches=16'h0000;
    logic gv=1'b0,gw=1'b0,gr=1'b0,tv=1'b0,tw=1'b0,tr=1'b0;
    logic [31:0] ga=32'h0,gd=32'h0,ta=32'h0,td=32'h0;
    logic [3:0] gb=4'h0,tb=4'h0;
    wire logic gq,gs,ge,tq,ts,te;
    wire logic [31:0] gdata,tdata;
    wire logic [15:0] leds;
    wire logic irq;
    integer preirq,postirq;
    gpio g(.clk_i(clk),.rst_i(rst),.switches_i(switches),.leds_o(leds),.req_valid_i(gv),.req_write_i(gw),
        .req_addr_i(ga),.req_wdata_i(gd[15:0]),.req_be_i(gb),.req_ready_o(gq),.rsp_valid_o(gs),.rsp_err_o(ge),.rsp_rdata_o(gdata),.rsp_ready_i(gr));
    timer #(.ENABLE_IRQ(1'b1)) t(.clk_i(clk),.rst_i(rst),.req_valid_i(tv),.req_write_i(tw),.req_addr_i(ta),.req_wdata_i(td),.req_be_i(tb),
        .req_ready_o(tq),.rsp_valid_o(ts),.rsp_err_o(te),.rsp_rdata_o(tdata),.rsp_ready_i(tr),.irq_o(irq));
    always #5 clk=~clk;
    integer fd,fields,checked=0,seed,ir,igv,igw,igr,itv,itw,itr;
    logic [15:0] isw,preled,postled;
    logic [31:0] iga,igd,ita,itd,pregd,pretd,postgd,posttd;
    logic [3:0] igb,itb;
    integer pregq,pregs,prege,pretq,prets,prete,postgq,postgs,postge,posttq,postts,postte;
    logic gwait=1'b0,twait=1'b0,next_gwait,next_twait;
    logic [68:0] gheld,theld;
    string vectors;
    function automatic integer read_row;
        read_row=$fscanf(fd,"%h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h\n",
            ir,isw,igv,iga,igw,igd,igb,igr,itv,ita,itw,itd,itb,itr,
            pregq,pregs,pregd,prege,preled,pretq,prets,pretd,prete,
            postgq,postgs,postgd,postge,postled,posttq,postts,posttd,postte,preirq,postirq);
    endfunction
    initial begin
        if(!$value$plusargs("SEED=%d",seed)||!$value$plusargs("VECTORS=%s",vectors))$fatal(1,"TIMER_IRQ_ARGUMENTS");
        fd=$fopen(vectors,"r");if(fd==0)$fatal(1,"TIMER_IRQ_VECTOR_OPEN");fields=read_row();
        while(fields==34) begin
            @(negedge clk);rst=(ir!=0);gv=(igv!=0);ga=iga;gw=(igw!=0);gd=igd;gb=igb;gr=(igr!=0);
            tv=(itv!=0);ta=ita;tw=(itw!=0);td=itd;tb=itb;tr=(itr!=0);#2;switches=isw;#2;
            if({gq,gs,gdata,ge,leds,tq,ts,tdata,te} !== {(pregq!=0),(pregs!=0),pregd,(prege!=0),preled,(pretq!=0),(prets!=0),pretd,(prete!=0)})
                $fatal(1,"TIMER_IRQ_MISMATCH phase=pre checked=%0d",checked);
            if(irq !== (preirq!=0))$fatal(1,"TIMER_IRQ_MISMATCH phase=pre checked=%0d",checked);
            if(!rst && gwait && (!gv || {ga,gw,gd,gb} !== gheld))$fatal(1,"TIMER_IRQ_GPIO_PRODUCER_VIOLATION");
            if(!rst && twait && (!tv || {ta,tw,td,tb} !== theld))$fatal(1,"TIMER_IRQ_TIMER_PRODUCER_VIOLATION");
            next_gwait=gv && !gq && !rst;next_twait=tv && !tq && !rst;gheld={ga,gw,gd,gb};theld={ta,tw,td,tb};
            @(posedge clk);#1;
            if({gq,gs,gdata,ge,leds,tq,ts,tdata,te} !== {(postgq!=0),(postgs!=0),postgd,(postge!=0),postled,(posttq!=0),(postts!=0),posttd,(postte!=0)})
                $fatal(1,"TIMER_IRQ_MISMATCH phase=post checked=%0d",checked);
            if(irq !== (postirq!=0))$fatal(1,"TIMER_IRQ_MISMATCH phase=post checked=%0d",checked);
            gwait=next_gwait;twait=next_twait;checked=checked+1;fields=read_row();
        end
        if(checked==0)$fatal(1,"TIMER_IRQ_EMPTY_VECTORS");
        if(fields>0 || !$feof(fd))$fatal(1,"TIMER_IRQ_MALFORMED_VECTOR");
        $display("TIMER_IRQ_SIM_PASS seed=%0d checked=%0d",seed,checked);$finish;
    end
    initial begin #10000000;$fatal(1,"TIMER_IRQ_TIMEOUT");end
endmodule
`default_nettype wire
