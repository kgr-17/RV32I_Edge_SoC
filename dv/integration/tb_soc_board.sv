`timescale 1ns/1ps
`default_nettype none
module tb_soc_board;
    localparam int unsigned DIVISOR=32'd868;
    logic clk=1'b0,arst=1'b1,rx=1'b1;
    logic [15:0] switches=16'h0000;
    wire logic rst,tx,rv,rdw,mv,mw,fv;
    wire logic [15:0] leds;
    wire logic [63:0] order;
    wire logic [31:0] pc,insn,np,rddata,ma,md,mread,fpc,fi,ftval;
    wire logic [4:0] rd;
    wire logic [3:0] be,fc;
    // Instantiate the actual canonical FPGA top, including its real reset chain.
    basys3_top board(.clk(clk),.btnC(arst),.sw(switches),.RsRx(rx),.led(leds),.RsTx(tx));
    assign rst=board.rst_s;
    assign rv=board.soc.retire_valid_o;
    assign order=board.soc.retire_order_o;
    assign pc=board.soc.retire_pc_o;
    assign np=board.soc.retire_next_pc_o;
    assign insn=board.soc.retire_insn_o;
    assign rdw=board.soc.retire_rd_write_o;
    assign rd=board.soc.retire_rd_o;
    assign rddata=board.soc.retire_rd_wdata_o;
    assign mv=board.soc.retire_mem_valid_o;
    assign mw=board.soc.retire_mem_write_o;
    assign ma=board.soc.retire_mem_addr_o;
    assign be=board.soc.retire_mem_be_o;
    assign md=board.soc.retire_mem_wdata_o;
    assign mread=board.soc.retire_mem_rdata_o;
    assign fv=board.soc.fault_valid_o;
    assign fpc=board.soc.fault_pc_o;
    assign fi=board.soc.fault_insn_o;
    assign fc=board.soc.fault_code_o;
    assign ftval=board.soc.fault_tval_o;
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
        if(!edge_reset && iwait && (!board.soc.iv || board.soc.ia !== held_i))$fatal(1,"SOC_I_PRODUCER_HOLD");
        if(!edge_reset && dwait && (!board.soc.dv || {board.soc.da,board.soc.dw,board.soc.dd,board.soc.db} !== held_d))$fatal(1,"SOC_D_PRODUCER_HOLD");
        next_iwait=board.soc.iv && !board.soc.ir && !edge_reset;next_dwait=board.soc.dv && !board.soc.dr && !edge_reset;
        held_i=board.soc.ia;held_d={board.soc.da,board.soc.dw,board.soc.dd,board.soc.db};
        $fwrite(fd,"%h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h ",
            epoch,rows,edge_reset,rx,switches,board.soc.iv,board.soc.ir,board.soc.ia,board.soc.is,board.soc.irdy,board.soc.idata,board.soc.ie,
            board.soc.dv,board.soc.dr,board.soc.da,board.soc.dw,board.soc.dd,board.soc.db,board.soc.ds,board.soc.dsr,board.soc.ddata,board.soc.de,tx,leds);
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
`default_nettype wire
