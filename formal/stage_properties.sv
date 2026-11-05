`default_nettype none
module formal_stage (
    input wire logic clk_i,rst_i,clear_i,hold_i,valid_i,
    input wire logic [31:0] payload_i
);
    wire logic valid_o;
    wire logic [31:0] payload_o;
    logic past_valid=1'b0;
    rv32_pipeline_stage #(.WIDTH(32'd32)) dut (.*);
    always_comb begin
        if (rst_i || !valid_o) assert (payload_o==32'd0);
        if (rst_i) assert (!valid_o);
    end
    always_ff @(posedge clk_i) begin
        past_valid<=1'b1;
        if (!past_valid) assume (rst_i);
        if (past_valid && !rst_i) begin
            if ($past(rst_i || clear_i)) assert (!valid_o && payload_o==32'd0);
            else if ($past(hold_i)) begin
                assert (valid_o==$past(valid_o));
                assert (payload_o==$past(payload_o));
            end else begin
                assert (valid_o==$past(valid_i));
                if ($past(valid_i)) assert (payload_o==$past(payload_i));
                else assert (payload_o==32'd0);
            end
        end
        cover (past_valid && !rst_i && valid_o && hold_i && payload_o!=32'd0);
    end
endmodule
`default_nettype wire
