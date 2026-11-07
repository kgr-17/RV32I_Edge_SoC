`default_nettype none
// Approved wrapper reset: asynchronous assertion, two clk_i edges to release.
module reset_sync(
    input wire logic clk_i,arst_i,
    output wire logic rst_o
);
    (* ASYNC_REG="TRUE", SHREG_EXTRACT="NO" *) logic [1:0] release_q=2'b11;
    always_ff @(posedge clk_i or posedge arst_i) begin
        if(arst_i) release_q<=2'b11;
        else release_q<={release_q[0],1'b0};
    end
    assign rst_o=release_q[1];
endmodule
`default_nettype wire
