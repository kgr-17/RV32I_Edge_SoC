`default_nettype none
// T025 board-only diagnostic shell. T031 replaces diagnostic connections with
// the verified SoC. No CPU, firmware, MMIO or UART controller is claimed here.
module basys3_diagnostic_top (
    input  wire logic        clk,
    input  wire logic        btnC,
    input  wire logic [15:0] sw,
    input  wire logic        RsRx,
    output logic [15:0] led,
    output logic        RsTx
);
    // FPGA INIT holds reset until two oscillator edges even without a button.
    // Physical bring-up must still explicitly press/release btnC.
    (* ASYNC_REG = "TRUE", SHREG_EXTRACT = "NO" *)
    logic [1:0] reset_release = 2'b11;
    logic rst_s;
    (* ASYNC_REG = "TRUE", SHREG_EXTRACT = "NO" *) logic [15:0] sw_meta;
    (* ASYNC_REG = "TRUE", SHREG_EXTRACT = "NO" *) logic [15:0] sw_sync;
    (* ASYNC_REG = "TRUE", SHREG_EXTRACT = "NO" *) logic rx_meta;
    (* ASYNC_REG = "TRUE", SHREG_EXTRACT = "NO" *) logic rx_sync;

    always_ff @(posedge clk or posedge btnC) begin
        if (btnC) reset_release <= 2'b11;
        else      reset_release <= {reset_release[0], 1'b0};
    end
    assign rst_s = reset_release[1];

    always_ff @(posedge clk) begin
        if (rst_s) begin
            sw_meta <= 16'h0000;
            sw_sync <= 16'h0000;
            rx_meta <= 1'b1;
            rx_sync <= 1'b1;
        end else begin
            sw_meta <= sw;
            sw_sync <= sw_meta;
            rx_meta <= RsRx;
            rx_sync <= rx_meta;
        end
    end
    // Selected pins remain live for board-boundary elaboration and DV.
    // Switch -> LED and synchronized serial loopback are diagnostic only.
    assign led  = rst_s ? 16'h0000 : sw_sync;
    assign RsTx = rst_s ? 1'b1 : rx_sync;
endmodule
`default_nettype wire
