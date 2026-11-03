`default_nettype none
module hazard_unit (
    input wire logic consumer_valid_i,uses_a_i,uses_b_i,
    input wire logic [4:0] rs_a_i,rs_b_i,
    input wire logic load_valid_i,load_write_i,load_is_load_i,
    input wire logic [4:0] load_rd_i,
    output wire logic wait_a_o,wait_b_o,stall_o
);
    wire logic pending_write;
    assign pending_write=load_valid_i && load_write_i && load_is_load_i && (load_rd_i!=5'd0);
    assign wait_a_o=consumer_valid_i && uses_a_i && pending_write && (rs_a_i==load_rd_i);
    assign wait_b_o=consumer_valid_i && uses_b_i && pending_write && (rs_b_i==load_rd_i);
    assign stall_o=wait_a_o || wait_b_o;
endmodule
`default_nettype wire
