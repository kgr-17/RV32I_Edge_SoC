`default_nettype none
module csr_lint_top(
    input wire logic clk_i,rst_i,
    input wire logic [2:0] load_i,observe_i,
    input wire logic [31:0] data_i,
    output logic [31:0] data_o
);
    logic [31:0] operand_q,cause_q,tval_q;
    logic [31:2] pc_q;
    logic [20:0] control_q;
    always_ff @(posedge clk_i) begin
        if(rst_i)begin operand_q<=32'd0;pc_q<=30'd0;cause_q<=32'd0;tval_q<=32'd0;control_q<=21'd0;end
        else case(load_i)
            3'd0:operand_q<=data_i;
            3'd1:pc_q<=data_i[31:2];
            3'd2:cause_q<=data_i;
            3'd3:tval_q<=data_i;
            3'd4:control_q<=data_i[20:0];
            default:;
        endcase
    end
    wire logic rd,wr,error,enabled;
    wire logic [31:0] rdata,wdata,vector,epc;
    csr_file unit_csrs(.clk_i(clk_i),.rst_i(rst_i),.addr_i(control_q[11:0]),.op_i(control_q[14:12]),
        .operand_i(operand_q),.source_zero_i(control_q[15]),.rd_zero_i(control_q[16]),.commit_i(control_q[17]),
        .trap_i(control_q[18]),.mret_i(control_q[19]),.irq_external_i(control_q[20]),
        .trap_pc_i(pc_q),.trap_cause_i(cause_q),.trap_tval_i(tval_q),.read_o(rd),.write_o(wr),.error_o(error),
        .rdata_o(rdata),.wdata_o(wdata),.mtvec_o(vector),.mepc_o(epc),.irq_enabled_o(enabled));
    always_comb begin
        case(observe_i)
            3'd0:data_o={29'd0,rd,wr,error};
            3'd1:data_o=rdata;
            3'd2:data_o=wdata;
            3'd3:data_o=vector;
            3'd4:data_o=epc;
            3'd5:data_o={31'd0,enabled};
            default:data_o=32'd0;
        endcase
    end
endmodule
`default_nettype wire
