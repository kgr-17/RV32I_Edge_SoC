`default_nettype none
// T013 stage storage only. The executable pipeline top is integrated later.
module rv32_pipeline_stage #(
    parameter int unsigned WIDTH = 32'd32,
    parameter bit MASK_PAYLOAD = 1'b1,
    parameter bit PRELOAD_WHEN_EMPTY = 1'b0
) (
    input wire logic clk_i, rst_i,
    input wire logic clear_i, hold_i, valid_i,
    input wire logic [WIDTH-1:0] payload_i,
    output wire logic valid_o,
    output wire logic [WIDTH-1:0] payload_o
);
    logic valid_q;
    logic [WIDTH-1:0] payload_q;
    // The controller first arbitrates architectural priorities. clear_i is an
    // already-selected kill/bubble, not an unqualified redirect request.
    always_ff @(posedge clk_i) begin
        if (rst_i || clear_i) begin
            valid_q <= 1'b0;
        end else if (!hold_i) begin
            valid_q <= valid_i;
        end
        if (PRELOAD_WHEN_EMPTY) begin
            // Fetch PC cache: prepare the next address only while inactive.
            // Active request payload stays fixed through all backpressure.
            if (!valid_q) payload_q <= payload_i;
        end else if (rst_i || clear_i) payload_q <= '0;
        else if (!hold_i) payload_q <= valid_i ? payload_i : '0;
    end
    // Reset masks observations immediately; storage itself resets only on edge.
    assign valid_o = !rst_i && valid_q;
    // Generic observation ports keep their immediate reset/invalid mask. The
    // integrated core may read the raw internal register. Default payload
    // clearing is retained; IF preload treats inactive payload as a cache.
    // The controller independently qualifies every architectural effect.
    assign payload_o = MASK_PAYLOAD ? ((!rst_i && valid_q) ? payload_q : '0) : payload_q;
endmodule

module pipeline_registers #(
    parameter int unsigned WIDTH = 32'd32
) (
    input wire logic clk_i, rst_i,
    input wire logic [4:0] clear_i, hold_i, valid_i,
    input wire logic [WIDTH-1:0] payload_i [0:4],
    output wire logic [4:0] valid_o,
    output wire logic [WIDTH-1:0] payload_o [0:4]
);
    // Stage indices: IF=0, ID=1, EX=2, MEM=3, WB=4. Each is independent;
    // upstream-to-downstream selection/transform is the controller's job.
    for (genvar stage=32'd0; stage<32'd5; stage=stage+32'd1) begin : g_stage
        rv32_pipeline_stage #(.WIDTH(WIDTH)) storage (
            .clk_i(clk_i), .rst_i(rst_i), .clear_i(clear_i[stage]),
            .hold_i(hold_i[stage]), .valid_i(valid_i[stage]),
            .payload_i(payload_i[stage]), .valid_o(valid_o[stage]), .payload_o(payload_o[stage]));
    end
endmodule
`default_nettype wire
