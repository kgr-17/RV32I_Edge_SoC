# Read-only installation probe: no project, synthesis, implementation or hardware.
puts "RV32I_VIVADO_VERSION=[version -short]"
set target_part xc7a35tcpg236-1
if {[llength [get_parts -quiet $target_part]] != 1} {
    error "Required target part is not available: $target_part"
}
puts "RV32I_TARGET_PART_AVAILABLE=$target_part"
exit 0
