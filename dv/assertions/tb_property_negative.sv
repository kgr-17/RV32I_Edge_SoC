`default_nettype none
module tb_property_negative;
    timeunit 1ns; timeprecision 1ps;
    logic clk_i=1'b0, rst_i=1'b1;
    always #5ns clk_i=~clk_i;
    logic [4:0] read_addr_a_i=5'd0, read_addr_b_i=5'd0;
    logic [31:0] read_data_a_i=32'd0, read_data_b_i=32'd0;
    logic core_state_zero_i=1'b1;
    logic i_valid_i=1'b0,i_ready_i=1'b0,i_rsp_valid_i=1'b0,i_rsp_ready_i=1'b0;
    logic [31:0] i_addr_i=32'd0;
    logic d_valid_i=1'b0,d_ready_i=1'b0,d_write_i=1'b0,d_rsp_valid_i=1'b0,d_rsp_ready_i=1'b0;
    logic [31:0] d_addr_i=32'd0,d_data_i=32'd0;
    logic [3:0] d_be_i=4'b1111;
    logic retire_valid_i=1'b0,retire_write_i=1'b0;
    logic [63:0] retire_order_i=64'd0;
    logic [4:0] retire_rd_i=5'd0;
    logic [31:0] retire_data_i=32'd0;
    logic fault_valid_i=1'b0;
    logic [99:0] fault_payload_i=100'd0;
    integer injection;
    core_properties monitor (.*);
    task automatic tick;
        @(posedge clk_i); #1ns; @(negedge clk_i);
    endtask
    initial begin
        if (!$value$plusargs("INJECT=%d",injection)) $fatal(1,"Missing injection");
        tick();
        if (injection==4) i_valid_i=1'b1;
        tick();
        rst_i=1'b0;
        if (injection==5) core_state_zero_i=1'b0;
        tick();
        if (injection==1) read_data_a_i=32'd1;
        if (injection==2) read_data_b_i=32'd1;
        if (injection==3) begin retire_valid_i=1'b1; retire_order_i=64'd1; end
        if (injection==12) begin retire_valid_i=1'b1; retire_write_i=1'b1; end
        if (injection==13) begin i_rsp_valid_i=1'b1; i_rsp_ready_i=1'b1; end
        if (injection==14) begin d_rsp_valid_i=1'b1; d_rsp_ready_i=1'b1; end
        tick();
        i_valid_i=1'b1; d_valid_i=1'b1;
        tick();
        if (injection==6) i_addr_i=32'd4;
        if (injection==7) d_data_i=32'd1;
        if (injection==8) i_valid_i=1'b0;
        if (injection==9) d_valid_i=1'b0;
        i_ready_i=1'b1; d_ready_i=1'b1;
        tick();
        if (injection!=15) i_valid_i=1'b0;
        if (injection!=16) d_valid_i=1'b0;
        tick();
        i_rsp_valid_i=1'b1; i_rsp_ready_i=1'b1;
        d_rsp_valid_i=1'b1; d_rsp_ready_i=1'b1;
        tick();
        i_rsp_valid_i=1'b0; d_rsp_valid_i=1'b0;
        i_rsp_ready_i=1'b0; d_rsp_ready_i=1'b0;
        retire_valid_i=1'b1;
        tick();
        retire_valid_i=1'b0; fault_valid_i=1'b1;
        tick();
        if (injection==10) fault_valid_i=1'b0;
        if (injection==11) fault_payload_i=100'd1;
        tick();
        if (injection!=0) $fatal(1,"Injection was not detected");
        $display("PROPERTY_CONTROL_PASS"); $finish;
    end
endmodule
`default_nettype wire
