# Authorized local inventory/programming only; input is data, never eval/source.
set root [file normalize [file join [file dirname [info script]] ..]]
if {$argc != 1} {error "HARDWARE_JOB_REQUIRED"}
set job [file normalize [lindex $argv 0]]
set channel [open $job r]
set fields [dict create]
foreach line [split [read $channel] "\n"] {
    if {$line eq ""} {continue}
    set pair [split $line "\t"]
    if {[llength $pair] != 2 || [dict exists $fields [lindex $pair 0]]} {error "HARDWARE_JOB_SCHEMA"}
    dict set fields [lindex $pair 0] [lindex $pair 1]
}
close $channel
if {[lsort [dict keys $fields]] ne [lsort {mode output python target device}]} {error "HARDWARE_JOB_KEYS"}
set mode [dict get $fields mode]
if {$mode ni {inventory program}} {error "HARDWARE_MODE"}
if {[version -short] ne "2025.2"} {error "HARDWARE_VERSION"}
# AMD sets its own PYTHONHOME/PYTHONPATH. Remove these only for the project's
# child interpreter, then restore the vendor process environment unchanged.
proc verify_job {python root job} {
    set saved [dict create]
    foreach key {PYTHONHOME PYTHONPATH} {
        if {[info exists ::env($key)]} {dict set saved $key $::env($key); unset ::env($key)}
    }
    set code [catch {exec $python -B [file join $root scripts hardware.py] guard --job $job} answer options]
    dict for {key value} $saved {set ::env($key) $value}
    if {$code} {return -options $options $answer}
    puts $answer
}
# Recheck live state/authority/image/job bindings immediately before hardware I/O.
verify_job [dict get $fields python] $root $job
set output [dict get $fields output]
set stream [open [file join $output inventory.tsv] {WRONLY CREAT EXCL}]
set opened 0
set manager 0
set server 0
set result [catch {
    open_hw_manager
    set manager 1
    connect_hw_server -url localhost:3121
    set server 1
    set targets [get_hw_targets]
    foreach target $targets {puts $stream "target\t$target"}
    if {[llength $targets] != 1} {
        if {$mode eq "program"} {error "HARDWARE_TARGET_COUNT"}
    } else {
        set target [lindex $targets 0]
        if {$mode eq "program" && $target ne [dict get $fields target]} {error "HARDWARE_TARGET_CHANGED"}
        current_hw_target $target
        open_hw_target $target
        set opened 1
        set devices [get_hw_devices]
        foreach device $devices {
            set part [get_property PART $device]
            set idcode "UNAVAILABLE"
            if {[lsearch -exact [list_property $device] IDCODE] >= 0} {set idcode [get_property IDCODE $device]}
            puts $stream "device\t$target\t$device\t$part\t$idcode"
        }
        if {$mode eq "program"} {
            if {[llength $devices] != 1} {error "HARDWARE_DEVICE_COUNT"}
            set device [lindex $devices 0]
            if {$device ne [dict get $fields device] || [get_property PART $device] ne "xc7a35t"} {
                error "HARDWARE_WRONG_DEVICE"
            }
            verify_job [dict get $fields python] $root $job
            set_property PROGRAM.FILE [file join $output approved.bit] $device
            program_hw_devices $device
            puts "HARDWARE_PROGRAM_PASS"
        }
    }
    puts "HARDWARE_INVENTORY_COMPLETE"
} message options]
close $stream
if {$opened} {close_hw_target}
if {$server} {disconnect_hw_server}
if {$manager} {close_hw_manager}
if {$result} {return -options $options $message}
