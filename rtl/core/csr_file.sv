`default_nettype none
// Approved v0.3 CSR subset; atomic commit, trap and return at core boundaries.
module csr_file (
    input wire logic clk_i,rst_i,irq_external_i,
    input wire logic [11:0] addr_i,
    input wire logic [2:0] op_i,
    input wire logic [31:0] operand_i,
    input wire logic source_zero_i,rd_zero_i,commit_i,
    input wire logic trap_i,mret_i,
    input wire logic [31:2] trap_pc_i,
    input wire logic [31:0] trap_cause_i,trap_tval_i,
    output logic read_o,write_o,error_o,
    output logic [31:0] rdata_o,wdata_o,
    output wire logic [31:0] mtvec_o,mepc_o,
    output wire logic irq_enabled_o
);
    logic mie_q,mpie_q,meie_q;
    logic [31:0] vector_q,scratch_q,epc_q,cause_q,tval_q;
    logic known,readonly_reg,operation;
    logic [31:0] raw,mask,candidate,normalized;
    assign mtvec_o=vector_q;
    assign mepc_o=epc_q;
    assign irq_enabled_o=!rst_i && irq_external_i && meie_q && mie_q;
    always_comb begin
        raw=32'd0;mask=32'd0;known=1'b1;readonly_reg=1'b0;
        case(addr_i)
            12'h300:begin raw=32'h00001800 | (mie_q ? 32'h8 : 32'd0) | (mpie_q ? 32'h80 : 32'd0);mask=32'h88;end
            12'h301:raw=32'h40000100;
            12'h304:begin raw=meie_q ? 32'h800 : 32'd0;mask=32'h800;end
            12'h305:begin raw=vector_q;mask=32'hfffffffc;end
            12'h310:raw=32'd0;
            12'h340:begin raw=scratch_q;mask=32'hffffffff;end
            12'h341:begin raw=epc_q;mask=32'hfffffffc;end
            12'h342:begin raw=cause_q;mask=32'hffffffff;end
            12'h343:begin raw=tval_q;mask=32'hffffffff;end
            12'h344:raw=(!rst_i && irq_external_i) ? 32'h800 : 32'd0;
            12'hf11,12'hf12,12'hf13,12'hf14:begin raw=32'd0;readonly_reg=1'b1;end
            default:known=1'b0;
        endcase
        operation=(op_i==3'd1 || op_i==3'd2 || op_i==3'd3 || op_i==3'd5 || op_i==3'd6 || op_i==3'd7);
        read_o=operation && !((op_i[1:0]==2'd1) && rd_zero_i);
        write_o=operation && ((op_i[1:0]==2'd1) || !source_zero_i);
        error_o=(op_i!=3'd0) && (!operation || !known || (readonly_reg && write_o));
        candidate=operand_i;
        if(op_i[1:0]==2'd2) candidate=raw | operand_i;
        if(op_i[1:0]==2'd3) candidate=raw & ~operand_i;
        normalized=(raw & ~mask) | (candidate & mask);
        rdata_o=(read_o && !error_o) ? raw : 32'd0;
        wdata_o=(write_o && !error_o) ? normalized : 32'd0;
        if(rst_i || error_o)begin read_o=1'b0;write_o=1'b0;rdata_o=32'd0;wdata_o=32'd0;end
    end
    always_ff @(posedge clk_i) begin
        if(rst_i) begin
            mie_q<=1'b0;mpie_q<=1'b0;meie_q<=1'b0;
            vector_q<=32'd0;scratch_q<=32'd0;epc_q<=32'd0;cause_q<=32'd0;tval_q<=32'd0;
        end else if(trap_i) begin
            mpie_q<=mie_q;mie_q<=1'b0;
            epc_q<={trap_pc_i,2'b00};cause_q<=trap_cause_i;tval_q<=trap_tval_i;
        end else if(mret_i) begin mie_q<=mpie_q;mpie_q<=1'b1;
        end else if(commit_i && write_o && !error_o) begin
            case(addr_i)
                12'h300:begin mie_q<=normalized[3];mpie_q<=normalized[7];end
                12'h304:meie_q<=normalized[11];
                12'h305:vector_q<=normalized;
                12'h340:scratch_q<=normalized;
                12'h341:epc_q<=normalized;
                12'h342:cause_q<=normalized;
                12'h343:tval_q<=normalized;
                default:;
            endcase
        end
    end
endmodule
`default_nettype wire
