# Non-project synthesis lint of explicitly listed fixture/design sources only.
# No open_project, implementation, bitstream or hardware commands.
if {[catch {
    lassign $argv source_list top part expected_version
    if {[version -short] ne $expected_version} { error "VERSION_MISMATCH" }
    puts "TOOLCHAIN_VIVADO_VERSION=[version -short]"
    puts "TOOLCHAIN_VIVADO_FULL_VERSION=[version]"
    if {[llength [get_parts -quiet $part]] != 1} { error "PART_UNAVAILABLE" }
    set stream [open $source_list r]
    set sources [split [string trim [read $stream]] "\n"]
    close $stream
    foreach source $sources { read_verilog -sv $source }
    synth_design -top $top -part $part -flatten_hierarchy none
    set latches [get_cells -quiet -hierarchical -filter {REF_NAME =~ LD*}]
    if {[llength $latches] != 0} { error "LATCH_DETECTED: $latches" }
    set boxes [get_cells -quiet -hierarchical -filter {IS_BLACKBOX == 1}]
    if {[llength $boxes] != 0} { error "BLACKBOX_DETECTED: $boxes" }
    set structural_checks [get_drc_checks {LUTLP-1 MDRV-1}]
    if {[llength $structural_checks] != 2} { error "STRUCTURAL_RULES_UNAVAILABLE" }
    report_drc -checks $structural_checks -file structural_drc.rpt
    if {[llength [get_drc_violations -quiet]] != 0} { error "STRUCTURAL_DRC_FAILED" }
    report_utilization -file fixture_utilization.rpt
    puts "TOOLCHAIN_LINT_PASS top=$top"
} detail]} {
    puts stderr "TOOLCHAIN_LINT_FAIL: $detail"
    exit 1
}
exit 0
