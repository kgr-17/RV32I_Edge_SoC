# Actual selected-part synchronous memory inference, without implementation.
if {[catch {
    set root [lindex $argv 0]
    if {[version -short] ne "2025.2"} {error "VERSION_MISMATCH"}
    read_verilog -sv [file join $root rtl/memory/boot_rom.sv]
    read_verilog -sv [file join $root rtl/memory/data_ram.sv]
    read_verilog -sv [file join $root dv/lint/memory_lint_top.sv]
    synth_design -top memory_lint_top -part xc7a35tcpg236-1 -flatten_hierarchy none
    set roms [get_cells -hier -filter {NAME =~ rom/* && REF_NAME =~ RAMB*}]
    set rams [get_cells -hier -filter {NAME =~ ram/* && REF_NAME =~ RAMB*}]
    if {[llength $roms] == 0 || [llength $rams] == 0} {error "BLOCK_RAM_NOT_INFERRED"}
    if {[llength [get_cells -quiet -hier -filter {REF_NAME =~ LD* || IS_BLACKBOX == 1}]]} {error "MEMORY_LATCH_OR_BLACKBOX"}
    report_utilization -hierarchical -file memory_utilization.rpt
    report_drc -checks [get_drc_checks {LUTLP-1 MDRV-1}] -file memory_drc.rpt
    if {[llength [get_drc_violations -quiet]]} {error "MEMORY_DRC_FAILED"}
    puts "MEMORY_BRAM_COUNTS rom=[llength $roms] ram=[llength $rams]"
    puts "MEMORY_INFERENCE_PASS"
} detail]} {
    puts stderr "MEMORY_INFERENCE_FAIL: $detail"
    exit 1
}
exit 0
