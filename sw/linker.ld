OUTPUT_ARCH(riscv)
ENTRY(_start)
MEMORY
{
  ROM (rx) : ORIGIN = 0x00000000, LENGTH = 64K
  RAM (rw) : ORIGIN = 0x00010000, LENGTH = 64K
}
PHDRS
{
  rom PT_LOAD FLAGS(5);
  ram PT_LOAD FLAGS(6);
}
SECTIONS
{
  .text :
  {
    KEEP(*(.text.init))
    *(.text .text.*)
    . = ALIGN(4);
  } > ROM :rom
  .rodata : { *(.rodata .rodata.*) . = ALIGN(4); } > ROM :rom
  .data :
  {
    __data_start = .;
    *(.data .data.* .sdata .sdata.*)
    . = ALIGN(4);
    __data_end = .;
  } > RAM AT> ROM :ram
  __data_load = LOADADDR(.data);
  __rom_image_end = LOADADDR(.data) + SIZEOF(.data);
  .bss (NOLOAD) :
  {
    __bss_start = .;
    *(.bss .bss.* .sbss .sbss.*) *(COMMON)
    . = ALIGN(4);
    __bss_end = .;
  } > RAM :ram
  __stack_top = ORIGIN(RAM) + LENGTH(RAM);
  __stack_bottom = __stack_top - 4096;
  .riscv.attributes 0 : { *(.riscv.attributes) }
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
  ASSERT(__rom_image_end <= ORIGIN(ROM) + LENGTH(ROM), "ROM image exceeds approved region")
  ASSERT(__bss_end <= __stack_bottom, "RAM/stack collision")
  ASSERT((__data_start % 4) == 0 && (__data_end % 4) == 0, "Data copy alignment")
  ASSERT((__bss_start % 4) == 0 && (__bss_end % 4) == 0, "BSS alignment")
}
