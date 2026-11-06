`timescale 1ns/1ps
`default_nettype none
module tb_uart_rx #(parameter int unsigned DIVISOR=32'd8);
    logic clk=1'b0,rst=1'b1,rx=1'b1,reqv=1'b0,wr=1'b0,rspr=1'b0,pe=1'b1;
    logic [31:0] addr=32'h0,data=32'h0;
    logic [3:0] be=4'h0;
    wire logic reqr,rspv,err,tx,received,frame_error,busy;
    wire logic [31:0] rdata;
    wire logic [7:0] rbyte;
    uart_mmio #(.CLKS_PER_BIT(DIVISOR)) dut(.clk_i(clk),.rst_i(rst),.rx_i(rx),
        .req_valid_i(reqv),.req_write_i(wr),.req_addr_i(addr),.req_wdata_i(data[9:0]),.req_be_i(be),
        .req_ready_o(reqr),.rsp_valid_o(rspv),.rsp_err_o(err),.rsp_rdata_o(rdata),.rsp_ready_i(rspr),.tx_o(tx));
    uart_rx #(.CLKS_PER_BIT(DIVISOR)) direct(.clk_i(clk),.rst_i(rst),.enable_i(pe),.rx_i(rx),
        .data_valid_o(received),.frame_error_o(frame_error),.data_o(rbyte),.busy_o(busy));
    always #5 clk=~clk;
    integer fd,fields,checked=0,seed,divider;
    integer ir,iline,phase,iv,iw,iready,ipe;
    logic [31:0] ia,idata,predata,postdata;
    logic [3:0] ibe;
    logic [7:0] prebyte,postbyte;
    integer preq,prev,preerr,pretx,prerxv,preframe,prebusy;
    integer postq,postv,posterr,posttx,postrxv,postframe,postbusy;
    logic waiting=1'b0,next_waiting;
    logic [68:0] held_bus;
    string vectors;
    function automatic integer read_row;
        read_row=$fscanf(fd,"%h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h\n",
            ir,iline,phase,iv,ia,iw,idata,ibe,iready,ipe,
            preq,prev,predata,preerr,pretx,prerxv,prebyte,preframe,prebusy,
            postq,postv,postdata,posterr,posttx,postrxv,postbyte,postframe,postbusy);
    endfunction
    initial begin
        if(!$value$plusargs("SEED=%d",seed)||!$value$plusargs("DIV=%d",divider)||!$value$plusargs("VECTORS=%s",vectors))$fatal(1,"UART_RX_ARGUMENTS");
        if(divider!=DIVISOR)$fatal(1,"UART_RX_DIV_CONFIG");
        fd=$fopen(vectors,"r");if(fd==0)$fatal(1,"UART_RX_VECTOR_OPEN");fields=read_row();
        while(fields==28) begin
            if(phase<0 || phase>3)$fatal(1,"UART_RX_PHASE_CONFIG");
            @(negedge clk);rst=(ir!=0);reqv=(iv!=0);addr=ia;wr=(iw!=0);data=idata;be=ibe;rspr=(iready!=0);pe=(ipe!=0);
            #(phase);rx=(iline!=0);#(4-phase);
            if({reqr,rspv,rdata,err,tx,received,rbyte,frame_error,busy} !== {(preq!=0),(prev!=0),predata,(preerr!=0),(pretx!=0),(prerxv!=0),prebyte,(preframe!=0),(prebusy!=0)})
                $fatal(1,"UART_RX_MISMATCH phase=pre checked=%0d",checked);
            if(!rst && waiting && (!reqv || {addr,wr,data,be} !== held_bus))$fatal(1,"UART_RX_PRODUCER_VIOLATION");
            next_waiting=reqv && !reqr && !rst;held_bus={addr,wr,data,be};
            @(posedge clk);#1;
            if({reqr,rspv,rdata,err,tx,received,rbyte,frame_error,busy} !== {(postq!=0),(postv!=0),postdata,(posterr!=0),(posttx!=0),(postrxv!=0),postbyte,(postframe!=0),(postbusy!=0)})
                $fatal(1,"UART_RX_MISMATCH phase=post checked=%0d",checked);
            waiting=next_waiting;checked=checked+1;fields=read_row();
        end
        if(checked==0)$fatal(1,"UART_RX_EMPTY_VECTORS");
        if(fields>0 || !$feof(fd))$fatal(1,"UART_RX_MALFORMED_VECTOR");
        $display("UART_RX_SIM_PASS div=%0d seed=%0d checked=%0d",divider,seed,checked);$finish;
    end
    initial begin #30000000;$fatal(1,"UART_RX_TIMEOUT");end
endmodule
module tb_uart_rx_default;tb_uart_rx #(.DIVISOR(32'd868)) body();endmodule
module tb_uart_rx_odd;tb_uart_rx #(.DIVISOR(32'd7)) body();endmodule
`default_nettype wire
