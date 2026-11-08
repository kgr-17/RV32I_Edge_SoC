`timescale 1ns/1ps
`default_nettype none
// Directed literal ISA witness. An older slow load fills the fetch FIFO before
// CSR followed by ordinary ALU work, so removing serialization is observable.
module tb_interrupt_serialization;
    logic clk=1'b0,rst=1'b1,is=1'b0,ds=1'b0,pending=1'b0;
    logic [31:0] idata=32'd0;
    wire logic iv,ir,irdy,dv,dr,dw,dsr,rv,rdw,mv,mw,fv,tv,cv,cr,cw;
    wire logic [31:0] ia,da,dd,pc,np,insn,value,ma,md,mread,tp,ti,tc,tt,target,cd,nd;
    wire logic [63:0] order,trap_order;
    wire logic [4:0] rd;
    wire logic [3:0] be,mbe;
    wire logic [11:0] ca;
    integer seed,delay=0,requests=0,replies=0,retired=0;
    logic queued_consumer_witness=1'b0;
    assign ir=!rst && !is;assign dr=!rst && !pending && !ds;
    pipeline_core #(.ENABLE_TRAPS(1'b1)) dut(.clk_i(clk),.rst_i(rst),.irq_external_i(1'b0),
        .imem_req_valid_o(iv),.imem_req_ready_i(ir),.imem_req_addr_o(ia),.imem_rsp_valid_i(is),
        .imem_rsp_ready_o(irdy),.imem_rsp_rdata_i(idata),.imem_rsp_err_i(1'b0),
        .dmem_req_valid_o(dv),.dmem_req_ready_i(dr),.dmem_req_addr_o(da),.dmem_req_write_o(dw),
        .dmem_req_wdata_o(dd),.dmem_req_be_o(be),.dmem_rsp_valid_i(ds),.dmem_rsp_ready_o(dsr),
        .dmem_rsp_rdata_i(32'd5),.dmem_rsp_err_i(1'b0),.retire_valid_o(rv),.retire_order_o(order),
        .retire_pc_o(pc),.retire_next_pc_o(np),.retire_insn_o(insn),.retire_rd_write_o(rdw),.retire_rd_o(rd),
        .retire_rd_wdata_o(value),.retire_mem_valid_o(mv),.retire_mem_write_o(mw),.retire_mem_addr_o(ma),
        .retire_mem_be_o(mbe),.retire_mem_wdata_o(md),.retire_mem_rdata_o(mread),
        .fault_valid_o(fv),.fault_pc_o(),.fault_insn_o(),.fault_code_o(),.fault_tval_o(),
        .trap_valid_o(tv),.trap_order_o(trap_order),.trap_pc_o(tp),.trap_insn_o(ti),.trap_cause_o(tc),
        .trap_tval_o(tt),.trap_target_o(target),.retire_csr_valid_o(cv),.retire_csr_read_o(cr),
        .retire_csr_write_o(cw),.retire_csr_addr_o(ca),.retire_csr_rdata_o(cd),.retire_csr_wdata_o(nd));
    always #5 clk=~clk;
    function automatic logic [31:0] instruction(input logic [31:0] address);
        case(address)
            32'd0:instruction=32'h00010537; // lui x10,0x10
            32'd4:instruction=32'h3401d073; // csrrwi x0,mscratch,3
            32'd8:instruction=32'h00052083; // lw x1,0(x10)
            32'd12:instruction=32'h00900413; // addi x8,x0,9
            32'd16:instruction=32'h00b00493; // addi x9,x0,11
            32'd20:instruction=32'h34009173; // csrrw x2,mscratch,x1
            32'd24:instruction=32'h00110193; // addi x3,x2,1
            32'd28:instruction=32'h00700213; // addi x4,x0,7
            32'd32:instruction=32'h340212f3; // csrrw x5,mscratch,x4
            32'd36:instruction=32'h00228313; // addi x6,x5,2
            32'd40:instruction=32'h00330393; // addi x7,x6,3
            32'd44:instruction=32'h00000073; // ecall
            default:instruction=32'h00000013;
        endcase
    endfunction
    always_ff @(posedge clk) begin
        if(rst) begin is<=1'b0;idata<=32'd0;ds<=1'b0;pending<=1'b0;delay<=0;requests<=0;replies<=0;end
        else begin
            if(iv && ir)begin is<=1'b1;idata<=instruction(ia);end
            else if(is && irdy)begin is<=1'b0;idata<=32'd0;end
            if(dv && dr)begin
                if(da!==32'h00010000 || dw || be!==4'hf || dd!==32'd0)$fatal(1,"SERIAL_DATA_REQUEST");
                pending<=1'b1;delay<=24+(seed%16);requests<=requests+1;
            end
            if(pending)begin
                if(delay==0)begin pending<=1'b0;ds<=1'b1;end else delay<=delay-1;
            end
            if(ds && dsr)begin ds<=1'b0;replies<=replies+1;end
        end
    end
    logic [4:0] expected_rd;
    logic [31:0] expected_value;
    always @(posedge clk) begin
        if(!rst && !(dut.redirect || dut.control_redirect || dut.wb_fault || dut.fault_valid_o) &&
            dut.queue_flow_count !== (dut.queue_count_q-{1'b0,dut.queue_pop}+{1'b0,dut.queue_push}))
            $fatal(1,"IRQ_QUEUE_FLOW_EQUIVALENCE");
        if(!rst && dut.e_valid && dut.e.insn==32'h34009173 && dut.d_valid && dut.d.insn==32'h00110193)
            queued_consumer_witness=1'b1;
        if(!rst && dut.w_valid && (dut.w.result.csr_op!=3'd0 || dut.w.result.mret) &&
            (dut.e_valid || dut.m_valid))$fatal(1,"IRQ_SERIALIZATION_INVARIANT");
        #1;
        if(!rst)begin
            if(fv || (rv && tv))$fatal(1,"SERIAL_FAULT_OBSERVATION");
            if(rv)begin
                case(retired)
                    0:begin expected_rd=5'd10;expected_value=32'h00010000;end
                    1:begin expected_rd=5'd0;expected_value=32'd0;end
                    2:begin expected_rd=5'd1;expected_value=32'd5;end
                    3:begin expected_rd=5'd8;expected_value=32'd9;end
                    4:begin expected_rd=5'd9;expected_value=32'd11;end
                    5:begin expected_rd=5'd2;expected_value=32'd3;end
                    6:begin expected_rd=5'd3;expected_value=32'd4;end
                    7:begin expected_rd=5'd4;expected_value=32'd7;end
                    8:begin expected_rd=5'd5;expected_value=32'd5;end
                    9:begin expected_rd=5'd6;expected_value=32'd7;end
                    10:begin expected_rd=5'd7;expected_value=32'd10;end
                    default:$fatal(1,"SERIAL_EXTRA_RETIREMENT");
                endcase
                if(order!==64'(retired) || pc!==32'(retired*4) || np!==pc+32'd4 || insn!==instruction(pc) ||
                    rdw!==(expected_rd!=5'd0) || rd!==expected_rd || value!==expected_value)$fatal(1,"SERIAL_RETIREMENT_MISMATCH");
                if(mw || mv!==(retired==2) || ma!==((retired==2)?32'h10000:32'd0) || mbe!==((retired==2)?4'hf:4'h0) ||
                    md!==32'd0 || mread!==((retired==2)?32'd5:32'd0))$fatal(1,"SERIAL_MEMORY_MISMATCH");
                if(retired==1 || retired==5 || retired==8)begin
                    if(!cv || ca!==12'h340 || !cw || cr!==(retired!=1) ||
                        cd!==((retired==1)?32'd0:(retired==5)?32'd3:32'd5) ||
                        nd!==((retired==1)?32'd3:(retired==5)?32'd5:32'd7))$fatal(1,"SERIAL_CSR_MISMATCH");
                end else if(cv || cr || cw || ca!==12'd0 || cd!==32'd0 || nd!==32'd0)$fatal(1,"SERIAL_NONCSR_METADATA");
                retired=retired+1;
            end
            if(tv)begin
                if(retired!=11 || trap_order!==64'd11 || tp!==32'd44 || ti!==32'h73 || tc!==32'd11 || tt!==32'd0 ||
                    target!==32'd0 || requests!=1 || replies!=1)$fatal(1,"SERIAL_PRECISE_TRAP");
                if(!queued_consumer_witness)$fatal(1,"SERIAL_MISSING_QUEUED_CONSUMER");
                $display("CSR_SERIAL_PASS seed=%0d retired=11 requests=1 replies=1",seed);$finish;
            end
        end
    end
    initial begin
        if(!$value$plusargs("SEED=%d",seed))$fatal(1,"SERIAL_SEED_REQUIRED");
        repeat(4)@(negedge clk);rst=1'b0;
        repeat(2000)@(negedge clk);$fatal(1,"SERIAL_TIMEOUT");
    end
endmodule
`default_nettype wire
