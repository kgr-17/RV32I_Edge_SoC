`timescale 1ns/1ps
`default_nettype none
module tb_board_io;
    logic clk = 1'b0;
    logic run_clock = 1'b1;
    logic btnC = 1'b0;
    logic [15:0] sw = 16'hffff;
    logic RsRx = 1'b0;
    wire [15:0] led;
    wire RsTx;
    basys3_diagnostic_top dut (.clk(clk), .btnC(btnC), .sw(sw), .RsRx(RsRx), .led(led), .RsTx(RsTx));
    always #5 if (run_clock) clk = ~clk;
    integer fd, fields, checked = 0, seed, r, rx, tx, rst;
    logic [15:0] switches, expected;
    string vectors;
    initial begin
        if (!$value$plusargs("SEED=%d", seed) || !$value$plusargs("VECTORS=%s", vectors))
            $fatal(1, "TOP_ARGUMENTS");
        // FPGA INIT: reset is held before any clock edge despite button low.
        #1;
        if (dut.rst_s !== 1'b1 || led !== 16'h0000 || RsTx !== 1'b1)
            $fatal(1, "TOP_STARTUP_RESET");
        repeat (6) @(negedge clk);
        run_clock = 1'b0;
        #2; btnC = 1'b1;
        #1;
        if (dut.rst_s !== 1'b1 || led !== 16'h0000 || RsTx !== 1'b1)
            $fatal(1, "TOP_ASYNC_ASSERT");
        #11; btnC = 1'b0;
        #13;
        if (dut.rst_s !== 1'b1) $fatal(1, "TOP_CLOCK_STOP_RELEASE");
        run_clock = 1'b1;
        fd = $fopen(vectors, "r");
        if (fd == 0) $fatal(1, "TOP_VECTOR_OPEN");
        fields = $fscanf(fd, "%h %h %h %h %h %h\n", r, switches, rx, expected, tx, rst);
        while (fields == 6) begin
            @(negedge clk); #2;
            btnC = (r != 0); sw = switches; RsRx = (rx != 0);
            #1;
            if (r != 0 && (led !== 16'h0000 || RsTx !== 1'b1 || dut.rst_s !== 1'b1))
                $fatal(1, "TOP_ASYNC_ASSERT");
            @(posedge clk); #1;
            if (led !== expected || RsTx !== (tx != 0) || dut.rst_s !== (rst != 0))
                $fatal(1, "TOP_MISMATCH checked=%0d led=%h expected=%h tx=%b expected_tx=%0d rst=%b expected_rst=%0d", checked, led, expected, RsTx, tx, dut.rst_s, rst);
            checked = checked + 1;
            fields = $fscanf(fd, "%h %h %h %h %h %h\n", r, switches, rx, expected, tx, rst);
        end
        if (checked == 0) $fatal(1, "TOP_EMPTY_VECTORS");
        if (fields > 0 || !$feof(fd)) $fatal(1, "TOP_MALFORMED_VECTOR");
        $fclose(fd);
        $display("TOP_SIM_PASS seed=%0d checked=%0d", seed, checked);
        $finish;
    end
    initial begin #100000; $fatal(1, "TOP_TEST_TIMEOUT"); end
endmodule
`default_nettype wire
