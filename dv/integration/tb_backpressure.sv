`default_nettype none
module tb_backpressure;
    timeunit 1ns; timeprecision 1ps;
    logic clk_i = '0;
    logic rst_i = '0;
    logic imem_req_valid_o;
    logic imem_req_ready_i = '0;
    logic [31:0] imem_req_addr_o;
    logic imem_rsp_valid_i = '0;
    logic imem_rsp_ready_o;
    logic [31:0] imem_rsp_rdata_i = '0;
    logic imem_rsp_err_i = '0;
    logic dmem_req_valid_o;
    logic dmem_req_ready_i = '0;
    logic [31:0] dmem_req_addr_o;
    logic dmem_req_write_o;
    logic [31:0] dmem_req_wdata_o;
    logic [3:0] dmem_req_be_o;
    logic dmem_rsp_valid_i = '0;
    logic dmem_rsp_ready_o;
    logic [31:0] dmem_rsp_rdata_i = '0;
    logic dmem_rsp_err_i = '0;
    logic retire_valid_o;
    logic [63:0] retire_order_o;
    logic [31:0] retire_pc_o;
    logic [31:0] retire_next_pc_o;
    logic [31:0] retire_insn_o;
    logic retire_rd_write_o;
    logic [4:0] retire_rd_o;
    logic [31:0] retire_rd_wdata_o;
    logic retire_mem_valid_o;
    logic retire_mem_write_o;
    logic [31:0] retire_mem_addr_o;
    logic [3:0] retire_mem_be_o;
    logic [31:0] retire_mem_wdata_o;
    logic [31:0] retire_mem_rdata_o;
    logic fault_valid_o;
    logic [31:0] fault_pc_o;
    logic [31:0] fault_insn_o;
    logic [3:0] fault_code_o;
    logic [31:0] fault_tval_o;
    always #5ns clk_i = ~clk_i;
    pipeline_core dut (
        .clk_i(clk_i),
        .rst_i(rst_i),
        .imem_req_valid_o(imem_req_valid_o),
        .imem_req_ready_i(imem_req_ready_i),
        .imem_req_addr_o(imem_req_addr_o),
        .imem_rsp_valid_i(imem_rsp_valid_i),
        .imem_rsp_ready_o(imem_rsp_ready_o),
        .imem_rsp_rdata_i(imem_rsp_rdata_i),
        .imem_rsp_err_i(imem_rsp_err_i),
        .dmem_req_valid_o(dmem_req_valid_o),
        .dmem_req_ready_i(dmem_req_ready_i),
        .dmem_req_addr_o(dmem_req_addr_o),
        .dmem_req_write_o(dmem_req_write_o),
        .dmem_req_wdata_o(dmem_req_wdata_o),
        .dmem_req_be_o(dmem_req_be_o),
        .dmem_rsp_valid_i(dmem_rsp_valid_i),
        .dmem_rsp_ready_o(dmem_rsp_ready_o),
        .dmem_rsp_rdata_i(dmem_rsp_rdata_i),
        .dmem_rsp_err_i(dmem_rsp_err_i),
        .retire_valid_o(retire_valid_o),
        .retire_order_o(retire_order_o),
        .retire_pc_o(retire_pc_o),
        .retire_next_pc_o(retire_next_pc_o),
        .retire_insn_o(retire_insn_o),
        .retire_rd_write_o(retire_rd_write_o),
        .retire_rd_o(retire_rd_o),
        .retire_rd_wdata_o(retire_rd_wdata_o),
        .retire_mem_valid_o(retire_mem_valid_o),
        .retire_mem_write_o(retire_mem_write_o),
        .retire_mem_addr_o(retire_mem_addr_o),
        .retire_mem_be_o(retire_mem_be_o),
        .retire_mem_wdata_o(retire_mem_wdata_o),
        .retire_mem_rdata_o(retire_mem_rdata_o),
        .fault_valid_o(fault_valid_o),
        .fault_pc_o(fault_pc_o),
        .fault_insn_o(fault_insn_o),
        .fault_code_o(fault_code_o),
        .fault_tval_o(fault_tval_o)
    );
    logic [31:0] rom [0:16383], ram [0:16383], expected_ram [0:16383];
    logic [31:0] expected [0:2047][0:11];
    logic [31:0] fields [0:11];
    logic [31:0] fault_pc, fault_insn, fault_tval;
    logic [3:0] fault_code;
    logic [31:0] ia, da, dw, held_iaddr, held_daddr, held_dw;
    logic [3:0] db, held_db;
    logic dwrite, held_dwrite;
    bit ipending, dpending, iheld, dheld, isnapshot, dsnapshot;
    integer vector_file, scanned, kind, checked=0, expected_count, expected_size=0;
    integer scenario=0, scenarios=0, retired, cycles, idue, ddue, ifetches, drequests, successes, memretires;
    integer total_retired=0, total_cycles=0;
    integer hazard_cycles=0,refresh_cycles=0,quiet=0,if_completed=0;
    integer redirects=0,deferred_redirects=0,suppressed_stores=0,killed_fetch_errors=0;
    integer case_deferred,case_suppressed,case_killed,case_hazards;
    integer i_request_stalls=0,d_request_stalls=0,max_data_age=0,data_accept_cycle=0;
    bit terminated=0;
    integer unsigned seed, random_state;
    string vector_path;

    task automatic fail(input string message);
        $fatal(1,"BACKPRESSURE_MISMATCH %s seed=%0d scenario=%0d cycle=%0d retired=%0d",message,seed,scenario,cycles,retired);
    endtask

    task automatic run_case;
        @(negedge clk_i);
        rst_i=1'b1;
        imem_req_ready_i=1'b0; dmem_req_ready_i=1'b0;
        imem_rsp_valid_i=1'b0; dmem_rsp_valid_i=1'b0;
        imem_rsp_rdata_i=32'd0; dmem_rsp_rdata_i=32'd0;
        imem_rsp_err_i=1'b0; dmem_rsp_err_i=1'b0;
        ipending=0; dpending=0; iheld=0; dheld=0; isnapshot=0; dsnapshot=0;
        case_deferred=deferred_redirects;case_suppressed=suppressed_stores;case_killed=killed_fetch_errors;case_hazards=hazard_cycles;
        retired=0; cycles=0; ifetches=0; terminated=0; quiet=0; if_completed=0; drequests=0; successes=0; memretires=0;
        repeat (2) begin
            @(posedge clk_i); #1ns;
            if (imem_req_valid_o || imem_rsp_ready_o || dmem_req_valid_o || dmem_rsp_ready_o || retire_valid_o || fault_valid_o)
                fail("reset outputs");
        end
        @(negedge clk_i); rst_i=1'b0;
        for (cycles=0;cycles<20000;cycles=cycles+1) begin
            random_state={random_state[30:0],random_state[31]^random_state[21]^random_state[1]^random_state[0]};
            imem_req_ready_i=!ipending && ((scenario<21) || (random_state[0] && cycles%13>=2));
            dmem_req_ready_i=!dpending && random_state[1] && ((scenario<21) || cycles%17>=3);
            imem_rsp_valid_i=ipending && (cycles>=idue);
            dmem_rsp_valid_i=dpending && (cycles>=ddue);
            if (imem_rsp_valid_i && !isnapshot) begin
                imem_rsp_err_i=(ia>=32'h00010000) || (ia[1:0]!=2'b00);
                imem_rsp_rdata_i=imem_rsp_err_i ? 32'd0 : rom[ia/4];
                isnapshot=1;
            end
            if (dmem_rsp_valid_i && !dsnapshot) begin
                dmem_rsp_err_i=!((da<32'h00010000 && !dwrite) || (da>=32'h00010000 && da<32'h00020000));
                dmem_rsp_rdata_i=32'd0;
                if (!dmem_rsp_err_i && !dwrite) begin
                    if (da<32'h00010000) dmem_rsp_rdata_i=rom[da/4];
                    else dmem_rsp_rdata_i=ram[(da-32'h00010000)/4];
                end
                dsnapshot=1;
            end
            @(posedge clk_i);
            if (scenario>=21) begin
                if (imem_req_valid_o && !imem_req_ready_i) i_request_stalls=i_request_stalls+1;
                if (dmem_req_valid_o && !dmem_req_ready_i) d_request_stalls=d_request_stalls+1;
                if (dpending && cycles-data_accept_cycle>max_data_age) max_data_age=cycles-data_accept_cycle;
            end
            if (terminated && imem_req_valid_o && !iheld && !ipending) fail("new fetch after halt");
            if (iheld && (!imem_req_valid_o || imem_req_addr_o!==held_iaddr)) fail("instruction offer changed");
            if (dheld && (!dmem_req_valid_o || {dmem_req_addr_o,dmem_req_wdata_o,dmem_req_be_o,dmem_req_write_o} !==
                                              {held_daddr,held_dw,held_db,held_dwrite})) fail("data offer changed");
            iheld=imem_req_valid_o && !imem_req_ready_i;
            dheld=dmem_req_valid_o && !dmem_req_ready_i;
            held_iaddr=imem_req_addr_o;
            held_daddr=dmem_req_addr_o; held_dw=dmem_req_wdata_o;
            held_db=dmem_req_be_o; held_dwrite=dmem_req_write_o;
            if (imem_req_valid_o && imem_req_ready_i && ipending) fail("duplicate instruction acceptance");
            if (dmem_req_valid_o && dmem_req_ready_i && dpending) fail("duplicate data acceptance");
            if (imem_rsp_valid_i && imem_rsp_ready_o) begin ipending=0; isnapshot=0; if_completed=if_completed+1; end
            if (dmem_rsp_valid_i && dmem_rsp_ready_o) begin
                if (!dmem_rsp_err_i) begin
                    successes=successes+1;
                    if (dwrite) begin
                        for (int lane=0;lane<4;lane=lane+1)
                            if (db[lane]) ram[(da-32'h00010000)/4][lane*8 +: 8]=dw[lane*8 +: 8];
                    end
                end
                dpending=0; dsnapshot=0;
            end
            if (imem_req_valid_o && imem_req_ready_i) begin
                if (imem_req_addr_o[1:0]!=2'b00) fail("unaligned instruction request");
                ia=imem_req_addr_o; ipending=1; idue=cycles+1+((scenario<21) ? 0 : int'(random_state[3:2]));
                ifetches=ifetches+1;
            end
            if (dmem_req_valid_o && dmem_req_ready_i) begin
                da=dmem_req_addr_o; dw=dmem_req_wdata_o; db=dmem_req_be_o; dwrite=dmem_req_write_o;
                case (db)
                    4'b0001: if (da[1:0]!=0) fail("byte lane 0");
                    4'b0010: if (da[1:0]!=1) fail("byte lane 1");
                    4'b0100: if (da[1:0]!=2) fail("byte lane 2");
                    4'b1000: if (da[1:0]!=3) fail("byte lane 3");
                    4'b0011: if (da[1:0]!=0) fail("half lane 0");
                    4'b1100: if (da[1:0]!=2) fail("half lane 2");
                    4'b1111: if (da[1:0]!=0) fail("word lane");
                    default: fail("invalid byte mask");
                endcase
                for (int lane=0;lane<4;lane=lane+1)
                    if ((!db[lane] || !dwrite) && dw[lane*8 +: 8]!==8'd0) fail("unused data lane nonzero");
                dpending=1; data_accept_cycle=cycles;
                if (scenario<21) ddue=cycles+12+random_state[5:4];
                else ddue=cycles+((drequests==0) ? 32 : 1+int'(random_state[8:4]));
                drequests=drequests+1;
            end
            if (dut.redirect) redirects=redirects+1;
            if (dut.e_valid && dut.branch_ok && dut.taken && !dut.bad_target && dut.mem_hold && !dut.blocked_a && !dut.blocked_b) deferred_redirects=deferred_redirects+1;
            if (dut.wb_fault && dut.m_valid && dut.m.result.mem && dut.m.result.mwrite) begin
                suppressed_stores=suppressed_stores+1;
                if (dmem_req_valid_o) fail("younger store offered behind WB fault");
            end
            if (dut.i_response && dut.fetch_killed_q && imem_rsp_err_i) killed_fetch_errors=killed_fetch_errors+1;
            if (dut.dependency && dut.e_valid) hazard_cycles=hazard_cycles+1;
            if (dut.front_hold && dut.e_valid && ((dut.source_a==2) || (dut.source_b==2))) refresh_cycles=refresh_cycles+1;
            #1ns;
            if (retire_valid_o) begin
                if (fault_valid_o || retired>=expected_size || retire_order_o!==64'(retired)) fail("retire count/order");
                if ({retire_pc_o,retire_insn_o,retire_next_pc_o,retire_rd_write_o,retire_rd_o,retire_rd_wdata_o,
                     retire_mem_valid_o,retire_mem_write_o,retire_mem_addr_o,retire_mem_be_o,retire_mem_wdata_o,retire_mem_rdata_o} !==
                    {expected[retired][0],expected[retired][1],expected[retired][2],expected[retired][3][0],
                     expected[retired][4][4:0],expected[retired][5],expected[retired][6][0],expected[retired][7][0],
                     expected[retired][8],expected[retired][9][3:0],expected[retired][10],expected[retired][11]}) begin
                    $display("ACTUAL pc=%h insn=%h next=%h rd=%d value=%h mem=%h be=%h raw=%h",retire_pc_o,retire_insn_o,
                        retire_next_pc_o,retire_rd_o,retire_rd_wdata_o,retire_mem_addr_o,retire_mem_be_o,retire_mem_rdata_o);
                    $display("EXPECTED pc=%h insn=%h next=%h rd=%d value=%h mem=%h be=%h raw=%h",expected[retired][0],expected[retired][1],
                        expected[retired][2],expected[retired][4],expected[retired][5],expected[retired][8],expected[retired][9],expected[retired][11]);
                    fail("retirement fields");
                end
                if (retire_mem_valid_o) begin
                    memretires=memretires+1;
                    if (memretires!=successes) fail("memory effect/retire count");
                    if (retire_mem_write_o) begin
                        for (int lane=0;lane<4;lane=lane+1)
                            if (retire_mem_be_o[lane]) expected_ram[(retire_mem_addr_o-32'h00010000)/4][lane*8 +: 8]=retire_mem_wdata_o[lane*8 +: 8];
                    end
                end
                $display("BACKPRESSURE_RETIRE %0d %016h %08h %08h %08h %h %h %08h %h %h %08h %h %08h %08h",
                    scenario,retire_order_o,retire_pc_o,retire_insn_o,retire_next_pc_o,retire_rd_write_o,retire_rd_o,
                    retire_rd_wdata_o,retire_mem_valid_o,retire_mem_write_o,retire_mem_addr_o,retire_mem_be_o,
                    retire_mem_wdata_o,retire_mem_rdata_o);
                retired=retired+1;
            end
            if (fault_valid_o && !terminated) begin
                terminated=1;
                if ({fault_pc_o,fault_insn_o,fault_code_o,fault_tval_o} !== {fault_pc,fault_insn,fault_code,fault_tval}) fail("fault fields");
                if (retired!=expected_size || dpending || successes!=memretires ||
                    drequests!=memretires+int'(fault_code==4'd5 || fault_code==4'd7)) fail("termination accounting");
                for (int word_index=0;word_index<16384;word_index=word_index+1)
                    if (ram[word_index]!==expected_ram[word_index]) fail("final RAM bytes");
                $display("BACKPRESSURE_FAULT %0d %08h %08h %h %08h",scenario,fault_pc_o,fault_insn_o,fault_code_o,fault_tval_o);
                for (int reg_index=1;reg_index<32;reg_index=reg_index+1)
                    $display("BACKPRESSURE_GPR %0d %0d %08h",scenario,reg_index,dut.registers.registers[reg_index]);
                for (int word_index=0;word_index<32;word_index=word_index+1)
                    $display("BACKPRESSURE_RAM %0d %0d %08h",scenario,word_index,ram[word_index]);
            end
            if (terminated) begin
                if (!fault_valid_o || retire_valid_o || dmem_req_valid_o ||
                    {fault_pc_o,fault_insn_o,fault_code_o,fault_tval_o} !== {fault_pc,fault_insn,fault_code,fault_tval}) fail("halt stability");
                if (!ipending && !iheld && !imem_req_valid_o) quiet=quiet+1;
                else quiet=0;
                if (quiet>=8) begin
                    if (if_completed!=ifetches) fail("instruction drain accounting");
                    if ((scenario==16 || scenario==17) && deferred_redirects==case_deferred) fail("vacuous memory-hold redirect case");
                    if (scenario==18 && hazard_cycles==case_hazards) fail("vacuous load-dependent JALR");
                    if (scenario==19 && suppressed_stores==case_suppressed) fail("vacuous older-fault store suppression");
                    if (scenario==20 && killed_fetch_errors==case_killed) fail("vacuous killed-fetch-error case");
                    $display("BACKPRESSURE_CASE_COLLISIONS scenario=%0d deferred=%0d suppressed=%0d killed_errors=%0d hazards=%0d",scenario,deferred_redirects-case_deferred,suppressed_stores-case_suppressed,killed_fetch_errors-case_killed,hazard_cycles-case_hazards);

                    total_retired=total_retired+retired; total_cycles=total_cycles+cycles+1;
                    scenarios=scenarios+1;
                    $display("BACKPRESSURE_CASE_PASS seed=%0d scenario=%0d retired=%0d cycles=%0d",seed,scenario,retired,cycles+1);
                    break;
                end
            end
            @(negedge clk_i);
        end
        if (cycles>=20000) fail("bounded progress timeout");
        @(negedge clk_i); rst_i=1;
    endtask

    initial begin
        rst_i=1;
        if (!$value$plusargs("SEED=%d",seed)) $fatal(1,"Missing seed");
        random_state=seed;
        if (!$value$plusargs("COUNT=%d",expected_count) || expected_count==0) $fatal(1,"Zero tests");
        if (!$value$plusargs("VECTORS=%s",vector_path)) $fatal(1,"Missing vectors");
        vector_file=$fopen(vector_path,"r");
        if (vector_file==0) $fatal(1,"Cannot read vectors");
        while (!$feof(vector_file)) begin
            scanned=$fscanf(vector_file,"%h %h %h %h %h %h %h %h %h %h %h %h %h\n",kind,
                fields[0],fields[1],fields[2],fields[3],fields[4],fields[5],fields[6],fields[7],fields[8],fields[9],fields[10],fields[11]);
            if (scanned==13) begin
                checked=checked+1;
                case (kind)
                    0: begin
                        fault_pc=fields[0]; fault_insn=fields[1]; fault_code=fields[2][3:0];
                        expected_size=fields[3]; scenario=fields[4]; fault_tval=fields[11];
                        if (expected_size>2048) fail("too many expectations");
                        for (int n=0;n<16384;n=n+1) begin rom[n]=32'd0; ram[n]=32'd0; expected_ram[n]=32'd0; end
                        retired=0;
                    end
                    1: begin
                        if (fields[0]>=65536 || fields[0]%4!=0) fail("bad ROM initialization");
                        rom[fields[0]/4]=fields[1];
                    end
                    2: begin
                        if (fields[0]<65536 || fields[0]>=131072 || fields[0]%4!=0) fail("bad RAM initialization");
                        ram[(fields[0]-65536)/4]=fields[1]; expected_ram[(fields[0]-65536)/4]=fields[1];
                    end
                    3: begin
                        if (retired>=expected_size) fail("excess expectations");
                        for (int n=0;n<12;n=n+1) expected[retired][n]=fields[n];
                        retired=retired+1;
                    end
                    4: begin
                        if (retired!=expected_size) fail("missing expectations");
                        run_case();
                    end
                    default: fail("unknown input record");
                endcase
            end else if (scanned!=-1) $fatal(1,"Malformed core vectors");
        end
        $fclose(vector_file);
        if (checked!=expected_count) $fatal(1,"Wrong count %0d != %0d",checked,expected_count);
        if (scenarios==0) fail("zero scenarios");
        if (hazard_cycles==0 || refresh_cycles==0) fail("unhit integration hazard/held-WB-refresh bins");
        if (redirects==0 || deferred_redirects==0 || suppressed_stores==0 || killed_fetch_errors==0) fail("unhit control/age collision bins");
        if (i_request_stalls==0 || d_request_stalls==0 || max_data_age<32) fail("unhit randomized wait bins");
        $display("BACKPRESSURE_TIMING i_stalls=%0d d_stalls=%0d max_data_age=%0d",i_request_stalls,d_request_stalls,max_data_age);
        $display("BACKPRESSURE_COLLISIONS redirects=%0d deferred=%0d suppressed_stores=%0d killed_fetch_errors=%0d",redirects,deferred_redirects,suppressed_stores,killed_fetch_errors);
        $display("BACKPRESSURE_COVER hazard_cycles=%0d held_refresh_cycles=%0d",hazard_cycles,refresh_cycles);
        $display("BACKPRESSURE_TOTAL seed=%0d scenarios=%0d retired=%0d cycles=%0d",seed,scenarios,total_retired,total_cycles);
        $display("BACKPRESSURE_SIM_PASS seed=%0d checked=%0d",seed,checked);
        $finish;
    end
endmodule
`default_nettype wire
