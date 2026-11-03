`default_nettype none
module forwarding_lint_top (
    input wire logic clk_i,rst_i,
    input wire logic [1:0] capture_i,
    input wire logic observe_b_i,
    input wire logic [31:0] data_i,
    input wire logic [7:0] flags_i,
    input wire logic [4:0] rs_a_i,rs_b_i,ex_rd_i,wb_rd_i,
    output wire logic [5:0] metadata_o,
    output wire logic [31:0] data_o
);
    logic [31:0] captured_a,captured_b,ex_value,wb_value;
    wire logic [31:0] a,b;
    wire logic [1:0] sa,sb;
    wire logic ba,bb;
    always_ff @(posedge clk_i) begin
        if (rst_i) begin
            captured_a<=32'd0;captured_b<=32'd0;ex_value<=32'd0;wb_value<=32'd0;
        end else begin
            case (capture_i)
                2'd0: captured_a<=data_i;
                2'd1: captured_b<=data_i;
                2'd2: ex_value<=data_i;
                2'd3: wb_value<=data_i;
                default: begin end
            endcase
        end
    end
    forwarding_unit dut (.valid_i(flags_i[0]),.uses_a_i(flags_i[1]),.uses_b_i(flags_i[2]),
        .rs_a_i(rs_a_i),.rs_b_i(rs_b_i),.captured_a_i(captured_a),.captured_b_i(captured_b),
        .ex_valid_i(flags_i[3]),.ex_write_i(flags_i[4]),.ex_load_i(flags_i[5]),.ex_rd_i(ex_rd_i),.ex_value_i(ex_value),
        .wb_valid_i(flags_i[6]),.wb_write_i(flags_i[7]),.wb_rd_i(wb_rd_i),.wb_value_i(wb_value),
        .value_a_o(a),.value_b_o(b),.source_a_o(sa),.source_b_o(sb),.blocked_a_o(ba),.blocked_b_o(bb));
    assign metadata_o={sa,sb,ba,bb};
    assign data_o=observe_b_i ? b : a;
endmodule
`default_nettype wire
