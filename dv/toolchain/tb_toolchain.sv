`default_nettype none
module tb_toolchain;
    timeunit 1ns;
    timeprecision 1ps;
    logic clk = 1'b0;
    logic rst = 1'b0;
    logic enable = 1'b0;
    logic [31:0] data_in = 32'h0000_0000;
    logic [31:0] data_out;
    logic vector_rst;
    logic vector_enable;
    logic [31:0] vector_data;
    logic [31:0] expected_data;
    integer vector_file;
    integer scanned;
    integer checked = 0;
    integer unsigned seed;
    string vector_path;

    always #5ns clk = ~clk;
    register_fixture dut (.clk_i(clk), .rst_i(rst), .enable_i(enable), .data_i(data_in), .data_o(data_out));

    initial begin
        if (!$value$plusargs("SEED=%d", seed)) $fatal(1, "Missing seed");
        if (!$value$plusargs("VECTORS=%s", vector_path)) $fatal(1, "Missing vectors");
        if ($test$plusargs("INJECT_FATAL")) $fatal(1, "TOOLCHAIN_EXPECTED_FATAL");
        if ($test$plusargs("HANG")) begin
            integer hang_file;
            hang_file = $fopen("hang_started.txt", "w");
            if (hang_file == 0) $fatal(1, "Cannot record hang entry");
            $fdisplay(hang_file, "TOOLCHAIN_EXPECTED_HANG");
            $fclose(hang_file);
            forever @(posedge clk);
        end
        vector_file = $fopen(vector_path, "r");
        if (vector_file == 0) $fatal(1, "Cannot read vectors");
        while (!$feof(vector_file)) begin
            scanned = $fscanf(vector_file, "%h %h %h %h\n", vector_rst, vector_enable, vector_data, expected_data);
            if (scanned == 4) begin
                @(negedge clk);
                rst = vector_rst;
                enable = vector_enable;
                data_in = vector_data;
                @(posedge clk);
                #1ns;
                if (data_out !== expected_data) $fatal(1, "Mismatch row=%0d actual=%h expected=%h", checked, data_out, expected_data);
                checked = checked + 1;
            end else if (scanned != -1) begin
                $fatal(1, "Malformed vector row");
            end
        end
        $fclose(vector_file);
        if (checked != 134) $fatal(1, "Wrong vector count %0d", checked);
        if (!$test$plusargs("OMIT_PASS")) $display("TOOLCHAIN_SIM_PASS seed=%0d checked=%0d", seed, checked);
        $finish;
    end
endmodule
`default_nettype wire
