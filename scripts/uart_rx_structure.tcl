# Bounded synthesis structure inspection, not a CDC/MTBF/routed signoff.
if {$argc != 1} {error "UART_RX_STRUCTURE_ARGUMENTS"}
set stream [open [lindex $argv 0] r]
set sources [split [string trim [read $stream]] "\n"]
close $stream
read_verilog -sv $sources
synth_design -top uart_full_lint_top -part xc7a35tcpg236-1 -flatten_hierarchy none
set meta [get_cells -hier -filter {NAME =~ */receiver/rx_meta_q_reg}]
set sync [get_cells -hier -filter {NAME =~ */receiver/rx_sync_q_reg}]
if {[llength $meta]!=1 || [llength $sync]!=1} {error "UART_RX_SYNC_STAGE_COUNT"}
foreach cell [list $meta $sync] {
    if {[string toupper [get_property ASYNC_REG $cell]] ni {TRUE 1}} {error "UART_RX_MISSING_ASYNC_REG"}
}
set net [get_nets -of_objects [get_pins $meta/Q]]
set sinks [get_pins -leaf -of_objects $net -filter {DIRECTION == IN}]
if {[llength $sinks]!=1 || [lindex $sinks 0] ne "$sync/D"} {error "UART_RX_META_FANOUT"}
set cm [get_nets -of_objects [get_pins $meta/C]]
set cs [get_nets -of_objects [get_pins $sync/C]]
if {[llength $cm]!=1 || $cm ne $cs} {error "UART_RX_CLOCK_DOMAIN"}
set out [open synchronizer.txt w]
puts $out "meta=$meta ASYNC_REG=[get_property ASYNC_REG $meta]"
puts $out "sync=$sync ASYNC_REG=[get_property ASYNC_REG $sync]"
puts $out "meta_Q_net=$net sinks=$sinks clock=$cm"
close $out
puts "UART_RX_SYNC_PASS stages=2 fanout=1 clock=common"
