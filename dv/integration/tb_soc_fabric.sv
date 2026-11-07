`timescale 1ns/1ps
`default_nettype none
module tb_soc_fabric;
    logic clk=1'b0,rst=1'b1,rx=1'b1;
    logic [15:0] sw=16'h0;
    logic iv=1'b0,irdy=1'b0,dv=1'b0,dw=1'b0,drdy=1'b0;
    logic [31:0] ia=32'd0,da=32'd0,dd=32'd0;
    logic [3:0] db=4'hf;
    wire logic ir,is,ie,dr,ds,de,tx;
    wire logic [31:0] idata,ddata;
    wire logic [15:0] leds;
    soc_fabric #(.ROM_INIT_FILE("fabric_pattern.mem"),.UART_CLKS_PER_BIT(32'd8)) dut(
        .clk_i(clk),.rst_i(rst),.rx_i(rx),.switches_i(sw),.tx_o(tx),.leds_o(leds),
        .i_req_valid_i(iv),.i_req_ready_o(ir),.i_req_addr_i(ia),.i_rsp_valid_o(is),.i_rsp_err_o(ie),.i_rsp_rdata_o(idata),.i_rsp_ready_i(irdy),
        .d_req_valid_i(dv),.d_req_write_i(dw),.d_req_ready_o(dr),.d_req_addr_i(da),.d_req_wdata_i(dd),.d_req_be_i(db),
        .d_rsp_valid_o(ds),.d_rsp_err_o(de),.d_rsp_rdata_o(ddata),.d_rsp_ready_i(drdy));
    always #5 clk=~clk;
    integer fd,fields,checked=0,seed,r0,r1,r3,r5,r6,r8,r11;
    logic [15:0] r2;
    logic [31:0] r4,r7,r9;
    logic [3:0] r10;
    integer p0,p1,p3,p4,p5,p7,p8,q0,q1,q3,q4,q5,q7,q8;
    logic [31:0] p2,p6,q2,q6;
    logic [15:0] p9,q9;
    logic iwait=1'b0,dwait=1'b0,niwait,ndwait;
    logic [31:0] iheld;
    logic [68:0] dheld;
    string vectors;
    function automatic integer read_row;
        read_row=$fscanf(fd,"%h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h\n",
            r0,r1,r2,r3,r4,r5,r6,r7,r8,r9,r10,r11,
            p0,p1,p2,p3,p4,p5,p6,p7,p8,p9,q0,q1,q2,q3,q4,q5,q6,q7,q8,q9);
    endfunction
    initial begin
        if(!$value$plusargs("SEED=%d",seed)||!$value$plusargs("VECTORS=%s",vectors))$fatal(1,"FABRIC_ARGUMENTS");
        fd=$fopen(vectors,"r");if(fd==0)$fatal(1,"FABRIC_VECTOR_OPEN");fields=read_row();
        while(fields==32) begin
            @(negedge clk);rst=(r0!=0);rx=(r1!=0);sw=r2;iv=(r3!=0);ia=r4;irdy=(r5!=0);
            dv=(r6!=0);da=r7;dw=(r8!=0);dd=r9;db=r10;drdy=(r11!=0);#4;
            if({ir,is,idata,ie,dr,ds,ddata,de,tx,leds} !== {(p0!=0),(p1!=0),p2,(p3!=0),(p4!=0),(p5!=0),p6,(p7!=0),(p8!=0),p9})
                $fatal(1,"FABRIC_MISMATCH phase=pre checked=%0d",checked);
            if(!rst && iwait && (!iv || ia!==iheld))$fatal(1,"FABRIC_I_HOLD");
            if(!rst && dwait && (!dv || {da,dw,dd,db}!==dheld))$fatal(1,"FABRIC_D_HOLD");
            niwait=iv && !ir && !rst;ndwait=dv && !dr && !rst;iheld=ia;dheld={da,dw,dd,db};
            @(posedge clk);#1;
            if({ir,is,idata,ie,dr,ds,ddata,de,tx,leds} !== {(q0!=0),(q1!=0),q2,(q3!=0),(q4!=0),(q5!=0),q6,(q7!=0),(q8!=0),q9})
                $fatal(1,"FABRIC_MISMATCH phase=post checked=%0d",checked);
            iwait=niwait;dwait=ndwait;checked=checked+1;fields=read_row();
        end
        if(checked==0)$fatal(1,"FABRIC_EMPTY_VECTORS");
        if(fields>0 || !$feof(fd))$fatal(1,"FABRIC_MALFORMED_VECTOR");
        $display("FABRIC_SIM_PASS seed=%0d checked=%0d",seed,checked);$finish;
    end
    initial begin #10000000;$fatal(1,"FABRIC_TIMEOUT");end
endmodule
`default_nettype wire
