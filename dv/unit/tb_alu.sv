`default_nettype none
module tb_alu;
    timeunit 1ns;
    timeprecision 1ps;
    logic [5:0] op = 6'd0;
    logic [31:0] a = 32'd0;
    logic [31:0] b = 32'd0;
    logic [31:0] result;
    logic supported;
    logic [31:0] expected;
    logic expected_supported;
    integer vector_file;
    integer scanned;
    integer checked = 0;
    integer unsigned seed;
    integer unsigned expected_count;
    string vector_path;
    alu dut (.op_i(rv32_pkg::op_t'(op)), .a_i(a), .b_i(b), .result_o(result), .supported_o(supported));
    initial begin
        if (!$value$plusargs("SEED=%d", seed)) $fatal(1, "Missing seed");
        if (!$value$plusargs("COUNT=%d", expected_count)) $fatal(1, "Missing count");
        if (expected_count == 0) $fatal(1, "Zero tests");
        if (!$value$plusargs("VECTORS=%s", vector_path)) $fatal(1, "Missing vectors");
        vector_file = $fopen(vector_path, "r");
        if (vector_file == 0) $fatal(1, "Cannot read vectors");
        while (!$feof(vector_file)) begin
            scanned = $fscanf(vector_file, "%h %h %h %h %h\n", op, a, b, expected, expected_supported);
            if (scanned == 5) begin
                #1ns;
                if ((result !== expected) || (supported !== expected_supported))
                    $fatal(1, "ALU_MISMATCH seed=%0d row=%0d op=%h a=%h b=%h actual=%h/%b expected=%h/%b",
                           seed, checked, op, a, b, result, supported, expected, expected_supported);
                checked = checked + 1;
            end else if (scanned != -1) $fatal(1, "Malformed ALU vector");
        end
        $fclose(vector_file);
        if (checked != expected_count) $fatal(1, "Wrong count %0d != %0d", checked, expected_count);
        $display("ALU_SIM_PASS seed=%0d checked=%0d", seed, checked);
        $finish;
    end
endmodule
`default_nettype wire
