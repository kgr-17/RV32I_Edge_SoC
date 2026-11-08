`default_nettype none
// Default async assertion/two-edge release. A board may select fully clocked
// assertion/release: both raw input transitions then pass two ASYNC_REG flops.
module reset_sync #(parameter bit ASYNC_ASSERT=1'b1)(
    input wire logic clk_i,arst_i,
    output wire logic rst_o
);
    (* ASYNC_REG="TRUE", SHREG_EXTRACT="NO" *) logic [1:0] release_q=2'b11;
    generate if(ASYNC_ASSERT) begin : g_async
        always_ff @(posedge clk_i or posedge arst_i) begin
            if(arst_i) release_q<=2'b11;
            else release_q<={release_q[0],1'b0};
        end
    end else begin : g_sync
        always_ff @(posedge clk_i) release_q<={release_q[0],arst_i};
    end endgenerate
    assign rst_o=release_q[1];
endmodule
`default_nettype wire
