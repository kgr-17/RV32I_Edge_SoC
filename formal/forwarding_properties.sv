`default_nettype none
module formal_forward (
    input wire logic valid_i,uses_a_i,uses_b_i,
    input wire logic [4:0] rs_a_i,rs_b_i,
    input wire logic [31:0] captured_a_i,captured_b_i,
    input wire logic ex_valid_i,ex_write_i,ex_load_i,
    input wire logic [4:0] ex_rd_i,
    input wire logic [31:0] ex_value_i,
    input wire logic wb_valid_i,wb_write_i,
    input wire logic [4:0] wb_rd_i,
    input wire logic [31:0] wb_value_i
);
    wire logic [31:0] value_a_o,value_b_o;
    wire logic [1:0] source_a_o,source_b_o;
    wire logic blocked_a_o,blocked_b_o;
    forwarding_unit dut (.*);
    always_comb begin
        if (!valid_i || !uses_a_i || rs_a_i==5'd0)
            assert ({value_a_o,source_a_o,blocked_a_o}==35'd0);
        if (!valid_i || !uses_b_i || rs_b_i==5'd0)
            assert ({value_b_o,source_b_o,blocked_b_o}==35'd0);
        // A matching nearest older producer cannot be overridden by WB.
        if (valid_i && uses_a_i && rs_a_i!=5'd0 && ex_valid_i && ex_write_i && ex_rd_i==rs_a_i) begin
            if (ex_load_i) assert (blocked_a_o && source_a_o==2'd3 && value_a_o==32'd0);
            else assert (!blocked_a_o && source_a_o==2'd1 && value_a_o==ex_value_i);
        end
        if (valid_i && uses_b_i && rs_b_i!=5'd0 && ex_valid_i && ex_write_i && ex_rd_i==rs_b_i) begin
            if (ex_load_i) assert (blocked_b_o && source_b_o==2'd3 && value_b_o==32'd0);
            else assert (!blocked_b_o && source_b_o==2'd1 && value_b_o==ex_value_i);
        end
    end
endmodule
`default_nettype wire
