# Non-project T025 shell synthesis and actual constraint/property inspection.
# No placement/routing/bitstream/hardware. Also used for an intentional bad XDC.
if {[catch {
    lassign $argv root xdc expected_file
    if {[version -short] ne "2025.2"} {error "VERSION_MISMATCH"}
    read_verilog -sv [file join $root fpga/basys3/top.sv]
    synth_design -top basys3_top -part xc7a35tcpg236-1 -flatten_hierarchy none
    read_xdc $xdc
    set stream [open $expected_file r]
    set lines [split [string trim [read $stream]] "\n"]
    close $stream
    if {[llength [get_ports]] != 36 || [llength $lines] != 36} {error "BOARD_PORT_COUNT"}
    foreach line $lines {
        lassign [split $line] name pin direction
        set port [get_ports -quiet $name]
        if {[llength $port] != 1} {error "BOARD_PORT_MISSING: $name"}
        if {[get_property DIRECTION $port] ne $direction} {error "BOARD_DIRECTION: $name"}
        if {[get_property PACKAGE_PIN $port] ne $pin} {error "BOARD_PIN_MISMATCH: $name"}
        if {[get_property IOSTANDARD $port] ne "LVCMOS33"} {error "BOARD_IOSTANDARD: $name"}
    }
    if {[llength [get_clocks]] != 1} {error "BOARD_CLOCK_COUNT"}
    set clock [get_clocks sys_clk]
    if {[get_property PERIOD $clock] != 10.000} {error "BOARD_CLOCK_PERIOD"}
    if {[get_clocks -of_objects [get_ports clk]] ne $clock} {error "BOARD_CLOCK_SOURCE"}
    if {[get_property WAVEFORM $clock] ne "0.000 5.000"} {error "BOARD_CLOCK_WAVEFORM"}
    if {[get_property CONFIG_VOLTAGE [current_design]] != 3.3 ||
        [get_property CFGBVS [current_design]] ne "VCCO"} {error "BOARD_CONFIG_VOLTAGE"}
    if {[llength [get_cells -quiet -hier -filter {ASYNC_REG == TRUE}]] != 36} {error "BOARD_SYNC_ATTRIBUTES"}
    if {[llength [get_cells -quiet -hier -filter {REF_NAME =~ LD* || IS_BLACKBOX == 1}]] != 0} {error "BOARD_LATCH_OR_BLACKBOX"}
    report_io -file board_io.rpt
    report_clocks -file board_clocks.rpt
    report_utilization -file board_utilization.rpt
    report_drc -checks [get_drc_checks {LUTLP-1 MDRV-1 NSTD-1 UCIO-1}] -file board_drc.rpt
    if {[llength [get_drc_violations -quiet]] != 0} {error "BOARD_DRC_FAILED"}
    puts "BOARD_CONSTRAINTS_PASS ports=36 clock_ns=10.000"
} detail]} {
    puts stderr "BOARD_CONSTRAINTS_FAIL: $detail"
    exit 1
}
exit 0
