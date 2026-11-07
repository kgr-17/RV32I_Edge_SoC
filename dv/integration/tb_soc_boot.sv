`timescale 1ns/1ps
`default_nettype none
module tb_soc_boot #(parameter int unsigned DIVISOR=32'd8);
    logic clk=1'b0,arst=1'b1,rx=1'b1;
    logic [15:0] switches=16'h0000;
    wire logic rst,tx,rv,rdw,mv,mw,fv;
    wire logic [15:0] leds;
    wire logic [63:0] order;
    wire logic [31:0] pc,insn,np,rddata,ma,md,mread,fpc,fi,ftval;
    wire logic [4:0] rd;
    wire logic [3:0] be,fc;
    reset_sync boundary(.clk_i(clk),.arst_i(arst),.rst_o(rst));
    edge_soc #(.UART_CLKS_PER_BIT(DIVISOR)) dut(.clk_i(clk),.rst_i(rst),.rx_i(rx),.switches_i(switches),.tx_o(tx),.leds_o(leds),
        .retire_valid_o(rv),.retire_order_o(order),.retire_pc_o(pc),.retire_next_pc_o(np),.retire_insn_o(insn),
        .retire_rd_write_o(rdw),.retire_rd_o(rd),.retire_rd_wdata_o(rddata),.retire_mem_valid_o(mv),.retire_mem_write_o(mw),
        .retire_mem_addr_o(ma),.retire_mem_be_o(be),.retire_mem_wdata_o(md),.retire_mem_rdata_o(mread),
        .fault_valid_o(fv),.fault_pc_o(fpc),.fault_insn_o(fi),.fault_code_o(fc),.fault_tval_o(ftval));
    always #5 clk=~clk;
    integer fd,seed,rows=0,phase,cycle;
    string trace_path;
    logic edge_reset,iwait=1'b0,dwait=1'b0,next_iwait,next_dwait;
    logic [31:0] held_i;
    logic [68:0] held_d;
    function automatic logic host_line(input integer tick_index);
        logic [9:0] frame;
        integer bit_index;
        begin
            frame={1'b1,8'h41,1'b0};
            if(tick_index<200 || tick_index>=200+10*DIVISOR) host_line=1'b1;
            else begin bit_index=(tick_index-200)/DIVISOR;host_line=frame[bit_index];end
        end
    endfunction
    task automatic tick(input integer epoch,input logic button,input logic line);
        @(negedge clk);#1;arst=button;rx=line;#2;
        edge_reset=rst;
        if(!edge_reset && iwait && (!dut.iv || dut.ia !== held_i))$fatal(1,"SOC_I_PRODUCER_HOLD");
        if(!edge_reset && dwait && (!dut.dv || {dut.da,dut.dw,dut.dd,dut.db} !== held_d))$fatal(1,"SOC_D_PRODUCER_HOLD");
        next_iwait=dut.iv && !dut.ir && !edge_reset;next_dwait=dut.dv && !dut.dr && !edge_reset;
        held_i=dut.ia;held_d={dut.da,dut.dw,dut.dd,dut.db};
        $fwrite(fd,"%h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h ",
            epoch,rows,edge_reset,rx,switches,dut.iv,dut.ir,dut.ia,dut.is,dut.irdy,dut.idata,dut.ie,
            dut.dv,dut.dr,dut.da,dut.dw,dut.dd,dut.db,dut.ds,dut.dsr,dut.ddata,dut.de,tx,leds);
        @(posedge clk);#1;
        if(edge_reset && (rv || fv))$fatal(1,"SOC_RESET_VISIBLE_EFFECT");
        $fwrite(fd,"%h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h\n",
            tx,leds,rv,order,pc,insn,np,rdw,rd,rddata,mv,mw,ma,be,md,mread,fv,fpc,fi,fc,ftval);
        iwait=next_iwait;dwait=next_dwait;rows=rows+1;
    endtask
    initial begin
        if(!$value$plusargs("SEED=%d",seed)||!$value$plusargs("TRACE=%s",trace_path))$fatal(1,"SOC_ARGUMENTS");
        fd=$fopen(trace_path,"w");if(fd==0)$fatal(1,"SOC_TRACE_OPEN");
        switches=(seed==1) ? 16'h5aa5 : 16'ha55a;
        for(phase=0;phase<2;phase=phase+1) begin
            repeat(4)tick(phase,1'b1,1'b1);
            cycle=0;
            while(fv!==1'b1 || cycle<3) begin
                tick(phase,1'b0,host_line(cycle));cycle=cycle+1;
                if(cycle>200000)$fatal(1,"SOC_BOOT_TIMEOUT");
            end
            repeat(16)tick(phase,1'b0,1'b1);
        end
        $fclose(fd);
        $display("SOC_RUN_COMPLETE seed=%0d divisor=%0d rows=%0d phases=2",seed,DIVISOR,rows);$finish;
    end
    initial begin #5000000;$fatal(1,"SOC_TEST_TIMEOUT");end
endmodule
module tb_soc_boot_default;tb_soc_boot #(.DIVISOR(32'd868)) body();endmodule
`default_nettype wire
