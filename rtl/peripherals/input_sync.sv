`default_nettype none
// Independent input bits, not an atomic multibit transfer or pulse synchronizer.
module input_sync #(parameter int unsigned WIDTH=32'd16)(
    input wire logic clk_i,rst_i,
    input wire logic [WIDTH-1:0] async_i,
    output wire logic [WIDTH-1:0] sync_o
);
    (* ASYNC_REG="TRUE" *) logic [WIDTH-1:0] meta_q,sync_q;
    if(WIDTH<32'd1 || WIDTH>32'd32) begin : invalid_width
        initial $fatal(1,"INPUT_SYNC_WIDTH");
    end
    always_ff @(posedge clk_i) begin
        if(rst_i) begin meta_q<={WIDTH{1'b0}};sync_q<={WIDTH{1'b0}};end
        else begin meta_q<=async_i;sync_q<=meta_q;end
    end
    assign sync_o=sync_q;
endmodule
`default_nettype wire
