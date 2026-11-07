# Add the inspected SoC manifest to the EXISTING project, idempotently.
# No synthesis/implementation, IP, bitstream, hardware server or programming.
if {[catch {
    set root [file normalize [file join [file dirname [info script]] ../..]]
    set xpr [file join $root RV32I_Edge_SoC.xpr]
    if {![file isfile $xpr]} {error "PROJECT_MISSING"}
    if {[llength $argv] != 1} {error "SOURCE_MANIFEST_REQUIRED"}
    set stream [open [lindex $argv 0] r]
    set rows [split [string trim [read $stream]] "\n"]
    close $stream
    set design_files {}
    set constraint_files {}
    foreach row $rows {
        lassign [split $row "\t"] kind relative
        if {$kind ni {rtl mem xdc} || [file pathtype $relative] ne "relative"} {error "SOURCE_MANIFEST_INVALID"}
        set path [file normalize [file join $root $relative]]
        if {![string equal -nocase [string range $path 0 [string length $root]] "$root/"] || ![file isfile $path]} {error "SOURCE_OUTSIDE_OR_MISSING"}
        if {$kind eq "xdc"} {lappend constraint_files $path} else {lappend design_files $path}
    }
    if {[llength $design_files] < 2 || [llength $constraint_files] != 1} {error "SOURCE_MANIFEST_EMPTY"}
    open_project $xpr
    if {[get_property PART [current_project]] ne "xc7a35tcpg236-1"} {error "TARGET_MISMATCH"}
    # Inspect every existing entry BEFORE modifying filesets/top. Refuse unknown
    # sources/top rather than replacing owner additions or integrating stale RTL.
    foreach file [get_files -quiet -of_objects [get_filesets sources_1]] {
        if {[file normalize $file] ni $design_files} {error "UNEXPECTED_DESIGN_SOURCE: $file"}
    }
    foreach file [get_files -quiet -of_objects [get_filesets constrs_1]] {
        if {[file normalize $file] ni $constraint_files} {error "UNEXPECTED_CONSTRAINT_SOURCE: $file"}
    }
    set oldtop [get_property TOP [get_filesets sources_1]]
    if {$oldtop ni {"" basys3_top}} {error "UNEXPECTED_OWNER_TOP: $oldtop"}
    foreach path $design_files {
        if {[llength [get_files -quiet $path]] == 0} {add_files -norecurse $path}
    }
    foreach path $constraint_files {
        if {[llength [get_files -quiet $path]] == 0} {add_files -fileset constrs_1 -norecurse $path}
    }
    set_property TOP basys3_top [get_filesets sources_1]
    set_property TOP_AUTO_SET 0 [get_filesets sources_1]
    update_compile_order -fileset sources_1
    close_project
    # Vivado writes CRLF on Windows. Keep repository serialization canonical LF
    # so new XML lines pass the existing whitespace gate without changing policy.
    set stream [open $xpr r]
    set text [read $stream]
    close $stream
    set stream [open $xpr w]
    fconfigure $stream -translation lf
    puts -nonewline $stream $text
    close $stream
    puts "BOARD_INTEGRATION_PASS"
} detail]} {
    puts stderr "BOARD_INTEGRATION_FAIL: $detail"
    exit 1
}
exit 0
