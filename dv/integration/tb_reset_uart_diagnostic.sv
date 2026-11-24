`timescale 1ns/1ps
`default_nettype none
// Diagnostic only: unchanged production top/firmware with explicit button pulses.
module tb_reset_uart_diagnostic;
    logic clk=1'b0,button=1'b1;
    wire logic tx;
    wire logic [15:0] leds;
    integer fd,mode,cycle=0;
    string trace_path;
    basys3_top board(.clk(clk),.btnC(button),.sw(16'h0000),.RsRx(1'b1),.led(leds),.RsTx(tx));
    always #5 clk=~clk;
    always @(posedge clk) begin
        #1;
        $fwrite(fd,"%0d %b %b %b\n",cycle,button,board.rst_s,tx);
        cycle=cycle+1;
    end
    initial begin
        if(!$value$plusargs("MODE=%d",mode)||!$value$plusargs("TRACE=%s",trace_path))$fatal(1,"RESET_UART_ARGUMENTS");
        if(mode!=0 && mode!=1)$fatal(1,"RESET_UART_MODE");
        fd=$fopen(trace_path,"w");if(fd==0)$fatal(1,"RESET_UART_TRACE");
        repeat(100)@(negedge clk);
        button=1'b0;
        if(mode==1) begin
            // Representative release-contact chatter: abort actual UART frames.
            // This stimulus illustrates a mechanism, not a measured switch waveform.
            wait(tx===1'b0);
            repeat(2704)@(negedge clk);button=1'b1;
            repeat(1000)@(negedge clk);button=1'b0;
            wait(tx===1'b0);
            repeat(1800)@(negedge clk);button=1'b1;
            repeat(5000)@(negedge clk);button=1'b0;
        end
        repeat(180000)@(negedge clk);
        $fclose(fd);
        $display("RESET_UART_DIAGNOSTIC_COMPLETE mode=%0d rows=%0d",mode,cycle);
        $finish;
    end
    initial begin #10000000;$fatal(1,"RESET_UART_TIMEOUT");end
endmodule
`default_nettype wire
