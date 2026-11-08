`default_nettype none
// Five-stage pipeline integration under the reviewed v0.2 external contract.
module pipeline_core #(parameter bit ENABLE_TRAPS=1'b0) (
    input wire logic clk_i, rst_i,
`ifndef RV32_CORE_LEGACY_PORTS
    input wire logic irq_external_i,
`endif
    output wire logic imem_req_valid_o,
    input wire logic imem_req_ready_i,
    output wire logic [31:0] imem_req_addr_o,
    input wire logic imem_rsp_valid_i,
    output wire logic imem_rsp_ready_o,
    input wire logic [31:0] imem_rsp_rdata_i,
    input wire logic imem_rsp_err_i,
    output wire logic dmem_req_valid_o,
    input wire logic dmem_req_ready_i,
    output wire logic [31:0] dmem_req_addr_o,
    output wire logic dmem_req_write_o,
    output wire logic [31:0] dmem_req_wdata_o,
    output wire logic [3:0] dmem_req_be_o,
    input wire logic dmem_rsp_valid_i,
    output wire logic dmem_rsp_ready_o,
    input wire logic [31:0] dmem_rsp_rdata_i,
    input wire logic dmem_rsp_err_i,
    output logic retire_valid_o,
    output logic [63:0] retire_order_o,
    output logic [31:0] retire_pc_o, retire_next_pc_o, retire_insn_o,
    output logic retire_rd_write_o,
    output logic [4:0] retire_rd_o,
    output logic [31:0] retire_rd_wdata_o,
    output logic retire_mem_valid_o, retire_mem_write_o,
    output logic [31:0] retire_mem_addr_o,
    output logic [3:0] retire_mem_be_o,
    output logic [31:0] retire_mem_wdata_o, retire_mem_rdata_o,
    output logic fault_valid_o,
    output logic [31:0] fault_pc_o, fault_insn_o,
    output logic [3:0] fault_code_o,
    output logic [31:0] fault_tval_o,
    output logic trap_valid_o,
    output logic [63:0] trap_order_o,
    output logic [31:0] trap_pc_o,trap_insn_o,trap_cause_o,trap_tval_o,trap_target_o,
    output logic retire_csr_valid_o,retire_csr_read_o,retire_csr_write_o,
    output logic [11:0] retire_csr_addr_o,
    output logic [31:0] retire_csr_rdata_o,retire_csr_wdata_o
);
`ifdef RV32_CORE_LEGACY_PORTS
    // Unit synthesis specialization: the legacy configuration ties IRQ low.
    wire logic irq_external_i=1'b0;
    generate if(ENABLE_TRAPS) begin : g_invalid_legacy_ports
        initial $fatal(1,"LEGACY_PORTS_REQUIRE_TRAPS_OFF");
    end endgenerate
