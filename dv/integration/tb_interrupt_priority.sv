`timescale 1ns/1ps
`default_nettype none
module tb_interrupt_priority #(parameter int unsigned DIVISOR=32'd8);
    logic clk=1'b0,arst=1'b1,rx=1'b1;
    logic [15:0] switches=16'h0000;
    wire logic rst,tx,rv,rdw,mv,mw,fv;
    wire logic [15:0] leds;
    wire logic [63:0] order;
    wire logic [31:0] pc,insn,np,rddata,ma,md,mread,fpc,fi,ftval;
    wire logic [4:0] rd;
    wire logic [3:0] be,fc;
    wire logic tv,cv,cr,cw;
    wire logic [63:0] to;
    wire logic [31:0] tp,ti,tc,tt,tgt,cd,nd;
    wire logic [11:0] ca;
    logic edge_irq;
    logic [3:0] gates=4'b0000,hold_gates=4'b0000;
    integer unsigned lfsr=32'd1;
    logic drop=1'b0;
    integer cancel_state=0,cancel_wait=0,canceled=0;

    logic [31:0] signature_addr;

    reset_sync boundary(.clk_i(clk),.arst_i(arst),.rst_o(rst));
    irq_wait_soc #(.ENABLE_TRAPS(1'b1),.ROM_INIT_FILE("irq_boot.mem"),.UART_CLKS_PER_BIT(DIVISOR)) dut(.clk_i(clk),.rst_i(rst),.rx_i(rx),.gates_i(gates),.irq_drop_i(drop),.switches_i(switches),.tx_o(tx),.leds_o(leds),
        .retire_valid_o(rv),.retire_order_o(order),.retire_pc_o(pc),.retire_next_pc_o(np),.retire_insn_o(insn),
        .retire_rd_write_o(rdw),.retire_rd_o(rd),.retire_rd_wdata_o(rddata),.retire_mem_valid_o(mv),.retire_mem_write_o(mw),
        .retire_mem_addr_o(ma),.retire_mem_be_o(be),.retire_mem_wdata_o(md),.retire_mem_rdata_o(mread),
        .fault_valid_o(fv),.fault_pc_o(fpc),.fault_insn_o(fi),.fault_code_o(fc),.fault_tval_o(ftval),.trap_valid_o(tv),.trap_order_o(to),.trap_pc_o(tp),.trap_insn_o(ti),.trap_cause_o(tc),.trap_tval_o(tt),.trap_target_o(tgt),.retire_csr_valid_o(cv),.retire_csr_read_o(cr),.retire_csr_write_o(cw),.retire_csr_addr_o(ca),.retire_csr_rdata_o(cd),.retire_csr_wdata_o(nd));
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
        edge_reset=rst;edge_irq=dut.irq;
        if(edge_reset)begin drop=1'b1;cancel_state=0;end
        else if(cancel_state==0 && dut.fabric_irq && dut.cpu.g_traps.csrs.mie_q && dut.cpu.g_traps.csrs.meie_q && dut.cpu.e_valid && dut.cpu.e.dec.illegal)begin drop=1'b0;cancel_state=1;end
        if(!edge_reset && dut.cpu.sync_trap && dut.cpu.irq_draining)canceled=canceled+1;
        #0.1;edge_irq=dut.irq;
        lfsr={lfsr[30:0],lfsr[31]^lfsr[21]^lfsr[1]^lfsr[0]};
        gates=edge_reset ? 4'b0000 : (((rows%127<25) ? 4'b0000 : lfsr[3:0]) | hold_gates);
        #1;
        hold_gates=edge_reset ? 4'b0000 : { (dut.fds && gates[3] && !dut.dsr),
            (dut.dv && gates[2] && !dut.fdr),(dut.fis && gates[1] && !dut.irdy),(dut.iv && gates[0] && !dut.fir)};

        if(!edge_reset && iwait && (!dut.iv || dut.ia !== held_i))$fatal(1,"IRQ_I_PRODUCER_HOLD");
        if(!edge_reset && dwait && (!dut.dv || {dut.da,dut.dw,dut.dd,dut.db} !== held_d))$fatal(1,"IRQ_D_PRODUCER_HOLD");
        next_iwait=dut.iv && !dut.ir && !edge_reset;next_dwait=dut.dv && !dut.dr && !edge_reset;
        held_i=dut.ia;held_d={dut.da,dut.dw,dut.dd,dut.db};
        $fwrite(fd,"%h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h ",
            epoch,rows,edge_reset,rx,switches,dut.iv,dut.ir,dut.ia,dut.is,dut.irdy,dut.idata,dut.ie,
            dut.dv,dut.dr,dut.da,dut.dw,dut.dd,dut.db,dut.ds,dut.dsr,dut.ddata,dut.de,tx,leds);
        @(posedge clk);#1;
        if(edge_reset && (rv || fv))$fatal(1,"IRQ_RESET_VISIBLE_EFFECT");
        $fwrite(fd,"%h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h ",
            tx,leds,rv,order,pc,insn,np,rdw,rd,rddata,mv,mw,ma,be,md,mread,fv,fpc,fi,fc,ftval);
        $fwrite(fd,"%h %h %h %h %h %h %h %h %h %h %h %h %h %h %h ",
            edge_irq,dut.irq,tv,to,tp,ti,tc,tt,tgt,cv,ca,cr,cw,cd,nd);
        $fwrite(fd,"%h %h\n",gates,drop);
        iwait=next_iwait;dwait=next_dwait;rows=rows+1;
    endtask
    initial begin
        if(!$value$plusargs("SEED=%d",seed)||!$value$plusargs("TRACE=%s",trace_path))$fatal(1,"IRQ_ARGUMENTS");
        if(!$value$plusargs("SIG=%h",signature_addr))$fatal(1,"IRQ_SIGNATURE_ARGUMENT");
        fd=$fopen(trace_path,"w");if(fd==0)$fatal(1,"IRQ_TRACE_OPEN");
        lfsr=32'(seed);
        switches=(seed==1) ? 16'h5aa5 : 16'ha55a;
        for(phase=0;phase<2;phase=phase+1) begin
            repeat(4)tick(phase,1'b1,1'b1);
            cycle=0;
            while(!(rv && mw && ma==signature_addr && (md==32'h600d600d || md==32'hdeadbeef)) || cycle<3) begin
                tick(phase,1'b0,host_line(cycle));cycle=cycle+1;
                if(cycle>200000)$fatal(1,"IRQ_BOOT_TIMEOUT");
            end
            repeat(16)tick(phase,1'b0,1'b1);
        end
        $fclose(fd);
        if(canceled<2)$fatal(1,"IRQ_FAULT_PRIORITY_COVERAGE");
        $display("IRQ_FAULT_WON count=%0d",canceled);
        $display("IRQ_RUN_COMPLETE seed=%0d divisor=%0d rows=%0d phases=2",seed,DIVISOR,rows);$finish;
    end
    initial begin #5000000;$fatal(1,"IRQ_TEST_TIMEOUT");end
endmodule
module tb_interrupt_priority_default;tb_interrupt_priority #(.DIVISOR(32'd868)) body();endmodule
`default_nettype wire
