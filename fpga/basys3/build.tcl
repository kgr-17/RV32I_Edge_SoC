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
    if {$mode ni {plan execute} || $stage ni {synth impl all}} {error "FPGA_MODE_STAGE"}
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
    if {$stage eq "impl"} {
        set checkpoint [checked_input $checkpoint $build_root {.dcp}]
    }
    if {$mode eq "execute" && ([dict get $job authorization] ne "T043" || [dict get $job scope] eq "diagnostic_shell_before_T031")} {error "FPGA_OWNER_AUTH_REQUIRED"}
    set flow {}
    if {$stage in {synth all}} {
        lappend flow [list read_verilog -sv $sources]
        lappend flow [list synth_design -top [dict get $job top] -part [dict get $job part] -flatten_hierarchy none]
        foreach xdc $constraints {lappend flow [list read_xdc $xdc]}
        lappend flow [list report_utilization -file synthesis_utilization.rpt]
        lappend flow [list report_timing_summary -delay_type min_max -report_unconstrained -file synthesis_timing.rpt]
        lappend flow [list write_checkpoint synthesis.dcp]
    } else {lappend flow [list open_checkpoint $checkpoint]}
    if {$stage in {impl all}} {
        foreach name {opt_design place_design phys_opt_design route_design} {lappend flow [list $name]}
        lappend flow [list report_utilization -file routed_utilization.rpt]
        lappend flow [list report_timing_summary -delay_type min_max -report_unconstrained -file routed_timing.rpt]
        lappend flow [list report_clocks -file routed_clocks.rpt]
        lappend flow [list report_clock_interaction -file routed_clock_interaction.rpt]
        lappend flow [list report_cdc -details -all_checks_per_endpoint -no_waiver -file routed_cdc.rpt]
        lappend flow [list check_timing -verbose -file routed_checks.rpt]
        lappend flow [list report_drc -file routed_drc.rpt]
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
                if {[get_property PART [current_design]] ne "xc7a35tcpg236-1" || [llength [get_clocks sys_clk]]!=1 ||
                    [get_property PERIOD [get_clocks sys_clk]]!=10.000 || [llength [get_ports]]!=36} {error "FPGA_DESIGN_CONTRACT"}
            }
        }
        puts "FPGA_BUILD_EXECUTION_PASS stage=$stage"
    }
} detail]} {
    puts stderr "FPGA_BUILD_FAIL: $detail"
    exit 1
}
exit 0
