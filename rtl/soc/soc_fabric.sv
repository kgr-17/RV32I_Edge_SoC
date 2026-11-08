`default_nettype none
// Reviewed one-outstanding local buses. Memory/peripheral writes commit only
// at successful response acceptance; shared reset cancels unfinished traffic.
module soc_fabric #(
    parameter string ROM_INIT_FILE="soc_boot.mem",
    parameter int unsigned UART_CLKS_PER_BIT=32'd868,
    parameter bit ENABLE_IRQ=1'b0
) (
    input wire logic clk_i,rst_i,rx_i,
    input wire logic [15:0] switches_i,
    output wire logic tx_o,
    output wire logic [15:0] leds_o,
    output wire logic irq_o,
    input wire logic i_req_valid_i,
    output wire logic i_req_ready_o,
    input wire logic [31:0] i_req_addr_i,
    output wire logic i_rsp_valid_o,i_rsp_err_o,
    output wire logic [31:0] i_rsp_rdata_o,
    input wire logic i_rsp_ready_i,
    input wire logic d_req_valid_i,d_req_write_i,
    output wire logic d_req_ready_o,
    input wire logic [31:0] d_req_addr_i,d_req_wdata_i,
    input wire logic [3:0] d_req_be_i,
    output wire logic d_rsp_valid_o,d_rsp_err_o,
    output wire logic [31:0] d_rsp_rdata_o,
    input wire logic d_rsp_ready_i
);
    typedef enum logic [2:0] {BAD=3'd0,ROM=3'd1,RAM=3'd2,UART=3'd3,GPIO=3'd4,TIMER=3'd5} target_t;
    target_t target_q,decoded;
    logic i_pending_q,i_error_q,d_pending_q,pending_write_q;
    logic [13:0] pending_addr_q;
    logic [31:0] pending_data_q;
    logic [3:0] pending_be_q;
    wire logic iq_accept=i_req_valid_i && i_req_ready_o;
    wire logic dq_accept=d_req_valid_i && d_req_ready_o;
    wire logic i_bad=(|i_req_addr_i[31:16]) || (|i_req_addr_i[1:0]);
    wire logic [31:0] rom_i_data,rom_d_data,ram_data,uart_data,gpio_data,timer_data;
    wire logic uart_ready,uart_valid,uart_error,gpio_ready,gpio_valid,gpio_error,timer_ready,timer_valid,timer_error;
    wire logic uart_reply_ready=!rst_i && d_pending_q && target_q==UART && d_rsp_ready_i;
    wire logic gpio_reply_ready=!rst_i && d_pending_q && target_q==GPIO && d_rsp_ready_i;
    wire logic timer_reply_ready=!rst_i && d_pending_q && target_q==TIMER && d_rsp_ready_i;
    // A pending RAM target always has a valid, error-free local response;
    // a new RAM request is always ready when the transaction slot is empty.
    // Factor those RAM-specific cases directly instead of traversing the
    // unrelated UART/GPIO/timer handshake muxes before the BRAM enable pins.
    wire logic ram_write=!rst_i && d_pending_q && target_q==RAM && pending_write_q && d_rsp_ready_i;
    wire logic ram_read=!rst_i && !d_pending_q && d_req_valid_i && decoded==RAM && !d_req_write_i;
    function automatic logic legal_lanes(input logic [1:0] offset,input logic [3:0] lanes);
        case(lanes)
            4'b0001:legal_lanes=(offset==2'd0);
            4'b0010:legal_lanes=(offset==2'd1);
            4'b0100:legal_lanes=(offset==2'd2);
            4'b1000:legal_lanes=(offset==2'd3);
            4'b0011:legal_lanes=(offset==2'd0);
            4'b1100:legal_lanes=(offset==2'd2);
            4'b1111:legal_lanes=(offset==2'd0);
            default:legal_lanes=1'b0;
        endcase
    endfunction
    always_comb begin
        decoded=BAD;
        if(legal_lanes(d_req_addr_i[1:0],d_req_be_i)) begin
            if(d_req_addr_i[31:16]==16'h0000) begin if(!d_req_write_i) decoded=ROM;end
            else if(d_req_addr_i[31:16]==16'h0001) decoded=RAM;
            else if({d_req_addr_i[31:5],5'b00000}==32'h10000000) decoded=UART;
            else if({d_req_addr_i[31:5],5'b00000}==32'h10000020) decoded=GPIO;
            else if({d_req_addr_i[31:4],4'b0000}==32'h10000100) decoded=TIMER;
        end
    end
    assign i_req_ready_o=!rst_i && !i_pending_q;
    assign i_rsp_valid_o=!rst_i && i_pending_q;
    assign i_rsp_err_o=!rst_i && i_pending_q && i_error_q;
    assign i_rsp_rdata_o=(!rst_i && i_pending_q && !i_error_q) ? rom_i_data : 32'h00000000;
    assign d_req_ready_o=!rst_i && !d_pending_q &&
        (decoded==UART ? uart_ready : decoded==GPIO ? gpio_ready : decoded==TIMER ? timer_ready : 1'b1);
    assign d_rsp_valid_o=!rst_i && d_pending_q &&
        (target_q==UART ? uart_valid : target_q==GPIO ? gpio_valid : target_q==TIMER ? timer_valid : 1'b1);
    assign d_rsp_err_o=!rst_i && d_pending_q &&
        (target_q==BAD || (target_q==UART && uart_error) || (target_q==GPIO && gpio_error) || (target_q==TIMER && timer_error));
    assign d_rsp_rdata_o=(!rst_i && d_pending_q) ?
        (target_q==ROM ? rom_d_data : target_q==RAM ? (pending_write_q ? 32'h00000000 : ram_data) :
         target_q==UART ? uart_data : target_q==GPIO ? gpio_data : target_q==TIMER ? timer_data : 32'h00000000) : 32'h00000000;
    boot_rom #(.INIT_FILE(ROM_INIT_FILE)) rom(
        .clk_i(clk_i),.rst_i(rst_i),.a_en_i(iq_accept && !i_bad),.a_addr_i(i_req_addr_i[15:2]),
        .b_en_i(dq_accept && decoded==ROM),.b_addr_i(d_req_addr_i[15:2]),
        .a_valid_o(),.b_valid_o(),.a_data_o(rom_i_data),.b_data_o(rom_d_data));
    data_ram ram(.clk_i(clk_i),.rst_i(rst_i),.en_i(ram_read || ram_write),
        .addr_i(ram_read ? d_req_addr_i[15:2] : pending_addr_q),
        .write_be_i(ram_write ? pending_be_q : 4'b0000),.write_data_i(pending_data_q),.read_valid_o(),.read_data_o(ram_data));
    uart_mmio #(.CLKS_PER_BIT(UART_CLKS_PER_BIT)) uart(.clk_i(clk_i),.rst_i(rst_i),.rx_i(rx_i),
        .req_valid_i(!rst_i && !d_pending_q && d_req_valid_i && decoded==UART),.req_write_i(d_req_write_i),
        .req_addr_i(d_req_addr_i),.req_wdata_i(d_req_wdata_i[9:0]),.req_be_i(d_req_be_i),.req_ready_o(uart_ready),
        .rsp_valid_o(uart_valid),.rsp_err_o(uart_error),.rsp_rdata_o(uart_data),.rsp_ready_i(uart_reply_ready),.tx_o(tx_o));
    gpio gpio_unit(.clk_i(clk_i),.rst_i(rst_i),.switches_i(switches_i),.leds_o(leds_o),
        .req_valid_i(!rst_i && !d_pending_q && d_req_valid_i && decoded==GPIO),.req_write_i(d_req_write_i),
        .req_addr_i(d_req_addr_i),.req_wdata_i(d_req_wdata_i[15:0]),.req_be_i(d_req_be_i),.req_ready_o(gpio_ready),
        .rsp_valid_o(gpio_valid),.rsp_err_o(gpio_error),.rsp_rdata_o(gpio_data),.rsp_ready_i(gpio_reply_ready));
    timer #(.ENABLE_IRQ(ENABLE_IRQ)) timer_unit(.clk_i(clk_i),.rst_i(rst_i),.irq_o(irq_o),
        .req_valid_i(!rst_i && !d_pending_q && d_req_valid_i && decoded==TIMER),.req_write_i(d_req_write_i),
        .req_addr_i(d_req_addr_i),.req_wdata_i(d_req_wdata_i),.req_be_i(d_req_be_i),.req_ready_o(timer_ready),
        .rsp_valid_o(timer_valid),.rsp_err_o(timer_error),.rsp_rdata_o(timer_data),.rsp_ready_i(timer_reply_ready));
    always_ff @(posedge clk_i) begin
        if(rst_i) begin
            i_pending_q<=1'b0;i_error_q<=1'b0;d_pending_q<=1'b0;target_q<=BAD;
            pending_write_q<=1'b0;pending_addr_q<=14'd0;pending_data_q<=32'd0;pending_be_q<=4'd0;
        end else begin
            if(i_pending_q) begin
                if(i_rsp_ready_i) begin i_pending_q<=1'b0;i_error_q<=1'b0;end
            end else if(iq_accept) begin i_pending_q<=1'b1;i_error_q<=i_bad;end
            if(d_pending_q) begin
                if(d_rsp_valid_o && d_rsp_ready_i) begin
                    d_pending_q<=1'b0;target_q<=BAD;pending_write_q<=1'b0;
                    pending_addr_q<=14'd0;pending_data_q<=32'd0;pending_be_q<=4'd0;
                end
            end else if(dq_accept) begin
                d_pending_q<=1'b1;target_q<=decoded;pending_write_q<=d_req_write_i;
                pending_addr_q<=d_req_addr_i[15:2];pending_data_q<=d_req_wdata_i;pending_be_q<=d_req_be_i;
            end
        end
    end
endmodule
`default_nettype wire
