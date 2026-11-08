# Scoped synthesized CDC analysis; virtual off-chip launch flops exist only in DV.
if {$argc!=1} {error "CDC_STRUCTURE_ARGUMENTS"}
set stream [open [lindex $argv 0] r]
set sources [split [string trim [read $stream]] "\n"];close $stream
read_verilog -sv $sources
synth_design -top cdc_registered_probe -part xc7a35tcpg236-1 -flatten_hierarchy none
create_clock -name core_clk -period 10.000 [get_ports clk_i]
create_clock -name external_model -period 13.000 [get_ports clk_external_i]
set external [get_ports -filter {DIRECTION == IN && NAME != clk_i && NAME != clk_external_i}]
if {[llength $external]!=18} {error "CDC_EXTERNAL_PORT_COUNT"}
set_input_delay -clock external_model -min 0.000 $external
set_input_delay -clock external_model -max 0.000 $external
set_output_delay -clock core_clk -min 0.000 [all_outputs]
set_output_delay -clock core_clk -max 0.000 [all_outputs]
set_clock_groups -asynchronous -group [get_clocks core_clk] -group [get_clocks external_model]
check_timing -verbose -file timing_checks.rpt
# Preserve every rule and waiver state. No waiver, severity filter or message edit.
report_cdc -details -all_checks_per_endpoint -no_waiver -file cdc.rpt
set violations [get_cdc_violations]
set out [open inventory.tsv w]
puts $out "rule\tseverity\tdepth\twaived\tendpoints\tstages\tfrom\tto"
foreach v $violations {
    puts $out "[get_property CHECK $v]\t[get_property SEVERITY $v]\t[get_property DEPTH $v]\t[get_property IS_WAIVED $v]\t[llength [get_property ENDPOINT_PIN $v]]\t[llength [get_property SYNCHRONIZER $v]]\t[get_property STARTPOINT_CLOCK $v]\t[get_property ENDPOINT_CLOCK $v]"
}
close $out
write_xdc effective_analysis.xdc
if {[llength $violations]!=3} {error "CDC_RULE_REJECTED crossing_count=[llength $violations]"}
set seen [dict create CDC-3 0 CDC-6 0 CDC-9 0]
foreach v $violations {
    set rule [get_property CHECK $v]
    if {![dict exists $seen $rule]} {error "CDC_RULE_REJECTED unexpected=$rule"}
    dict incr seen $rule
    set expected_severity Info
    set endpoints 1
    set stages 2
    if {$rule eq "CDC-6"} {set expected_severity Warning;set endpoints 16;set stages 32}
    # CDC-6 stays Warning: GPIO bits are independent levels, not a coherent bus.
    # This is disclosed analysis, not a waiver or zero-warning signoff claim.
    if {[get_property SEVERITY $v] ne $expected_severity || [get_property DEPTH $v]!=2 ||
        [get_property IS_WAIVED $v] || [get_property IS_WAIVED_INTERNAL $v] ||
        [get_property STARTPOINT_CLOCK $v] ne "external_model" || [get_property ENDPOINT_CLOCK $v] ne "core_clk" ||
        [llength [get_property ENDPOINT_PIN $v]]!=$endpoints || [llength [get_property SYNCHRONIZER $v]]!=$stages} {
        error "CDC_RULE_REJECTED properties=$rule"
    }
}
foreach rule [dict keys $seen] {if {[dict get $seen $rule]!=1} {error "CDC_RULE_REJECTED duplicate=$rule"}}
set chains {}
for {set bit 0} {$bit<16} {incr bit} {
    lappend chains [list [format {boundary/switches/meta_q_reg[%d]} $bit] [format {boundary/switches/sync_q_reg[%d]} $bit]]
}
lappend chains [list boundary/receiver/rx_meta_q_reg boundary/receiver/rx_sync_q_reg]
lappend chains [list {boundary/reset_boundary/g_async.release_q_reg[0]} {boundary/reset_boundary/g_async.release_q_reg[1]}]
set out [open chains.tsv w]
puts $out "first\tsecond\tfirst_async\tsecond_async\tfanout\tclock"
foreach chain $chains {
    lassign $chain first second
    foreach name $chain {
        set cell [get_cells -hier -filter "NAME == $name"]
        if {[llength $cell]!=1 || [string toupper [get_property ASYNC_REG $cell]] ni {TRUE 1}} {error "CDC_CHAIN_ATTRIBUTE $name"}
    }
    set first_cell [get_cells -hier -filter "NAME == $first"]
    set second_cell [get_cells -hier -filter "NAME == $second"]
    set first_q [get_pins -of_objects $first_cell -filter {REF_PIN_NAME == Q}]
    set second_d [get_pins -of_objects $second_cell -filter {REF_PIN_NAME == D}]
    set sinks [get_pins -leaf -of_objects [get_nets -of_objects $first_q] -filter {DIRECTION == IN}]
    set clock1 [get_nets -of_objects [get_pins -of_objects $first_cell -filter {REF_PIN_NAME == C}]]
    set clock2 [get_nets -of_objects [get_pins -of_objects $second_cell -filter {REF_PIN_NAME == C}]]
    if {[llength $sinks]!=1 || $sinks ne $second_d || [llength $clock1]!=1 || $clock1 ne $clock2} {error "CDC_CHAIN_ISOLATION $first"}
    puts $out "$first\t$second\t[get_property ASYNC_REG $first_cell]\t[get_property ASYNC_REG $second_cell]\t[llength $sinks]\t$clock1"
}
close $out
if {[llength [get_cells -hier -filter {ASYNC_REG == 1}]]!=36} {error "CDC_ASYNC_CELL_COUNT"}
puts "CDC_STRUCTURE_PASS chains=18 stages=36 rules=3 retained_warning=CDC-6"
