`default_nettype none
module tb_regfile;
    timeunit 1ns;
    timeprecision 1ps;
    logic clk = 1'b0;
    logic rst = 1'b0;
    logic write_en = 1'b0;
    logic [4:0] write_addr = 5'd0;
    logic [31:0] write_data = 32'd0;
    logic [4:0] read_a = 5'd0;
    logic [4:0] read_b = 5'd0;
    logic [31:0] data_a, data_b;
    logic vector_rst, vector_en, pulse;
    logic [4:0] vector_target, vector_a, vector_b;
    logic [31:0] vector_data, pre_a, pre_b, post_a, post_b;
    integer vector_file;
    integer scanned;
    integer checked = 0;
    integer unsigned seed;
    integer unsigned expected_count;
    string vector_path;
    always #5ns clk = ~clk;
    regfile dut (.clk_i(clk), .rst_i(rst), .write_en_i(write_en),
        .write_addr_i(write_addr), .write_data_i(write_data),
        .read_addr_a_i(read_a), .read_addr_b_i(read_b),
        .read_data_a_o(data_a), .read_data_b_o(data_b));
    task automatic compare(input logic [31:0] want_a, want_b, input string phase);
        if ((data_a !== want_a) || (data_b !== want_b))
            $fatal(1, "REGFILE_MISMATCH seed=%0d row=%0d phase=%s actual=%h/%h expected=%h/%h",
                   seed, checked, phase, data_a, data_b, want_a, want_b);
    endtask
    initial begin
        if (!$value$plusargs("SEED=%d", seed)) $fatal(1, "Missing seed");
        if (!$value$plusargs("COUNT=%d", expected_count)) $fatal(1, "Missing count");
        if (expected_count == 0) $fatal(1, "Zero tests");
        if (!$value$plusargs("VECTORS=%s", vector_path)) $fatal(1, "Missing vectors");
        vector_file = $fopen(vector_path, "r");
        if (vector_file == 0) $fatal(1, "Cannot read vectors");
        while (!$feof(vector_file)) begin
            scanned = $fscanf(vector_file, "%h %h %h %h %h %h %h %h %h %h %h\n",
                vector_rst, vector_en, vector_target, vector_data, vector_a, vector_b,
                pulse, pre_a, pre_b, post_a, post_b);
            if (scanned == 11) begin
                @(negedge clk);
                rst = vector_rst; write_en = vector_en;
                write_addr = vector_target; write_data = vector_data;
                read_a = vector_a; read_b = vector_b;
                #1ns;
                compare(pre_a, pre_b, "before-edge/bypass");
                if (pulse) begin
                    rst = 1'b1;
                    #1ns;
                    compare(32'd0, 32'd0, "reset-pulse-mask");
                    rst = 1'b0;
                    #1ns;
                    compare(pre_a, pre_b, "synchronous-state-retained");
                end
                @(posedge clk);
                #1ns;
                // Remove bypass so the post-edge check observes actual storage.
                write_en = 1'b0;
                #1ns;
                compare(post_a, post_b, "after-edge/bypass-disabled");
                checked = checked + 1;
            end else if (scanned != -1) $fatal(1, "Malformed register-file vector");
        end
        $fclose(vector_file);
        if (checked != expected_count) $fatal(1, "Wrong count %0d != %0d", checked, expected_count);
        $display("REGFILE_SIM_PASS seed=%0d checked=%0d", seed, checked);
        $finish;
    end
endmodule
`default_nettype wire
