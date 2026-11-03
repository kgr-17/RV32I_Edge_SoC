`default_nettype none
module pipeline_lint_top (
    input wire logic clk_i, rst_i,
    input wire logic [2:0] load_sel_i, observe_sel_i,
    input wire logic [31:0] data_i,
    input wire logic [4:0] clear_i, hold_i, valid_i,
    output wire logic [4:0] valid_o,
    output logic [31:0] data_o
);
    logic [31:0] inputs_q [0:4];
    wire logic [31:0] payload [0:4];
    for (genvar stage=32'd0; stage<32'd5; stage=stage+32'd1) begin : g_capture
        always_ff @(posedge clk_i) begin
            if (rst_i) inputs_q[stage] <= 32'd0;
            else if (load_sel_i==stage[2:0]) inputs_q[stage] <= data_i;
        end
    end
    pipeline_registers #(.WIDTH(32'd32)) dut (.clk_i(clk_i), .rst_i(rst_i),
        .clear_i(clear_i), .hold_i(hold_i), .valid_i(valid_i), .payload_i(inputs_q),
        .valid_o(valid_o), .payload_o(payload));
    always_comb begin
        data_o=32'd0;
        case (observe_sel_i)
            3'd0: data_o=payload[0];
            3'd1: data_o=payload[1];
            3'd2: data_o=payload[2];
            3'd3: data_o=payload[3];
            3'd4: data_o=payload[4];
            default: data_o=32'd0;
        endcase
    end
endmodule
`default_nettype wire
