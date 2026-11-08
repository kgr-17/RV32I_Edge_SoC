`default_nettype none
// Drain admission and continuation tracking, independent of speculative fetch PC.
module trap_control (
    input wire logic clk_i,rst_i,eligible_i,empty_i,sync_trap_i,retire_i,
    input wire logic [31:0] retire_next_pc_i,trap_target_i,
    output wire logic draining_o,block_fetch_o,irq_commit_o,boundary_o,
    output wire logic [31:0] resume_pc_o
);
    logic draining_q;
    logic [31:0] continuation_q;
    assign draining_o=!rst_i && draining_q;
    assign block_fetch_o=!rst_i && (draining_q || eligible_i);
    assign boundary_o=!rst_i && draining_q && empty_i && !sync_trap_i;
    assign irq_commit_o=boundary_o && eligible_i;
    assign resume_pc_o=continuation_q;
    always_ff @(posedge clk_i) begin
        if(rst_i) begin draining_q<=1'b0;continuation_q<=32'd0;end
        else begin
            if(retire_i) continuation_q<=retire_next_pc_i;
            if(sync_trap_i)begin draining_q<=1'b0;continuation_q<=trap_target_i;end
            else if(draining_q)begin if(empty_i)draining_q<=1'b0;end
            else if(eligible_i)draining_q<=1'b1;
        end
    end
endmodule
`default_nettype wire
