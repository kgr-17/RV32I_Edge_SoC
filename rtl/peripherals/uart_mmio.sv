`default_nettype none
// Canonical combined UART. Only meaningful write bits9:0 cross this internal
// frontend; the32-bit master retains original address/lanes and selects [9:0].
module uart_mmio #(
    parameter int unsigned CLKS_PER_BIT=32'd868
) (
    input wire logic clk_i,rst_i,rx_i,
    input wire logic req_valid_i,req_write_i,
    input wire logic [31:0] req_addr_i,
    input wire logic [9:0] req_wdata_i,
    input wire logic [3:0] req_be_i,
    output wire logic req_ready_o,rsp_valid_o,rsp_err_o,
    output wire logic [31:0] rsp_rdata_o,
    input wire logic rsp_ready_i,
    output wire logic tx_o
);
    typedef enum logic [1:0] {OP_NONE=2'd0,OP_TX=2'd1,OP_CTRL=2'd2,OP_RX=2'd3} op_t;
    logic [1:0] ctrl_q,pending_ctrl_q,pending_clear_q;
    logic pending_low_q,pending_w1c_q,pending_pop_q;
    logic [7:0] pending_byte_q,head_q;
    logic full_q,overrun_q,frame_q;
    logic rsp_valid_q,rsp_err_q;
    logic [31:0] rsp_data_q,decode_data;
    op_t pending_op_q,decode_op;
    logic decode_error;
    wire logic tx_ready,tx_valid,received,frame_event;
    wire logic [7:0] received_byte;
    wire logic [31:0] word_addr={req_addr_i[31:2],2'b00};
    wire logic commit_ok=!rst_i && rsp_valid_q && rsp_ready_i && !rsp_err_q;
    wire logic pop=commit_ok && pending_op_q==OP_RX && pending_pop_q;
    wire logic clear_over=commit_ok && pending_op_q==OP_CTRL && pending_w1c_q && pending_clear_q[0];
    wire logic clear_frame=commit_ok && pending_op_q==OP_CTRL && pending_w1c_q && pending_clear_q[1];
    function automatic logic legal_lanes(input logic [1:0] offset,input logic [3:0] lanes);
        case(lanes)
            4'b0001:legal_lanes=(offset==2'd0);
            4'b0010:legal_lanes=(offset==2'd1);
            4'b0100:legal_lanes=(offset==2'd2);
            4'b1000:legal_lanes=(offset==2'd3);
            4'b0011:legal_lanes=(offset==2'd0);
            4'b1100:legal_lanes=(offset==2'd2);
            4'b1111:legal_lanes=(offset==2'd0);
            default:legal_lanes=1'b0;
        endcase
    endfunction
    always_comb begin
        decode_error=!legal_lanes(req_addr_i[1:0],req_be_i);
        decode_data=32'h00000000;decode_op=OP_NONE;
        if(!decode_error) begin
            case(word_addr)
                32'h10000000:if(req_write_i) begin
                    if(!ctrl_q[1]) decode_error=1'b1;
                    else if(req_be_i[0]) decode_op=OP_TX;
                end
                32'h10000004:begin
                    if(req_write_i) decode_error=1'b1;
                    else decode_data={28'h0000000,frame_q,overrun_q,full_q,tx_ready};
                end
                32'h10000008:begin
                    if(req_write_i) decode_error=1'b1;
                    else begin decode_data={24'h000000,full_q ? head_q : 8'h00};decode_op=OP_RX;end
                end
                32'h1000000c:begin
                    if(req_write_i) decode_op=OP_CTRL;
                    else decode_data={30'h00000000,ctrl_q};
                end
                default:decode_error=1'b1;
            endcase
        end
    end
    assign req_ready_o=!rst_i && !rsp_valid_q && (decode_error || decode_op!=OP_TX || tx_ready);
    assign rsp_valid_o=!rst_i && rsp_valid_q;
    assign rsp_err_o=!rst_i && rsp_err_q;
    assign rsp_rdata_o=rst_i ? 32'h00000000 : rsp_data_q;
    assign tx_valid=commit_ok && pending_op_q==OP_TX;
    uart_tx #(.CLKS_PER_BIT(CLKS_PER_BIT)) transmitter(
        .clk_i(clk_i),.rst_i(rst_i),.enable_i(ctrl_q[1]),.data_valid_i(tx_valid),
        .data_i(pending_byte_q),.data_ready_o(tx_ready),.busy_o(),.tx_o(tx_o));
    uart_rx #(.CLKS_PER_BIT(CLKS_PER_BIT)) receiver(
        .clk_i(clk_i),.rst_i(rst_i),.enable_i(ctrl_q[0]),.rx_i(rx_i),
        .data_valid_o(received),.frame_error_o(frame_event),.data_o(received_byte),.busy_o());
    always_ff @(posedge clk_i) begin
        if(rst_i) begin
            ctrl_q<=2'b11;pending_ctrl_q<=2'b00;pending_clear_q<=2'b00;
            pending_low_q<=1'b0;pending_w1c_q<=1'b0;pending_pop_q<=1'b0;
            pending_byte_q<=8'h00;pending_op_q<=OP_NONE;
            rsp_valid_q<=1'b0;rsp_err_q<=1'b0;rsp_data_q<=32'h00000000;
            head_q<=8'h00;full_q<=1'b0;overrun_q<=1'b0;frame_q<=1'b0;
        end else begin
            if(clear_over) overrun_q<=1'b0;
            if(clear_frame) frame_q<=1'b0;
            if(pop) begin full_q<=1'b0;head_q<=8'h00;end
            if(received) begin
                if(!full_q || pop) begin full_q<=1'b1;head_q<=received_byte;end
                else overrun_q<=1'b1;
            end
            if(frame_event) frame_q<=1'b1;
            if(rsp_valid_q) begin
                if(rsp_ready_i) begin
                    if(!rsp_err_q && pending_op_q==OP_CTRL && pending_low_q) ctrl_q<=pending_ctrl_q;
                    pending_ctrl_q<=2'b00;pending_clear_q<=2'b00;
                    pending_low_q<=1'b0;pending_w1c_q<=1'b0;pending_pop_q<=1'b0;
                    pending_byte_q<=8'h00;pending_op_q<=OP_NONE;
                    rsp_valid_q<=1'b0;rsp_err_q<=1'b0;rsp_data_q<=32'h00000000;
                end
            end else if(req_valid_i && req_ready_o) begin
                pending_ctrl_q<=req_wdata_i[1:0];pending_clear_q<=req_wdata_i[9:8];
                pending_low_q<=req_be_i[0];pending_w1c_q<=req_be_i[1];
                pending_pop_q<=full_q && req_be_i[0];pending_byte_q<=req_wdata_i[7:0];
                pending_op_q<=decode_op;rsp_valid_q<=1'b1;rsp_err_q<=decode_error;rsp_data_q<=decode_data;
            end
        end
    end
endmodule
`default_nettype wire
