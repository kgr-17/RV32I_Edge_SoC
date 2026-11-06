`timescale 1ns/1ps
`default_nettype none
module tb_uart #(parameter int unsigned CLKS_PER_BIT=32'd4);
    logic clk=1'b0, rst=1'b1, reqv=1'b0, wr=1'b0, rspr=1'b0;
    logic [31:0] addr=32'h0, data=32'h0;
    logic [3:0] be=4'h0;
    wire logic reqr,rspv,err,tx;
    wire logic [31:0] rdata;
    logic pe=1'b1,pv=1'b0;
    logic [7:0] pdata=8'h00;
    wire logic pr,pb,pt;
    uart_mmio_tx #(.CLKS_PER_BIT(CLKS_PER_BIT)) dut (.clk_i(clk),.rst_i(rst),.req_valid_i(reqv),.req_write_i(wr),
        .req_addr_i(addr),.req_wdata_i(data[7:0]),.req_be_i(be),.req_ready_o(reqr),.rsp_valid_o(rspv),.rsp_err_o(err),.rsp_rdata_o(rdata),.rsp_ready_i(rspr),.tx_o(tx));
    uart_tx #(.CLKS_PER_BIT(CLKS_PER_BIT)) phy (.clk_i(clk),.rst_i(rst),.enable_i(pe),.data_valid_i(pv),.data_i(pdata),.data_ready_o(pr),.busy_o(pb),.tx_o(pt));
    always #5 clk=~clk;
    integer fd,fields,checked=0,seed,divider;
    integer ir,iv,iw,iready,ipe,ipv;
    logic [31:0] ia,idata,predata,postdata;
    logic [3:0] ibe;
    logic [7:0] ipdata;
    integer preq,prev,preerr,pretx,prepr,prepb,prept;
    integer postq,postv,posterr,posttx,postpr,postpb,postpt;
    logic phy_waiting=1'b0, bus_waiting=1'b0, next_phy_waiting, next_bus_waiting;
    logic [7:0] held_phy;
    logic [68:0] held_bus;
    string vectors;
    function automatic integer read_row;
        read_row=$fscanf(fd,"%h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h\n",
            ir,iv,ia,iw,idata,ibe,iready,ipe,ipv,ipdata,
            preq,prev,predata,preerr,pretx,prepr,prepb,prept,
            postq,postv,postdata,posterr,posttx,postpr,postpb,postpt);
    endfunction
    initial begin
        if (!$value$plusargs("SEED=%d",seed) || !$value$plusargs("DIV=%d",divider) || !$value$plusargs("VECTORS=%s",vectors))$fatal(1,"UART_ARGUMENTS");
        if(divider!=CLKS_PER_BIT)$fatal(1,"UART_DIV_CONFIG");
        fd=$fopen(vectors,"r");if(fd==0)$fatal(1,"UART_VECTOR_OPEN");
        fields=read_row();
        while(fields==26) begin
            @(negedge clk);
            rst=(ir!=0);reqv=(iv!=0);addr=ia;wr=(iw!=0);data=idata;be=ibe;rspr=(iready!=0);pe=(ipe!=0);pv=(ipv!=0);pdata=ipdata;
            #1;
            if({reqr,rspv,rdata,err,tx,pr,pb,pt} !== {(preq!=0),(prev!=0),predata,(preerr!=0),(pretx!=0),(prepr!=0),(prepb!=0),(prept!=0)})
                $fatal(1,"UART_MISMATCH phase=pre checked=%0d",checked);
            if(!rst && phy_waiting && (!pv || pdata !== held_phy))$fatal(1,"UART_PHY_PRODUCER_VIOLATION");
            if(!rst && bus_waiting && (!reqv || {addr,wr,data,be} !== held_bus))$fatal(1,"UART_BUS_PRODUCER_VIOLATION");
            next_phy_waiting=pv && !pr && !rst;held_phy=pdata;
            next_bus_waiting=reqv && !reqr && !rst;held_bus={addr,wr,data,be};
            @(posedge clk);#1;
            if({reqr,rspv,rdata,err,tx,pr,pb,pt} !== {(postq!=0),(postv!=0),postdata,(posterr!=0),(posttx!=0),(postpr!=0),(postpb!=0),(postpt!=0)})
                $fatal(1,"UART_MISMATCH phase=post checked=%0d",checked);
            phy_waiting=next_phy_waiting;bus_waiting=next_bus_waiting;
            checked=checked+1;fields=read_row();
        end
        if(checked==0)$fatal(1,"UART_EMPTY_VECTORS");
        if(fields>0 || !$feof(fd))$fatal(1,"UART_MALFORMED_VECTOR");
        $display("UART_SIM_PASS div=%0d seed=%0d checked=%0d",divider,seed,checked);$finish;
    end
    initial begin #10000000; $fatal(1,"UART_TEST_TIMEOUT"); end
endmodule
module tb_uart_default;
    tb_uart #(.CLKS_PER_BIT(32'd868)) body();
endmodule
`default_nettype wire
