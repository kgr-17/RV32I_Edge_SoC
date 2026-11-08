# Nonproject flow. Plan validates/prints commands only. No hardware programming.
# T043 execution is owner-controlled through scripts/fpga_build.py; flags/job
# acknowledgments are workflow checks, not sandboxing or authentication.
proc inside_path {candidate base} {
    set candidate [file normalize $candidate];set base [file normalize $base]
    if {[string equal -nocase $candidate $base]} {return 1}
    return [string equal -nocase [string range $candidate 0 [string length $base]] "$base/"]
}
proc checked_input {path root extensions} {
    set path [file normalize $path]
    if {![inside_path $path $root] || ![file isfile $path] || [string tolower [file extension $path]] ni $extensions} {error "FPGA_INPUT_REJECTED $path"}
    return $path
}
proc fpga_power_model {} {
    # An explicit operating assumption for vectorless estimation, not SAIF data.
    set_switching_activity -deassert_resets
    report_switching_activity -static_probability -signal_rate -file routed_activity.rpt [all_inputs]
    puts "FPGA_POWER_MODEL=vectorless_resets_deasserted_no_activity_file"
}
proc fpga_inventory {} {
    set out [open physical_inventory.tsv w]
    puts $out "part\t[get_property PART [current_design]]"
    puts $out "ports\t[llength [get_ports]]"
    puts $out "clocks\t[llength [get_clocks]]"
    puts $out "period\t[get_property PERIOD [get_clocks sys_clk]]"
    set count [llength [get_cells -hier -filter {ASYNC_REG == 1}]]
    if {$count!=36} {error "FPGA_ASYNC_STAGE_COUNT $count"}
    puts $out "async_regs\t$count"
    set copies [get_cells -hier -filter {NAME =~ rst_s_reg* && REF_NAME == FDRE}]
    if {[llength $copies]<1} {error "FPGA_CLOCKED_RESET_COPY_MISSING"}
    puts $out "clocked_reset_copies\t[llength $copies]"
    foreach p [lsort [get_ports]] {
        puts $out "port\t$p\t[get_property DIRECTION $p]\t[get_property PACKAGE_PIN $p]\t[get_property IOSTANDARD $p]"
    }
    set chains {}
    for {set bit 0} {$bit<16} {incr bit} {
        lappend chains [list [format {soc/fabric/gpio_unit/inputs/meta_q_reg[%d]} $bit] [format {soc/fabric/gpio_unit/inputs/sync_q_reg[%d]} $bit]]
    }
    lappend chains [list soc/fabric/uart/receiver/rx_meta_q_reg soc/fabric/uart/receiver/rx_sync_q_reg]
    lappend chains [list {reset_boundary/g_sync.release_q_reg[0]} {reset_boundary/g_sync.release_q_reg[1]}]
    foreach chain $chains {
        lassign $chain first second
        set a [get_cells -hier -filter "NAME == $first"]
        set b [get_cells -hier -filter "NAME == $second"]
        if {[llength $a]!=1 || [llength $b]!=1} {error "FPGA_SYNC_CHAIN_MISSING $first"}
        foreach cell [list $a $b] {
            if {[string toupper [get_property ASYNC_REG $cell]] ni {TRUE 1}} {error "FPGA_ASYNC_ATTRIBUTE $cell"}
            if {[string match {reset_boundary/*} $cell] && [get_property REF_NAME $cell] ne "FDRE"} {error "FPGA_RESET_STAGES_MUST_BE_CLOCKED"}
        }
        set q [get_pins -of_objects $a -filter {REF_PIN_NAME == Q}]
        set d [get_pins -of_objects $b -filter {REF_PIN_NAME == D}]
        set sinks [get_pins -leaf -of_objects [get_nets -of_objects $q] -filter {DIRECTION == IN}]
        if {[llength $sinks]!=1 || $sinks ne $d} {error "FPGA_SYNC_CHAIN_FANOUT $first"}
        puts $out "chain\t$first\t$second\t1\t1\t[llength $sinks]"
    }
    close $out
    puts "FPGA_PHYSICAL_INVENTORY_PASS chains=18 async_regs=36 clocked_reset=1"
}
if {[catch {
    if {$argc!=1} {error "FPGA_JOB_ARGUMENTS"}
    set project_root [file normalize [file join [file dirname [info script]] ../..]]
    set build_root [file join $project_root build]
    set jobfile [file normalize [lindex $argv 0]]
    if {![inside_path $jobfile $build_root] || ![file isfile $jobfile]} {error "FPGA_JOB_LOCATION"}
    set stream [open $jobfile r];set text [read $stream];close $stream
    set job [dict create];set sources {};set constraints {};set memories {}
    set required {schema root mode stage top part period version sw_build scope output authorization checkpoint}
    foreach line [split [string trimright $text "\r\n"] "\n"] {
        set fields [split [string trimright $line "\r"] "\t"]
        if {[llength $fields]!=2} {error "FPGA_JOB_FIELDS"}
        lassign $fields key value
        switch -- $key {
            source {lappend sources [checked_input $value $project_root {.sv .v}]}
            constraint {lappend constraints [checked_input $value $project_root {.xdc}]}
            memory {lappend memories [checked_input $value $project_root {.mem}]}
            default {
                if {$key ni $required || [dict exists $job $key]} {error "FPGA_JOB_DUPLICATE_OR_UNKNOWN $key"}
                dict set job $key $value
            }
        }
    }
    foreach key $required {if {![dict exists $job $key]} {error "FPGA_JOB_MISSING $key"}}
    if {[dict get $job schema] ne "1" || [file normalize [dict get $job root]] ne $project_root} {error "FPGA_JOB_SCHEMA_ROOT"}
    set mode [dict get $job mode];set stage [dict get $job stage]
    if {$mode ni {plan execute} || $stage ni {synth impl all opt place physopt phys_fanout phys_placement phys_logic phys_pin route reports}} {error "FPGA_MODE_STAGE"}
    if {[dict get $job top] ne "basys3_top" || [dict get $job part] ne "xc7a35tcpg236-1" || [dict get $job period]!=10.000} {error "FPGA_TARGET_CONTRACT"}
    if {[version -short] ne [dict get $job version] || [dict get $job version] ne "2025.2" ||
        [dict get $job sw_build] ne "6299465" || ![string match {*SW Build 6299465*} [version]]} {error "FPGA_VERSION_CONTRACT"}
    if {[llength $sources]==0 || [llength $constraints]==0 || [llength [lsort -unique $sources]]!=[llength $sources] ||
        [llength [lsort -unique $constraints]]!=[llength $constraints]} {error "FPGA_INPUT_LIST"}
    set basenames {}
    foreach name $memories {lappend basenames [string tolower [file tail $name]]}
    if {[llength [lsort -unique $basenames]]!=[llength $basenames]} {error "FPGA_MEMORY_BASENAME_ALIAS"}
    set output [file normalize [dict get $job output]]
    if {![inside_path $output $build_root] || $output eq $build_root || [file exists $output]} {error "FPGA_OUTPUT_REJECTED"}
    set checkpoint [dict get $job checkpoint]
    if {$stage ni {synth all}} {
        set checkpoint [checked_input $checkpoint $build_root {.dcp}]
    }
    if {$mode eq "execute" && ([dict get $job authorization] ne "T043" || [dict get $job scope] eq "diagnostic_shell_before_T031")} {error "FPGA_OWNER_AUTH_REQUIRED"}
    set flow {}
    if {$stage in {synth all}} {
        lappend flow [list read_verilog -sv $sources]
        # Permit cross-module logic optimization while rebuilding source names.
        # Clock, state boundaries and timing checks remain unchanged.
        lappend flow [list synth_design -top [dict get $job top] -part [dict get $job part] -flatten_hierarchy rebuilt]
        foreach xdc $constraints {lappend flow [list read_xdc $xdc]}
        lappend flow [list report_utilization -file synthesis_utilization.rpt]
        lappend flow [list report_timing_summary -delay_type min_max -report_unconstrained -file synthesis_timing.rpt]
        lappend flow [list write_checkpoint synthesis.dcp]
    } else {lappend flow [list open_checkpoint $checkpoint]}
    if {$stage in {opt place physopt phys_fanout phys_placement phys_logic phys_pin route}} {
        set stage_commands [dict create opt {opt_design -retarget -propconst -sweep} place place_design physopt phys_opt_design phys_fanout {phys_opt_design -fanout_opt} phys_placement {phys_opt_design -placement_opt} phys_logic {phys_opt_design -restruct_opt -critical_cell_opt} phys_pin {phys_opt_design -critical_pin_opt} route route_design]
        set stage_checkpoints [dict create opt optimized.dcp place placed.dcp physopt physopt.dcp phys_fanout fanout.dcp phys_placement placement_opt.dcp phys_logic logic_opt.dcp phys_pin pin_opt.dcp route routed.dcp]
        lappend flow [dict get $stage_commands $stage]
        lappend flow [list write_checkpoint [dict get $stage_checkpoints $stage]]
    }
    if {$stage in {impl all}} {
        # Keep retarget/constant/sweep optimization, omitting optional BRAM CE
        # lookahead that pulled asynchronous reset across the clocked boundary.
        lappend flow [list opt_design -retarget -propconst -sweep]
        lappend flow [list place_design]
        lappend flow [list phys_opt_design]
        lappend flow [list route_design]
    }
    if {$stage in {impl all reports}} {
        lappend flow [list report_utilization -file routed_utilization.rpt]
        lappend flow [list report_timing_summary -delay_type min_max -report_unconstrained -file routed_timing.rpt]
        lappend flow [list report_clocks -file routed_clocks.rpt]
        lappend flow [list report_clock_interaction -file routed_clock_interaction.rpt]
        lappend flow [list report_route_status -file routed_route_status.rpt]
        lappend flow [list report_cdc -details -all_checks_per_endpoint -no_waiver -file routed_cdc.rpt]
        lappend flow [list check_timing -verbose -file routed_checks.rpt]
        lappend flow [list report_drc -file routed_drc.rpt]
        lappend flow [list write_xdc effective_constraints.xdc]
        lappend flow [list fpga_inventory]
        lappend flow [list fpga_power_model]
        lappend flow [list report_power -file routed_power.rpt]
        lappend flow [list write_checkpoint routed.dcp]
        lappend flow [list write_bitstream design.bit]
    }
    foreach command $flow {
        if {![info complete $command] || [llength [info commands [lindex $command 0]]]!=1} {error "FPGA_FLOW_COMMAND_MISSING"}
        puts "FPGA_PLANNED_COMMAND=$command"
    }
    if {$mode eq "plan"} {
        puts "FPGA_BUILD_PLAN_PASS stage=$stage top=[dict get $job top] part=[dict get $job part] period_ns=10.000 commands=[llength $flow]"
    } else {
        file mkdir $output;cd $output
        foreach memory $memories {file copy $memory [file tail $memory]}
        set_param general.maxThreads 2
        foreach command $flow {
            set action [lindex $command 0]
            # Never emit a bitstream for missing/failed setup/hold paths or DRC.
            if {$action eq "write_bitstream"} {
                foreach type {max min} {
                    set path [get_timing_paths -delay_type $type -max_paths 1]
                    if {[llength $path]!=1 || [get_property SLACK $path]<0.000} {error "FPGA_ROUTED_TIMING_FAILED $type"}
                }
                if {[llength [get_drc_violations -quiet]]!=0} {error "FPGA_ROUTED_DRC_FAILED"}
            }
            {*}$command
            if {$action in {read_xdc open_checkpoint}} {
                if {[get_property PART [current_design]] ne "xc7a35tcpg236-1" || [llength [get_clocks]]!=1 || [llength [get_clocks sys_clk]]!=1 ||
                    [get_property PERIOD [get_clocks sys_clk]]!=10.000 || [llength [get_ports]]!=36} {error "FPGA_DESIGN_CONTRACT"}
            }
            if {$action in {synth_design open_checkpoint}} {
                if {[llength [get_cells -quiet -hier -filter {REF_NAME =~ LD*}]]!=0 ||
                    [llength [get_cells -quiet -hier -filter {IS_BLACKBOX == 1}]]!=0} {error "FPGA_LATCH_OR_BLACKBOX"}
            }
        }
        puts "FPGA_BUILD_EXECUTION_PASS stage=$stage"
    }
} detail]} {
    puts stderr "FPGA_BUILD_FAIL: $detail"
    exit 1
}
exit 0
