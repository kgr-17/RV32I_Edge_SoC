`default_nettype none
module tb_pipeline_base;
    timeunit 1ns; timeprecision 1ps;
    logic clk=1'b0, rst=1'b1;
    always #10ns clk=~clk;
    logic [4:0] clear,hold,valid;
    logic pulse;
    logic [128:0] data [0:4],pre_data [0:4],post_data [0:4];
    wire logic [128:0] observed [0:4];
    wire logic [31:0] data32 [0:4],observed32 [0:4];
    wire logic [0:0] data1 [0:4],observed1 [0:4];
    wire logic [4:0] v129,v32,v1;
    wire logic [128:0] if_payload,id_payload,ex_payload,mem_payload,wb_payload;
    assign {if_payload,id_payload,ex_payload,mem_payload,wb_payload}=
           {observed[0],observed[1],observed[2],observed[3],observed[4]};
    logic [4:0] pre_valid,post_valid;
    integer vector_file,scanned,checked=0;
    integer unsigned seed,expected_count;
    string vector_path;
    for (genvar stage=32'd0;stage<32'd5;stage=stage+32'd1) begin : g_width
        assign data32[stage]=data[stage][31:0];
        assign data1[stage]=data[stage][0:0];
    end
    pipeline_registers #(.WIDTH(32'd129)) wide (.clk_i(clk),.rst_i(rst),.clear_i(clear),.hold_i(hold),.valid_i(valid),.payload_i(data),.valid_o(v129),.payload_o(observed));
    pipeline_registers #(.WIDTH(32'd32)) word (.clk_i(clk),.rst_i(rst),.clear_i(clear),.hold_i(hold),.valid_i(valid),.payload_i(data32),.valid_o(v32),.payload_o(observed32));
    pipeline_registers #(.WIDTH(32'd1)) bit_stage (.clk_i(clk),.rst_i(rst),.clear_i(clear),.hold_i(hold),.valid_i(valid),.payload_i(data1),.valid_o(v1),.payload_o(observed1));
    task automatic compare(input bit after_edge);
        if ({v129,v32,v1} !== {3{after_edge ? post_valid : pre_valid}})
            $fatal(1,"PIPELINE_MISMATCH valid seed=%0d row=%0d phase=%0d",seed,checked,after_edge);
        for (int stage=0;stage<5;stage=stage+1) begin
            if (observed[stage] !== (after_edge ? post_data[stage] : pre_data[stage]) ||
                observed32[stage] !== (after_edge ? post_data[stage][31:0] : pre_data[stage][31:0]) ||
                observed1[stage] !== (after_edge ? post_data[stage][0:0] : pre_data[stage][0:0]))
                $fatal(1,"PIPELINE_MISMATCH payload seed=%0d row=%0d stage=%0d phase=%0d",seed,checked,stage,after_edge);
        end
    endtask
    initial begin
        if (!$value$plusargs("SEED=%d",seed)) $fatal(1,"Missing seed");
        if (!$value$plusargs("COUNT=%d",expected_count) || expected_count==0) $fatal(1,"Zero tests");
        if (!$value$plusargs("VECTORS=%s",vector_path)) $fatal(1,"Missing vectors");
        vector_file=$fopen(vector_path,"r");
        if (vector_file==0) $fatal(1,"Cannot read vectors");
        while (!$feof(vector_file)) begin
            @(negedge clk);
            scanned=$fscanf(vector_file,"%h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h %h\n",
                rst,clear,hold,valid,pulse,data[0],data[1],data[2],data[3],data[4],pre_valid,post_valid,
                pre_data[0],pre_data[1],pre_data[2],pre_data[3],pre_data[4],post_data[0],post_data[1],post_data[2],post_data[3],post_data[4]);
            if (scanned==22) begin
                #1ns;compare(0);
                @(posedge clk);#1ns;compare(1);
                if (pulse) begin
                    #1ns;rst=1'b1;#1ns;
                    if ({v129,v32,v1}!==15'd0) $fatal(1,"PIPELINE_MISMATCH reset mask");
                    for (int stage=0;stage<5;stage=stage+1)
                        if ({observed[stage],observed32[stage],observed1[stage]}!==162'd0) $fatal(1,"PIPELINE_MISMATCH reset payload mask");
                    #1ns;rst=1'b0;#1ns;compare(1);
                end
                checked=checked+1;
            end else if (scanned!=-1) $fatal(1,"Malformed pipeline input");
        end
        $fclose(vector_file);
        if (checked!=expected_count) $fatal(1,"Wrong count %0d != %0d",checked,expected_count);
        $display("PIPELINE_SIM_PASS seed=%0d checked=%0d",seed,checked);
        $finish;
    end
endmodule
`default_nettype wire
