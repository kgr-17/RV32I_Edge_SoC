`default_nettype none
// Single-clock center sampling. Async input touches only the two-stage chain.
module uart_rx #(
    parameter int unsigned CLKS_PER_BIT = 32'd868
) (
    input wire logic clk_i, rst_i, enable_i, rx_i,
    output logic data_valid_o, frame_error_o,
    output logic [7:0] data_o,
    output wire logic busy_o
);
    localparam int unsigned COUNT_W = $clog2(CLKS_PER_BIT);
    localparam logic [COUNT_W-1:0] LAST = COUNT_W'(CLKS_PER_BIT-32'd1);
    localparam logic [COUNT_W-1:0] HALF = COUNT_W'(CLKS_PER_BIT/32'd2-32'd1);
    typedef enum logic [2:0] {WAIT_HIGH=3'd0, IDLE=3'd1, START=3'd2,
        DATA=3'd3, STOP=3'd4} state_t;
    (* ASYNC_REG="TRUE" *) logic rx_meta_q, rx_sync_q;
    logic [COUNT_W-1:0] count_q;
    logic [2:0] bit_q;
    logic [7:0] byte_q;
    state_t state_q;
    if (CLKS_PER_BIT<32'd2 || CLKS_PER_BIT>32'd65536) begin : invalid_divisor
        initial $fatal(1,"UART_RX_DIVISOR_RANGE");
    end
    assign busy_o = (state_q==START || state_q==DATA || state_q==STOP);
    always_ff @(posedge clk_i) begin
        if(rst_i) begin rx_meta_q<=1'b1;rx_sync_q<=1'b1;end
        else begin rx_meta_q<=rx_i;rx_sync_q<=rx_meta_q;end
    end
    always_ff @(posedge clk_i) begin
        data_valid_o<=1'b0;frame_error_o<=1'b0;
        if(rst_i) begin
            state_q<=WAIT_HIGH;count_q<={COUNT_W{1'b0}};bit_q<=3'd0;
            byte_q<=8'h00;data_o<=8'h00;
        end else if(!enable_i) begin
            state_q<=WAIT_HIGH;count_q<={COUNT_W{1'b0}};bit_q<=3'd0;byte_q<=8'h00;
        end else begin
            case(state_q)
                WAIT_HIGH: if(rx_sync_q) state_q<=IDLE;
                IDLE: if(!rx_sync_q) begin state_q<=START;count_q<=HALF;end
                START: begin
                    if(count_q!={COUNT_W{1'b0}}) count_q<=count_q-COUNT_W'(1);
                    else if(rx_sync_q) state_q<=IDLE; // false start, no frame error
                    else begin state_q<=DATA;count_q<=LAST;bit_q<=3'd0;end
                end
                DATA: begin
                    if(count_q!={COUNT_W{1'b0}}) count_q<=count_q-COUNT_W'(1);
                    else begin
                        byte_q[bit_q]<=rx_sync_q;count_q<=LAST;
                        if(bit_q==3'd7) state_q<=STOP;
                        else bit_q<=bit_q+3'd1;
                    end
                end
                STOP: begin
                    if(count_q!={COUNT_W{1'b0}}) count_q<=count_q-COUNT_W'(1);
                    else if(rx_sync_q) begin
                        data_o<=byte_q;data_valid_o<=1'b1;state_q<=IDLE;
                    end else begin frame_error_o<=1'b1;state_q<=WAIT_HIGH;end
                end
                default: state_q<=WAIT_HIGH;
            endcase
        end
    end
endmodule
`default_nettype wire
