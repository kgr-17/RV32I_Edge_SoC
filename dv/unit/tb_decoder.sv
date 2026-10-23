`default_nettype none
module tb_decoder;
    timeunit 1ns;
    timeprecision 1ps;
    logic [31:0] insn = 32'h0000_0000;
    rv32_pkg::decode_t decoded;
    logic [56:0] expected;
    integer vector_file;
    integer scanned;
    integer checked = 0;
    integer unsigned seed;
    integer unsigned expected_count;
    string vector_path;
    decoder dut (.insn_i(insn), .decode_o(decoded));

    initial begin
        if ($bits(decoded) != 57) $fatal(1, "Decode interface width changed");
        if (!$value$plusargs("SEED=%d", seed)) $fatal(1, "Missing seed");
        if (!$value$plusargs("COUNT=%d", expected_count)) $fatal(1, "Missing count");
        if (expected_count == 0) $fatal(1, "Zero tests");
        if (!$value$plusargs("VECTORS=%s", vector_path)) $fatal(1, "Missing vectors");
        vector_file = $fopen(vector_path, "r");
        if (vector_file == 0) $fatal(1, "Cannot read vectors");
        while (!$feof(vector_file)) begin
            scanned = $fscanf(vector_file, "%h %h\n", insn, expected);
            if (scanned == 2) begin
                #1ns;
                if (decoded !== expected)
                    $fatal(1, "DECODE_MISMATCH seed=%0d row=%0d insn=%h actual=%h expected=%h",
                           seed, checked, insn, decoded, expected);
                checked = checked + 1;
            end else if (scanned != -1) begin
                $fatal(1, "Malformed decoder vector");
            end
        end
        $fclose(vector_file);
        if (checked != expected_count) $fatal(1, "Wrong count %0d != %0d", checked, expected_count);
        $display("DECODE_SIM_PASS seed=%0d checked=%0d", seed, checked);
        $finish;
    end
endmodule
`default_nettype wire
