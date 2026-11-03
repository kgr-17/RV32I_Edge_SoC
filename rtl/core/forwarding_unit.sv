`default_nettype none
module forwarding_unit (
    input wire logic valid_i, uses_a_i, uses_b_i,
    input wire logic [4:0] rs_a_i, rs_b_i,
    input wire logic [31:0] captured_a_i, captured_b_i,
    input wire logic ex_valid_i, ex_write_i, ex_load_i,
    input wire logic [4:0] ex_rd_i,
    input wire logic [31:0] ex_value_i,
    input wire logic wb_valid_i, wb_write_i,
    input wire logic [4:0] wb_rd_i,
    input wire logic [31:0] wb_value_i,
    output logic [31:0] value_a_o, value_b_o,
    output logic [1:0] source_a_o, source_b_o,
    output logic blocked_a_o, blocked_b_o
);
    // 0=captured/RF, 1=EX/MEM, 2=completed MEM/WB, 3=wait for younger load.
    // Both producers must be older than the consumer. Write qualification must
    // already exclude faulting/killed instructions; WB denotes completed data.
    typedef struct packed {
        logic [31:0] value;
        logic [1:0] source;
        logic blocked;
    } decision_t;
    decision_t a_decision,b_decision;
    function automatic decision_t resolve_operand (
        input logic used,
        input logic [4:0] source_reg,
        input logic [31:0] captured
    );
        decision_t result;
        begin
            result='0;
            if (valid_i && used && (source_reg!=5'd0)) begin
                result.value=captured;
                if (ex_valid_i && ex_write_i && (ex_rd_i!=5'd0) && (ex_rd_i==source_reg)) begin
                    if (ex_load_i) begin
                        result.value=32'd0;
                        result.source=2'd3;
                        result.blocked=1'b1;
                    end else begin
                        result.value=ex_value_i;
                        result.source=2'd1;
                    end
                end else if (wb_valid_i && wb_write_i && (wb_rd_i!=5'd0) && (wb_rd_i==source_reg)) begin
                    result.value=wb_value_i;
                    result.source=2'd2;
                end
            end
            resolve_operand=result;
        end
    endfunction
    always_comb begin
        a_decision=resolve_operand(uses_a_i,rs_a_i,captured_a_i);
        b_decision=resolve_operand(uses_b_i,rs_b_i,captured_b_i);
        {value_a_o,source_a_o,blocked_a_o}=a_decision;
        {value_b_o,source_b_o,blocked_b_o}=b_decision;
    end
endmodule
`default_nettype wire
