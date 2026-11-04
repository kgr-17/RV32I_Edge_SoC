`default_nettype none
// Simulation monitor. Temporal rules use explicit prior-edge state and immediate
// SystemVerilog assertions; no concurrent-SVA/formal support is inferred.
module core_properties (
    input wire logic clk_i, rst_i,
    input wire logic [4:0] read_addr_a_i, read_addr_b_i,
    input wire logic [31:0] read_data_a_i, read_data_b_i,
    input wire logic core_state_zero_i,
    input wire logic i_valid_i, i_ready_i,
    input wire logic [31:0] i_addr_i,
    input wire logic i_rsp_valid_i, i_rsp_ready_i,
    input wire logic d_valid_i, d_ready_i,
    input wire logic [31:0] d_addr_i, d_data_i,
    input wire logic [3:0] d_be_i,
    input wire logic d_write_i, d_rsp_valid_i, d_rsp_ready_i,
    input wire logic retire_valid_i,
    input wire logic [63:0] retire_order_i,
    input wire logic retire_write_i,
    input wire logic [4:0] retire_rd_i,
    input wire logic [31:0] retire_data_i,
    input wire logic fault_valid_i,
    input wire logic [99:0] fault_payload_i
);
    logic initialized_q = 1'b0;
    logic reset_q = 1'b0, i_stalled_q = 1'b0, d_stalled_q = 1'b0;
    logic i_pending_q = 1'b0, d_pending_q = 1'b0, fault_q = 1'b0;
    logic [31:0] i_addr_q;
    logic [68:0] d_payload_q;
    logic [99:0] fault_payload_q;
    logic [63:0] expected_order_q = 64'd0;
    // Cumulative witnesses survive per-scenario resets. They are simulation-only.
    logic [31:0] resets = 32'd0, x0_a = 32'd0, x0_b = 32'd0;
    logic [31:0] retires = 32'd0, i_holds = 32'd0, d_holds = 32'd0;
    logic [31:0] faults = 32'd0, i_requests = 32'd0, d_requests = 32'd0;

    always_ff @(posedge clk_i) begin
        if (rst_i) begin
            assert ({i_valid_i,i_rsp_ready_i,d_valid_i,d_rsp_ready_i} === 4'd0)
                else $fatal(1,"CORE_ASSERT_FAIL P_RESET_QUIET");
            initialized_q <= 1'b1;
            resets <= resets + 32'd1;
        end
        // At edge n, observe the state produced by reset at edge n-1. This also
        // checks the first released edge and avoids sampling before NBA reset.
        if (initialized_q && reset_q) begin
            assert (core_state_zero_i === 1'b1)
                else $fatal(1,"CORE_ASSERT_FAIL P_RESET_STATE");
        end
        if (initialized_q) begin
            if (read_addr_a_i === 5'd0) begin
                assert (read_data_a_i === 32'd0) else $fatal(1,"CORE_ASSERT_FAIL P_X0_A");
                x0_a <= x0_a + 32'd1;
            end
            if (read_addr_b_i === 5'd0) begin
                assert (read_data_b_i === 32'd0) else $fatal(1,"CORE_ASSERT_FAIL P_X0_B");
                x0_b <= x0_b + 32'd1;
            end
        end
        if (rst_i) begin
            expected_order_q <= 64'd0;
            i_pending_q <= 1'b0; d_pending_q <= 1'b0;
            i_stalled_q <= 1'b0; d_stalled_q <= 1'b0; fault_q <= 1'b0;
        end else if (initialized_q) begin
            if (i_stalled_q) begin
                assert (i_valid_i === 1'b1 && i_addr_i === i_addr_q)
                    else $fatal(1,"CORE_ASSERT_FAIL P_I_STABLE");
                i_holds <= i_holds + 32'd1;
            end
            if (d_stalled_q) begin
                assert (d_valid_i === 1'b1 && {d_addr_i,d_data_i,d_be_i,d_write_i} === d_payload_q)
                    else $fatal(1,"CORE_ASSERT_FAIL P_D_STABLE");
                d_holds <= d_holds + 32'd1;
            end
            // The reviewed local protocol permits neither unsolicited responses
            // nor replacement requests on the previous response's consume edge.
            if (i_valid_i && i_ready_i) begin
                assert (!i_pending_q) else $fatal(1,"CORE_ASSERT_FAIL P_I_SINGLE");
                i_pending_q <= 1'b1; i_requests <= i_requests + 32'd1;
            end
            if (i_rsp_valid_i && i_rsp_ready_i) begin
                assert (i_pending_q && !(i_valid_i && i_ready_i))
                    else $fatal(1,"CORE_ASSERT_FAIL P_I_RESPONSE");
                i_pending_q <= 1'b0;
            end
            if (d_valid_i && d_ready_i) begin
                assert (!d_pending_q) else $fatal(1,"CORE_ASSERT_FAIL P_D_SINGLE");
                d_pending_q <= 1'b1; d_requests <= d_requests + 32'd1;
            end
            if (d_rsp_valid_i && d_rsp_ready_i) begin
                assert (d_pending_q && !(d_valid_i && d_ready_i))
                    else $fatal(1,"CORE_ASSERT_FAIL P_D_RESPONSE");
                d_pending_q <= 1'b0;
            end
            if (retire_valid_i) begin
                assert (!fault_valid_i && retire_order_i === expected_order_q)
                    else $fatal(1,"CORE_ASSERT_FAIL P_RETIRE_ORDER");
                assert ((retire_write_i && retire_rd_i != 5'd0) ||
                        (!retire_write_i && {retire_rd_i,retire_data_i} === 37'd0))
                    else $fatal(1,"CORE_ASSERT_FAIL P_RETIRE_DEST");
                expected_order_q <= expected_order_q + 64'd1;
                retires <= retires + 32'd1;
            end
            if (fault_q) begin
                assert (fault_valid_i === 1'b1 && fault_payload_i === fault_payload_q &&
                        {retire_valid_i,d_valid_i,d_rsp_ready_i} === 3'd0)
                    else $fatal(1,"CORE_ASSERT_FAIL P_FAULT_STICKY");
                faults <= faults + 32'd1;
            end
            i_stalled_q <= i_valid_i && !i_ready_i;
            d_stalled_q <= d_valid_i && !d_ready_i;
            i_addr_q <= i_addr_i;
            d_payload_q <= {d_addr_i,d_data_i,d_be_i,d_write_i};
            fault_q <= fault_valid_i; fault_payload_q <= fault_payload_i;
        end
        reset_q <= rst_i;
    end
endmodule
`default_nettype wire
