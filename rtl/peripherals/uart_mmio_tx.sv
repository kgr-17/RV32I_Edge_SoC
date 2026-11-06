`default_nettype none
// T027 TX-side register frontend. RX slot/flags/deserializer are T042 work;
// until connected, STATUS RX bits and empty RXDATA are zero. No SoC hookup yet.
module uart_mmio_tx #(
    parameter int unsigned CLKS_PER_BIT = 32'd868
) (
    input wire logic clk_i, rst_i,
    input wire logic req_valid_i, req_write_i,
    input wire logic [31:0] req_addr_i,
    input wire logic [7:0] req_wdata_i,
    input wire logic [3:0] req_be_i,
    output wire logic req_ready_o,
    output wire logic rsp_valid_o, rsp_err_o,
    output wire logic [31:0] rsp_rdata_o,
    input wire logic rsp_ready_i,
    output wire logic tx_o
);
    typedef enum logic [1:0] {OP_NONE=2'd0, OP_TX=2'd1, OP_CTRL=2'd2} op_t;
    logic [1:0] ctrl_q, pending_ctrl_q;
    logic pending_low_q, rsp_valid_q, rsp_err_q;
    logic [31:0] rsp_data_q, decode_data;
    logic [7:0] pending_byte_q;
    op_t pending_op_q, decode_op;
    logic decode_error;
    wire logic tx_ready, tx_valid;
    wire logic [31:0] word_addr = {req_addr_i[31:2], 2'b00};

    function automatic logic legal_lanes(input logic [1:0] offset, input logic [3:0] lanes);
        case (lanes)
            4'b0001: legal_lanes = (offset == 2'd0);
            4'b0010: legal_lanes = (offset == 2'd1);
            4'b0100: legal_lanes = (offset == 2'd2);
            4'b1000: legal_lanes = (offset == 2'd3);
            4'b0011: legal_lanes = (offset == 2'd0);
            4'b1100: legal_lanes = (offset == 2'd2);
            4'b1111: legal_lanes = (offset == 2'd0);
            default: legal_lanes = 1'b0;
        endcase
    endfunction
    always_comb begin
        decode_error = !legal_lanes(req_addr_i[1:0], req_be_i);
        decode_op = OP_NONE;
        decode_data = 32'h00000000;
        if (!decode_error) begin
            case (word_addr)
                32'h10000000: begin
                    if (req_write_i) begin
                        if (!ctrl_q[1]) decode_error = 1'b1;
                        else if (req_be_i[0]) decode_op = OP_TX;
                    end
                end
                32'h10000004: begin
                    if (req_write_i) decode_error = 1'b1;
                    else decode_data = {31'h00000000, tx_ready};
                end
                32'h10000008: begin
                    if (req_write_i) decode_error = 1'b1;
                end
                32'h1000000c: begin
                    if (req_write_i) decode_op = OP_CTRL;
                    else decode_data = {30'h00000000, ctrl_q};
                end
                default: decode_error = 1'b1;
            endcase
        end
    end
    assign req_ready_o = !rst_i && !rsp_valid_q &&
        (decode_error || decode_op != OP_TX || tx_ready);
    assign rsp_valid_o = !rst_i && rsp_valid_q;
    assign rsp_rdata_o = rst_i ? 32'h00000000 : rsp_data_q;
    assign rsp_err_o = !rst_i && rsp_err_q;
    assign tx_valid = !rst_i && rsp_valid_q && rsp_ready_i && !rsp_err_q && pending_op_q == OP_TX;
    uart_tx #(.CLKS_PER_BIT(CLKS_PER_BIT)) serial (
        .clk_i(clk_i), .rst_i(rst_i), .enable_i(ctrl_q[1]),
        .data_valid_i(tx_valid), .data_i(pending_byte_q),
        .data_ready_o(tx_ready), .busy_o(), .tx_o(tx_o));

    always_ff @(posedge clk_i) begin
        if (rst_i) begin
            ctrl_q <= 2'b11;
            pending_ctrl_q <= 2'b00;
            pending_low_q <= 1'b0;
            pending_byte_q <= 8'h00;
            pending_op_q <= OP_NONE;
            rsp_valid_q <= 1'b0;
            rsp_err_q <= 1'b0;
            rsp_data_q <= 32'h00000000;
        end else if (rsp_valid_q) begin
            if (rsp_ready_i) begin
                if (!rsp_err_q && pending_op_q == OP_CTRL && pending_low_q)
                    ctrl_q <= pending_ctrl_q;
                pending_ctrl_q <= 2'b00;
                pending_low_q <= 1'b0;
                pending_byte_q <= 8'h00;
                pending_op_q <= OP_NONE;
                rsp_valid_q <= 1'b0;
                rsp_err_q <= 1'b0;
                rsp_data_q <= 32'h00000000;
            end
        end else if (req_valid_i && req_ready_o) begin
            pending_ctrl_q <= req_wdata_i[1:0];
            pending_low_q <= req_be_i[0];
            pending_byte_q <= req_wdata_i[7:0];
            pending_op_q <= decode_op;
            rsp_valid_q <= 1'b1;
            rsp_err_q <= decode_error;
            rsp_data_q <= decode_data;
        end
    end
endmodule
`default_nettype wire