`endif
    import rv32_pkg::*;
    typedef struct packed {
        logic [31:0] pc,insn;
        logic fetch_error;
    } d_t;
    typedef struct packed {
        logic [31:0] pc,insn,a,b;
        decode_t dec;
        logic fetch_error;
    } e_t;
    typedef struct packed {
        logic [31:0] pc,insn,next_pc,value;
        logic write;
        logic [4:0] rd;
        logic mem,mwrite;
        logic [31:0] addr,wdata;
        logic [3:0] be,fault;
        logic [31:0] tval;
        logic [2:0] csr_op;
        logic [11:0] csr_addr;
        logic [31:0] csr_operand;
        logic csr_source_zero,csr_rd_zero,mret;

    } result_t;
    typedef struct packed { result_t result; op_t op; } m_t;
    typedef struct packed { result_t result; logic [31:0] raw; } w_t;
    wire logic f_valid,d_valid,e_valid,m_valid,w_valid;
    wire logic [31:0] fetch_pc;
    wire d_t d;
    wire e_t e;
    wire m_t m;
    wire w_t w;
    wire d_t fetch_queue [0:2];
    wire logic [2:0] queue_valid;
    d_t queue_next [0:2];
    logic [1:0] queue_count_q,queue_count_next;
    wire logic queue_pop,queue_room;
    assign d=fetch_queue[0];
    assign d_valid=queue_valid[0];
    d_t d_next;
    e_t e_next;
    m_t m_next;
    w_t w_next;
    decode_t decoded;
    wire logic [31:0] rf_a,rf_b,fa,fb,alu_b,alu_value,target,address,store_word,load_value;
    wire logic [1:0] source_a,source_b;
    wire logic blocked_a,blocked_b,wait_a,wait_b,dependency;
    wire logic alu_ok,branch_ok,taken,bad_target,lsu_ok,bad_address,lsu_write;
    // For branch/jump operations, LSU/ECALL/EBREAK faults are mutually
    // exclusive. Qualify redirects directly without the full fault encoder.
    wire logic branch_clean=!e.fetch_error && !e.dec.illegal && !bad_target;
    // Alignment is independent of taken for redirect qualification. The token
    // above retains the not-taken/no-fault semantics for verification.
    wire logic branch_redirect_clean=!e.fetch_error && !e.dec.illegal && (target[1:0]==2'b00);
    wire logic [3:0] byte_enable;
    wire logic wb_fault,wb_token_fault,gpr_write,mem_hold,front_hold,mem_complete;
    wire logic i_request,i_response,d_request,d_response,create_fetch;
    logic redirect;
    logic [31:0] next_fetch_pc_q;
    logic fetch_sent_q,fetch_killed_q,data_sent_q;
    logic [63:0] order_q;

    wire logic csr_read,csr_write,csr_error,irq_eligible,irq_draining,irq_block,irq_commit,irq_boundary;
    wire logic [31:0] csr_rdata,csr_wdata,csr_vector,csr_epc,irq_resume;
    wire logic sync_trap=ENABLE_TRAPS && wb_fault && !rst_i;
    wire logic mret_commit=ENABLE_TRAPS && w_valid && w.result.mret && !wb_fault && !rst_i;
    wire logic successful_retire=!rst_i && !fault_valid_o && w_valid && !wb_fault;
    wire logic trap_enter=sync_trap || irq_commit;
    wire logic control_redirect=sync_trap || mret_commit || irq_boundary;
    wire logic [31:0] control_target=(sync_trap || irq_commit) ? csr_vector : mret_commit ? csr_epc : irq_resume;
    wire logic [31:0] wb_value=(ENABLE_TRAPS && w.result.csr_op!=3'd0) ? csr_rdata : w.result.value;
    wire logic empty_pipeline=!f_valid && !d_valid && !e_valid && !m_valid && !w_valid && !fetch_sent_q && !data_sent_q;
    wire logic d_serial=ENABLE_TRAPS && d_valid && decoded.op>=OP_CSRRW;
    wire logic e_serial=ENABLE_TRAPS && e_valid && e.dec.op>=OP_CSRRW;
    wire logic m_serial=ENABLE_TRAPS && m_valid && (m.result.csr_op!=3'd0 || m.result.mret);
    wire logic w_serial=ENABLE_TRAPS && w_valid && (w.result.csr_op!=3'd0 || w.result.mret);
    wire logic serial_block=(d_serial && (e_valid || m_valid || w_valid)) || e_serial || m_serial || w_serial;
    wire logic [31:0] sync_cause;
    function automatic logic [31:0] mapped_cause(input logic [3:0] diagnostic);
        case(diagnostic)
            4'd1:mapped_cause=32'd2;
            4'd2:mapped_cause=32'd0;
            4'd3:mapped_cause=32'd1;
            4'd4:mapped_cause=32'd4;
            4'd5:mapped_cause=32'd5;
            4'd6:mapped_cause=32'd6;
            4'd7:mapped_cause=32'd7;
            4'd8:mapped_cause=32'd11;
            4'd9:mapped_cause=32'd3;
            default:mapped_cause=32'd2;
        endcase
    endfunction
    assign sync_cause=csr_error ? 32'd2 : mapped_cause(w.result.fault);
    assign wb_token_fault=w_valid && (w.result.fault!=4'd0);
    assign wb_fault=wb_token_fault || (w_valid && ENABLE_TRAPS && csr_error);
    generate if(ENABLE_TRAPS) begin : g_traps
        csr_file csrs(.clk_i(clk_i),.rst_i(rst_i),.irq_external_i(irq_external_i),
            .addr_i(w.result.csr_addr),.op_i(w.result.csr_op),.operand_i(w.result.csr_operand),
            .source_zero_i(w.result.csr_source_zero),.rd_zero_i(w.result.csr_rd_zero),.commit_i(successful_retire),
            .trap_i(trap_enter),.mret_i(mret_commit),.trap_pc_i(sync_trap ? w.result.pc[31:2] : irq_resume[31:2]),
            .trap_cause_i(sync_trap ? sync_cause : 32'h8000000b),.trap_tval_i(sync_trap ? (csr_error ? w.result.insn : w.result.tval) : 32'd0),
            .read_o(csr_read),.write_o(csr_write),.error_o(csr_error),.rdata_o(csr_rdata),.wdata_o(csr_wdata),
            .mtvec_o(csr_vector),.mepc_o(csr_epc),.irq_enabled_o(irq_eligible));
        trap_control admission(.clk_i(clk_i),.rst_i(rst_i),.eligible_i(irq_eligible),.empty_i(empty_pipeline),
            .sync_trap_i(sync_trap),.retire_i(successful_retire),.retire_next_pc_i(w.result.next_pc),.trap_target_i(csr_vector),
            .draining_o(irq_draining),.block_fetch_o(irq_block),.irq_commit_o(irq_commit),.boundary_o(irq_boundary),.resume_pc_o(irq_resume));
    end else begin : g_legacy
        assign csr_read=1'b0;assign csr_write=1'b0;assign csr_error=1'b0;
        assign csr_rdata=32'd0;assign csr_wdata=32'd0;assign csr_vector=32'd0;assign csr_epc=32'd0;
        assign irq_eligible=1'b0;assign irq_draining=1'b0;assign irq_block=1'b0;assign irq_commit=1'b0;assign irq_boundary=1'b0;assign irq_resume=32'd0;
    end endgenerate

    assign gpr_write=!rst_i && !fault_valid_o && w_valid && !wb_fault && w.result.write;
    decoder #(.ENABLE_TRAPS(ENABLE_TRAPS)) decode (.insn_i(d.insn),.decode_o(decoded));
    regfile registers (.clk_i(clk_i),.rst_i(rst_i),.write_en_i(gpr_write),
        .write_addr_i(w.result.rd),.write_data_i(wb_value),.read_addr_a_i(decoded.rs1),
        .read_addr_b_i(decoded.rs2),.read_data_a_o(rf_a),.read_data_b_o(rf_b));
    forwarding_unit forwarding (.valid_i(e_valid && !e.fetch_error),
        .uses_a_i(e.dec.uses_rs1),.uses_b_i(e.dec.uses_rs2),.rs_a_i(e.dec.rs1),.rs_b_i(e.dec.rs2),
        .captured_a_i(e.a),.captured_b_i(e.b),.ex_valid_i(m_valid),.ex_write_i(m.result.write),
        .ex_load_i(m.result.mem && !m.result.mwrite),.ex_rd_i(m.result.rd),.ex_value_i(m.result.value),
        // CSR/MRET serialize: no EX consumer exists while their WB is valid.
        // Write CSR results through the GPR port; keep CSR read/error decode out
        // of the same-cycle EX branch/address forwarding cone.
        .wb_valid_i(w_valid && w.result.fault==4'd0 && (!ENABLE_TRAPS || w.result.csr_op==3'd0)),
        .wb_write_i(w.result.write),.wb_rd_i(w.result.rd),.wb_value_i(w.result.value),
        .value_a_o(fa),.value_b_o(fb),.source_a_o(source_a),.source_b_o(source_b),
        .blocked_a_o(blocked_a),.blocked_b_o(blocked_b));
    hazard_unit hazards (.consumer_valid_i(e_valid && !e.fetch_error),
        .uses_a_i(e.dec.uses_rs1),.uses_b_i(e.dec.uses_rs2),.rs_a_i(e.dec.rs1),.rs_b_i(e.dec.rs2),
        .load_valid_i(m_valid),.load_write_i(m.result.write),.load_is_load_i(m.result.mem && !m.result.mwrite),
        .load_rd_i(m.result.rd),.wait_a_o(wait_a),.wait_b_o(wait_b),.stall_o(dependency));
    assign alu_b=((e.dec.op>=OP_ADDI)&&(e.dec.op<=OP_SRAI)) ? e.dec.imm : fb;
    assign address=fa+e.dec.imm;
    alu arithmetic (.op_i(e.dec.op),.a_i(fa),.b_i(alu_b),.result_o(alu_value),.supported_o(alu_ok));
    branch_unit #(.MASK_UNTAKEN_TARGET(1'b0)) branch (.op_i(e.dec.op),.pc_i(e.pc),.rs1_i(fa),.rs2_i(fb),.imm_i(e.dec.imm),
        .target_o(target),.taken_o(taken),.misaligned_o(bad_target),.supported_o(branch_ok));
    lsu ex_format (.op_i(e.dec.op),.byte_offset_i(address[1:0]),.store_data_i(fb),.read_word_i(32'd0),
        .load_data_o(),.store_word_o(store_word),.byte_enable_o(byte_enable),
        .write_o(lsu_write),.misaligned_o(bad_address),.supported_o(lsu_ok));
    lsu load_format (.op_i(m.op),.byte_offset_i(m.result.addr[1:0]),.store_data_i(32'd0),
        .read_word_i(dmem_rsp_rdata_i),.load_data_o(load_value),.store_word_o(),
        .byte_enable_o(),.write_o(),.misaligned_o(),.supported_o());

    // CSR operations serialize, so no younger MEM request/response can exist
    // during CSR WB validation. Token faults still suppress younger bus work;
    // keep the unrelated CSR address/permission decoder out of this bus cone.
    assign dmem_req_valid_o=!rst_i && !fault_valid_o && !wb_token_fault && m_valid && m.result.mem && !data_sent_q;
    assign dmem_req_addr_o=dmem_req_valid_o ? m.result.addr : 32'd0;
    assign dmem_req_write_o=dmem_req_valid_o && m.result.mwrite;
    assign dmem_req_be_o=dmem_req_valid_o ? m.result.be : 4'd0;
    assign dmem_req_wdata_o=dmem_req_valid_o ? m.result.wdata : 32'd0;
    assign dmem_rsp_ready_o=!rst_i && !fault_valid_o && !wb_token_fault && m_valid && m.result.mem && data_sent_q;
    assign d_request=dmem_req_valid_o && dmem_req_ready_i;
    assign d_response=dmem_rsp_valid_i && dmem_rsp_ready_o;
    assign mem_hold=m_valid && m.result.mem && !d_response;
    assign mem_complete=m_valid && (!m.result.mem || d_response);
    assign front_hold=mem_hold || dependency;
    assign queue_pop=d_valid && !front_hold && !serial_block && !redirect && !control_redirect && !wb_fault && !fault_valid_o;
    assign queue_room=(queue_count_q<2'd3) || queue_pop;

    // An offered/accepted instruction request is drained even after halt/kill.
    assign imem_req_valid_o=!rst_i && f_valid && !fetch_sent_q;
    assign imem_req_addr_o=imem_req_valid_o ? fetch_pc : 32'd0;
    assign imem_rsp_ready_o=!rst_i && f_valid && fetch_sent_q &&
        (fault_valid_o || wb_fault || fetch_killed_q || redirect || control_redirect || irq_block || queue_room);
    assign i_request=imem_req_valid_o && imem_req_ready_i;
    assign i_response=imem_rsp_valid_i && imem_rsp_ready_o;
    assign create_fetch=!rst_i && !fault_valid_o && !wb_fault && !redirect && !control_redirect && !irq_block && !d_serial && !e_serial && !m_serial && !w_serial && !f_valid && queue_room;
    wire logic queue_push=i_response && !fetch_killed_q && !redirect && !control_redirect && !irq_block && !wb_fault && !fault_valid_o;
    // Flush qualifies valid/count only. Speculative payload movement into a
    // now-invalid slot has no effect and need not wait for branch comparison.
    wire logic queue_payload_pop=d_valid && !front_hold && !serial_block;
    wire logic queue_payload_push=f_valid && fetch_sent_q && imem_rsp_valid_i;
    wire logic queue_flow_push=queue_payload_push && !fetch_killed_q && !irq_block &&
        ((queue_count_q<2'd3) || queue_payload_pop);
    wire logic [1:0] queue_flow_count=queue_count_q-{1'b0,queue_payload_pop}+{1'b0,queue_flow_push};
    // Speculatively prepare PC+4 without feeding the branch decision through
    // fetch admission first. A redirect overrides this value on the same edge.
    // Without a redirect this predicate equals create_fetch exactly.
    wire logic pc_prepare=!rst_i && !fault_valid_o && !wb_fault && !irq_block &&
        !d_serial && !e_serial && !m_serial && !w_serial && !f_valid &&
        ((queue_count_q<2'd3) || queue_payload_pop);
    wire logic pc_update=pc_prepare || redirect || control_redirect;
    wire logic [31:0] prepared_pc=control_redirect ? control_target : redirect ? target : next_fetch_pc_q+32'd4;

    always_comb begin
        m_next='0;
        m_next.op=e.dec.op;
        m_next.result.pc=e.pc;
        m_next.result.insn=e.insn;
        m_next.result.next_pc=e.pc+32'd4;
        m_next.result.write=e.dec.writes_rd;
        m_next.result.rd=e.dec.rd;
        if (alu_ok) m_next.result.value=alu_value;
        if (branch_ok && taken) m_next.result.next_pc=target;
        case (e.dec.op)
            OP_LUI: m_next.result.value=e.dec.imm;
            OP_AUIPC: m_next.result.value=e.pc+e.dec.imm;
            OP_JAL,OP_JALR: m_next.result.value=e.pc+32'd4;
            default: begin end
        endcase
        m_next.result.mem=lsu_ok;
        m_next.result.mwrite=lsu_write;
        m_next.result.addr=lsu_ok ? address : 32'd0;
        m_next.result.wdata=store_word;
        m_next.result.be=byte_enable;
        if (e.fetch_error) begin
            m_next.result.fault=4'd3;
            m_next.result.tval=e.pc;
        end else if (e.dec.illegal) begin
            m_next.result.fault=4'd1;
            m_next.result.tval=e.insn;
        end else if (e.dec.op==OP_ECALL) m_next.result.fault=4'd8;
        else if (e.dec.op==OP_EBREAK) m_next.result.fault=4'd9;
        else if (branch_ok && bad_target) begin
            m_next.result.fault=4'd2;
            m_next.result.tval=target;
        end else if (lsu_ok && bad_address) begin
            m_next.result.fault=((e.dec.op>=OP_SB)&&(e.dec.op<=OP_SW)) ? 4'd6 : 4'd4;
            m_next.result.tval=address;
        end
        if(ENABLE_TRAPS && e.dec.op>=OP_CSRRW && e.dec.op<=OP_CSRRCI) begin
            m_next.result.csr_op=e.insn[14:12];m_next.result.csr_addr=e.insn[31:20];
            m_next.result.csr_operand=e.insn[14] ? {27'd0,e.insn[19:15]} : fa;
            m_next.result.csr_source_zero=(e.insn[19:15]==5'd0);
            m_next.result.csr_rd_zero=(e.insn[11:7]==5'd0);
        end
        if(ENABLE_TRAPS && e.dec.op==OP_MRET) begin
            m_next.result.mret=1'b1;m_next.result.next_pc=csr_epc;
        end
        if (m_next.result.fault!=4'd0) begin
            m_next.result.write=1'b0;
            m_next.result.rd=5'd0;
            m_next.result.mem=1'b0;
        end
        redirect=e_valid && branch_ok && taken && branch_redirect_clean &&
            !mem_hold && !dependency && !blocked_a && !blocked_b &&
            !wb_fault && !fault_valid_o && !control_redirect && !(d_response && dmem_rsp_err_i) && !rst_i;
    end
    always_comb begin
        // Without a flush, flow pop/push equals accepted pop/push. During a
        // flush the direct clear_i wins, so valid bits need not wait for the
        // branch decision to traverse count encoding and threshold decoding.
        queue_count_next=queue_flow_count;
        for (int unsigned index=32'd0;index<32'd3;index=index+32'd1) queue_next[index]=fetch_queue[index];
        if (queue_payload_pop) begin
            queue_next[0]=fetch_queue[1];queue_next[1]=fetch_queue[2];queue_next[2]='0;
        end
        if (queue_payload_push) begin
            // Select the append slot directly from the registered count and
            // pop bit. Payload muxes need no subtract-then-decode carry path.
            for (int unsigned index=32'd0;index<32'd3;index=index+32'd1)
                if ((queue_payload_pop && queue_count_q==2'(index+32'd1)) || (!queue_payload_pop && queue_count_q==2'(index)))
                    queue_next[index]=d_next;
        end
        if (redirect || control_redirect || wb_fault || fault_valid_o) begin
            queue_count_next=2'd0;
        end
    end
    always_comb begin
        d_next='0;
        d_next.pc=fetch_pc;
        d_next.insn=imem_rsp_err_i ? 32'd0 : imem_rsp_rdata_i;
        d_next.fetch_error=imem_rsp_err_i;
        e_next='0;
        e_next.pc=d.pc;e_next.insn=d.insn;e_next.dec=decoded;
        e_next.a=rf_a;e_next.b=rf_b;e_next.fetch_error=d.fetch_error;
        if (front_hold) begin
            e_next=e;
            // Preserve a transient WB/EX bypass while a consumer is held.
            if (!wait_a && !blocked_a && source_a!=2'd0) e_next.a=fa;
            if (!wait_b && !blocked_b && source_b!=2'd0) e_next.b=fb;
        end
        w_next='0;
        w_next.result=m.result;
        if (m.result.mem) begin
            w_next.result.value=m.result.mwrite ? 32'd0 : load_value;
            w_next.raw=m.result.mwrite ? 32'd0 : dmem_rsp_rdata_i;
            if (dmem_rsp_err_i) begin
                w_next.result.fault=m.result.mwrite ? 4'd7 : 4'd5;
                w_next.result.tval=m.result.addr;
                w_next.result.write=1'b0;
                w_next.result.rd=5'd0;
            end
        end
    end
    rv32_pipeline_stage #(.WIDTH(32'd32),.MASK_PAYLOAD(1'b0),.PRELOAD_WHEN_EMPTY(1'b1)) if_stage (.clk_i(clk_i),.rst_i(rst_i),
        .clear_i(i_response),.hold_i(!create_fetch),.valid_i(1'b1),.payload_i(next_fetch_pc_q),
        .valid_o(f_valid),.payload_o(fetch_pc));
    // Responded words are FIFO buffers, not additional outstanding requests.
    for (genvar index=32'd0;index<32'd3;index=index+32'd1) begin : g_fetch_queue
        rv32_pipeline_stage #(.WIDTH($bits(d_t)),.MASK_PAYLOAD(1'b0),.CLEAR_INVALID_PAYLOAD(1'b0)) storage (.clk_i(clk_i),.rst_i(rst_i),
            .clear_i(wb_fault || fault_valid_o || redirect || control_redirect),.hold_i(1'b0),
            .valid_i(queue_flow_count>index),.payload_i(queue_next[index]),
            .valid_o(queue_valid[index]),.payload_o(fetch_queue[index]));
    end
    rv32_pipeline_stage #(.WIDTH($bits(e_t)),.MASK_PAYLOAD(1'b0),.CLEAR_INVALID_PAYLOAD(1'b0)) ex_stage (.clk_i(clk_i),.rst_i(rst_i),
        .clear_i(wb_fault || fault_valid_o || redirect || control_redirect),.hold_i(1'b0),
        .valid_i(front_hold ? e_valid : (d_valid && !serial_block)),.payload_i(e_next),.valid_o(e_valid),.payload_o(e));
    rv32_pipeline_stage #(.WIDTH($bits(m_t)),.MASK_PAYLOAD(1'b0),.CLEAR_INVALID_PAYLOAD(1'b0)) mem_stage (.clk_i(clk_i),.rst_i(rst_i),
        .clear_i(wb_fault || fault_valid_o || control_redirect),.hold_i(mem_hold),.valid_i(e_valid && !dependency && !blocked_a && !blocked_b),
        .payload_i(m_next),.valid_o(m_valid),.payload_o(m));
    rv32_pipeline_stage #(.WIDTH($bits(w_t)),.MASK_PAYLOAD(1'b0),.CLEAR_INVALID_PAYLOAD(1'b0)) wb_stage (.clk_i(clk_i),.rst_i(rst_i),
        .clear_i(wb_fault || fault_valid_o || control_redirect),.hold_i(1'b0),.valid_i(mem_complete),
        .payload_i(w_next),.valid_o(w_valid),.payload_o(w));

    always_ff @(posedge clk_i) begin
        if (rst_i) begin
            next_fetch_pc_q<=32'd0;fetch_sent_q<=1'b0;fetch_killed_q<=1'b0;data_sent_q<=1'b0;
            queue_count_q<=2'd0;
        end else begin
            queue_count_q<=queue_count_next;
            if (i_request) fetch_sent_q<=1'b1;
            if (i_response) begin fetch_sent_q<=1'b0;fetch_killed_q<=1'b0;end
            if (pc_update) next_fetch_pc_q<=prepared_pc;
            if ((redirect || control_redirect || irq_block || wb_fault || fault_valid_o) && f_valid && !i_response) fetch_killed_q<=1'b1;
            if (!mem_hold || wb_fault || fault_valid_o) data_sent_q<=1'b0;
            else if (d_request) data_sent_q<=1'b1;
        end
    end
    task automatic clear_trace;
        retire_valid_o<=1'b0;retire_order_o<=64'd0;
        retire_pc_o<=32'd0;retire_next_pc_o<=32'd0;retire_insn_o<=32'd0;
        retire_rd_write_o<=1'b0;retire_rd_o<=5'd0;retire_rd_wdata_o<=32'd0;
        retire_mem_valid_o<=1'b0;retire_mem_write_o<=1'b0;retire_mem_addr_o<=32'd0;
        retire_mem_be_o<=4'd0;retire_mem_wdata_o<=32'd0;retire_mem_rdata_o<=32'd0;
    endtask
    always_ff @(posedge clk_i) begin
        clear_trace();
        if (rst_i) begin
            order_q<=64'd0;fault_valid_o<=1'b0;fault_pc_o<=32'd0;
            fault_insn_o<=32'd0;fault_code_o<=4'd0;fault_tval_o<=32'd0;
        end else if (!fault_valid_o && w_valid) begin
            if (wb_fault) begin
                if(!ENABLE_TRAPS)begin
                fault_valid_o<=1'b1;fault_pc_o<=w.result.pc;fault_insn_o<=w.result.insn;
                fault_code_o<=w.result.fault;fault_tval_o<=w.result.tval;
                end
            end else begin
                retire_valid_o<=1'b1;retire_order_o<=order_q;
                retire_pc_o<=w.result.pc;retire_next_pc_o<=w.result.next_pc;retire_insn_o<=w.result.insn;
                retire_rd_write_o<=w.result.write;retire_rd_o<=w.result.rd;
                retire_rd_wdata_o<=w.result.write ? wb_value : 32'd0;
                retire_mem_valid_o<=w.result.mem;retire_mem_write_o<=w.result.mwrite;
                retire_mem_addr_o<=w.result.addr;retire_mem_be_o<=w.result.be;
                retire_mem_wdata_o<=w.result.wdata;retire_mem_rdata_o<=w.raw;
                order_q<=order_q+64'd1;
            end
        end
    end
    // Disabled features have constant observation outputs, not unused flops.
    generate if(ENABLE_TRAPS) begin : g_enabled_observation
        always_ff @(posedge clk_i) begin
        trap_valid_o<=1'b0;trap_order_o<=64'd0;trap_pc_o<=32'd0;trap_insn_o<=32'd0;
        trap_cause_o<=32'd0;trap_tval_o<=32'd0;trap_target_o<=32'd0;
        retire_csr_valid_o<=1'b0;retire_csr_read_o<=1'b0;retire_csr_write_o<=1'b0;
        retire_csr_addr_o<=12'd0;retire_csr_rdata_o<=32'd0;retire_csr_wdata_o<=32'd0;
            if(!rst_i) begin
                if(successful_retire && w.result.csr_op!=3'd0) begin
                    retire_csr_valid_o<=1'b1;retire_csr_addr_o<=w.result.csr_addr;
                    retire_csr_read_o<=csr_read;retire_csr_write_o<=csr_write;
                    retire_csr_rdata_o<=csr_rdata;retire_csr_wdata_o<=csr_wdata;
                end
            end
        if(!rst_i && trap_enter) begin
            trap_valid_o<=1'b1;trap_order_o<=order_q;
            trap_pc_o<=sync_trap ? w.result.pc : irq_resume;
            trap_insn_o<=sync_trap ? w.result.insn : 32'd0;
            trap_cause_o<=sync_trap ? sync_cause : 32'h8000000b;
            trap_tval_o<=sync_trap ? (csr_error ? w.result.insn : w.result.tval) : 32'd0;
            trap_target_o<=csr_vector;
        end
        end
    end else begin : g_legacy_observation
        assign trap_valid_o=1'b0;
        assign retire_csr_valid_o=1'b0;
        assign retire_csr_read_o=1'b0;
        assign retire_csr_write_o=1'b0;
        assign trap_order_o=64'd0;
        assign retire_csr_addr_o=12'd0;
        assign trap_pc_o=32'd0;
        assign trap_insn_o=32'd0;
        assign trap_cause_o=32'd0;
        assign trap_tval_o=32'd0;
        assign trap_target_o=32'd0;
        assign retire_csr_rdata_o=32'd0;
        assign retire_csr_wdata_o=32'd0;
    end endgenerate
endmodule
`default_nettype wire
