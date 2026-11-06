`default_nettype none
module timer(
    input wire logic clk_i,rst_i,req_valid_i,req_write_i,
    input wire logic [31:0] req_addr_i,req_wdata_i,
    input wire logic [3:0] req_be_i,
    output wire logic req_ready_o,rsp_valid_o,rsp_err_o,
    output wire logic [31:0] rsp_rdata_o,
    input wire logic rsp_ready_i
);
    typedef enum logic [2:0] {NONE=3'd0,COUNT=3'd1,COMPARE=3'd2,CTRL=3'd3,STATUS=3'd4} op_t;
    logic [31:0] count_q,compare_q,pending_data_q,pending_mask_q;
    logic [1:0] ctrl_q;
    logic matched_q,rsp_valid_q,rsp_err_q,decode_error;
    logic [31:0] rsp_data_q,decode_data;
    op_t pending_op_q,decode_op;
    wire logic [31:0] word_addr={req_addr_i[31:2],2'b00};
    wire logic commit_ok=!rst_i && rsp_valid_q && rsp_ready_i && !rsp_err_q;
    wire logic count_write=commit_ok && pending_op_q==COUNT;
    wire logic status_clear=commit_ok && pending_op_q==STATUS && pending_mask_q[0] && pending_data_q[0];
    wire logic [31:0] increment=count_q+32'd1;
    wire logic match_event=ctrl_q[0] && increment==compare_q && !count_write;
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
        decode_error=!legal_lanes(req_addr_i[1:0],req_be_i);decode_data=32'h00000000;decode_op=NONE;
        if(!decode_error) begin
            case(word_addr)
                32'h10000100:if(req_write_i) decode_op=COUNT;else decode_data=count_q;
                32'h10000104:if(req_write_i) decode_op=COMPARE;else decode_data=compare_q;
                32'h10000108:if(req_write_i) decode_op=CTRL;else decode_data={30'h00000000,ctrl_q};
                32'h1000010c:if(req_write_i) decode_op=STATUS;else decode_data={31'h00000000,matched_q};
                default:decode_error=1'b1;
            endcase
        end
    end
    assign req_ready_o=!rst_i && !rsp_valid_q;
    assign rsp_valid_o=!rst_i && rsp_valid_q;
    assign rsp_err_o=!rst_i && rsp_err_q;
    assign rsp_rdata_o=rst_i ? 32'h00000000 : rsp_data_q;
    always_ff @(posedge clk_i) begin
        if(rst_i) begin
            count_q<=32'h00000000;compare_q<=32'h00000000;ctrl_q<=2'b00;matched_q<=1'b0;
            pending_data_q<=32'h00000000;pending_mask_q<=32'h00000000;pending_op_q<=NONE;
            rsp_valid_q<=1'b0;rsp_err_q<=1'b0;rsp_data_q<=32'h00000000;
        end else begin
            if(ctrl_q[0]) begin
                if(match_event && ctrl_q[1]) count_q<=32'h00000000;
                else count_q<=increment;
            end
            if(status_clear) matched_q<=1'b0;
            if(match_event) matched_q<=1'b1;
            if(rsp_valid_q) begin
                if(rsp_ready_i) begin
                    if(!rsp_err_q) begin
                        case(pending_op_q)
                            COUNT:count_q<=(count_q & ~pending_mask_q)|(pending_data_q & pending_mask_q);
                            COMPARE:compare_q<=(compare_q & ~pending_mask_q)|(pending_data_q & pending_mask_q);
                            CTRL:if(pending_mask_q[0]) ctrl_q<=pending_data_q[1:0];
                            default:;
                        endcase
                    end
                    pending_data_q<=32'h00000000;pending_mask_q<=32'h00000000;pending_op_q<=NONE;
                    rsp_valid_q<=1'b0;rsp_err_q<=1'b0;rsp_data_q<=32'h00000000;
                end
            end else if(req_valid_i && req_ready_o) begin
                pending_data_q<=req_wdata_i;pending_mask_q<={{8{req_be_i[3]}},{8{req_be_i[2]}},{8{req_be_i[1]}},{8{req_be_i[0]}}};pending_op_q<=decode_op;
                rsp_valid_q<=1'b1;rsp_err_q<=decode_error;rsp_data_q<=decode_data;
            end
        end
    end
endmodule
`default_nettype wire
