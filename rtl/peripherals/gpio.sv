`default_nettype none
module gpio(
    input wire logic clk_i,rst_i,
    input wire logic [15:0] switches_i,
    output wire logic [15:0] leds_o,
    input wire logic req_valid_i,req_write_i,
    input wire logic [31:0] req_addr_i,
    input wire logic [15:0] req_wdata_i,
    input wire logic [3:0] req_be_i,
    output wire logic req_ready_o,rsp_valid_o,rsp_err_o,
    output wire logic [31:0] rsp_rdata_o,
    input wire logic rsp_ready_i
);
    typedef enum logic [1:0] {NONE=2'd0,OUT=2'd1,SET=2'd2,CLEAR=2'd3} op_t;
    logic [15:0] output_q,pending_data_q,pending_mask_q;
    wire logic [15:0] sampled;
    logic rsp_valid_q,rsp_err_q,decode_error;
    logic [31:0] rsp_data_q,decode_data;
    op_t pending_op_q,decode_op;
    wire logic [31:0] word_addr={req_addr_i[31:2],2'b00};
    input_sync #(.WIDTH(32'd16)) inputs(.clk_i(clk_i),.rst_i(rst_i),.async_i(switches_i),.sync_o(sampled));
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
        decode_error=!legal_lanes(req_addr_i[1:0],req_be_i);decode_op=NONE;decode_data=32'h00000000;
        if(!decode_error) begin
            case(word_addr)
                32'h10000020:if(req_write_i) decode_op=OUT;else decode_data={16'h0000,output_q};
                32'h10000024:if(req_write_i) decode_error=1'b1;else decode_data={16'h0000,sampled};
                32'h10000028:if(req_write_i) decode_op=SET;
                32'h1000002c:if(req_write_i) decode_op=CLEAR;
                default:decode_error=1'b1;
            endcase
        end
    end
    assign leds_o=output_q;
    assign req_ready_o=!rst_i && !rsp_valid_q;
    assign rsp_valid_o=!rst_i && rsp_valid_q;
    assign rsp_err_o=!rst_i && rsp_err_q;
    assign rsp_rdata_o=rst_i ? 32'h00000000 : rsp_data_q;
    always_ff @(posedge clk_i) begin
        if(rst_i) begin
            output_q<=16'h0000;pending_data_q<=16'h0000;pending_mask_q<=16'h0000;pending_op_q<=NONE;
            rsp_valid_q<=1'b0;rsp_err_q<=1'b0;rsp_data_q<=32'h00000000;
        end else if(rsp_valid_q) begin
            if(rsp_ready_i) begin
                if(!rsp_err_q) begin
                    case(pending_op_q)
                        OUT:output_q<=(output_q & ~pending_mask_q)|(pending_data_q & pending_mask_q);
                        SET:output_q<=output_q|(pending_data_q & pending_mask_q);
                        CLEAR:output_q<=output_q & ~(pending_data_q & pending_mask_q);
                        default:;
                    endcase
                end
                pending_data_q<=16'h0000;pending_mask_q<=16'h0000;pending_op_q<=NONE;
                rsp_valid_q<=1'b0;rsp_err_q<=1'b0;rsp_data_q<=32'h00000000;
            end
        end else if(req_valid_i && req_ready_o) begin
            pending_data_q<=req_wdata_i;pending_mask_q<={{8{req_be_i[1]}},{8{req_be_i[0]}}};pending_op_q<=decode_op;
            rsp_valid_q<=1'b1;rsp_err_q<=decode_error;rsp_data_q<=decode_data;
        end
    end
endmodule
`default_nettype wire
