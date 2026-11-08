/* Approved v0.3 subset; main never returns to legacy halt_ecall. */
    .option norvc
    .option norelax
    .section .text,"ax",@progbits
    .globl main
main:
    la t0, trap_handler
    csrw mtvec, t0
    csrrwi t0, mscratch, 31
    csrrsi t1, mscratch, 0
    csrrci t2, mscratch, 3
    csrrs t3, mscratch, zero
    csrrc t4, mscratch, t3
    csrrw t5, mscratch, t1
    csrrw t5, mscratch, t5
    csrr zero, mvendorid
    li t0, 0
    csrrs t1, mvendorid, t0 /* nonzero index with zero value must fault */
    csrrw zero, mvendorid, zero
    csrr t1, 0xfff
    ecall
    ebreak
    .word 0xffffffff
    li t0, 0x10001
    lw t1, 0(t0)
    sh t1, 0(t0)
    li t0, 0
    sw t1, 0(t0)
    li t0, 0x20000
    lw zero, 0(t0)
    sw t1, 0(t0)
    li t0, 2
    jalr zero, 0(t0)
    la t0, recovered_fetch
    la t1, recovery_pc
    sw t0, 0(t1)
    li t0, 0x10000
    jalr zero, 0(t0)
recovered_fetch:
    li t0, 0x1e000
    lw t1, 0(t0)
    addi t1, t1, 1
    sw t1, 0(t0)
    li t0, 0x10000100
    sw zero, 8(t0)
    sw zero, 0(t0)
    li t1, 40
    sw t1, 4(t0)
    li t1, 1
    sw t1, 12(t0)
    li t1, 5 /* count + IRQ, existing reload bit left clear */
    sw t1, 8(t0)
    li t1, 0x800
    csrw mie, t1
    li s0, 0x12345678
    li s1, 0x76543210
    csrsi mstatus, 8
1:  la t0, irq_count
    lw t1, 0(t0)
    beq t1, zero, 1b
    li t0, 0x12345678
    bne s0, t0, failed
    li t0, 0x76543210
    bne s1, t0, failed
    la a1, pass_message
    jal ra, put_string
    la t0, signature
    li t1, 0x600d600d
    sw t1, 0(t0)
    .globl completed_loop
completed_loop:
    jal zero, completed_loop
failed:
    la a1, fail_message
    jal ra, put_string
    la t0, signature
    li t1, 0xdeadbeef
    sw t1, 0(t0)
    jal zero, completed_loop
put_string:
    li t3, 0x10000000
2:  lbu t0, 0(a1)
    beq t0, zero, 3f
    sb t0, 0(t3)
    addi a1, a1, 1
    jal zero, 2b
3:  lw t0, 4(t3)
    andi t0, t0, 1
    beq t0, zero, 3b
    jalr zero, 0(ra)
    .balign 4
trap_handler:
    addi sp, sp, -64
    sw ra, 0(sp)
    sw t0, 4(sp)
    sw t1, 8(sp)
    sw t2, 12(sp)
    sw t3, 16(sp)
    sw t4, 20(sp)
    sw t5, 24(sp)
    sw t6, 28(sp)
    csrr t0, mepc
    sw t0, 32(sp)
    csrr t0, mstatus
    sw t0, 36(sp)
    csrr t0, mcause
    blt t0, zero, external_handler
    li t1, 1
    beq t0, t1, fetch_handler
    lw t1, 32(sp)
    addi t1, t1, 4
    sw t1, 32(sp)
    /* Exercise nested synchronous traps with a software-saved hardware frame. */
    li t1, 11
    bne t0, t1, restore
    la t1, nested_done
    lw t2, 0(t1)
    bne t2, zero, restore
    li t2, 1
    sw t2, 0(t1)
    .word 0xffffffff
    jal zero, restore
fetch_handler:
    la t1, recovery_pc
    lw t1, 0(t1)
    sw t1, 32(sp)
    jal zero, restore
external_handler:
    li t1, 0x10000100
    sw zero, 8(t1)
    li t2, 1
    sw t2, 12(t1)
    la t1, irq_count
    lw t2, 0(t1)
    addi t2, t2, 1
    sw t2, 0(t1)
restore:
    lw t0, 32(sp)
    csrw mepc, t0
    lw t0, 36(sp)
    csrw mstatus, t0
    lw ra, 0(sp)
    lw t0, 4(sp)
    lw t1, 8(sp)
    lw t2, 12(sp)
    lw t3, 16(sp)
    lw t4, 20(sp)
    lw t5, 24(sp)
    lw t6, 28(sp)
    addi sp, sp, 64
    mret
    .section .rodata,"a",@progbits
pass_message: .asciz "IRQ PASS\r\n"
fail_message: .asciz "IRQ FAIL\r\n"
    .section .data,"aw",@progbits
    .balign 4
    .globl initial_data
initial_data: .word 0xcafebabe, 0x13579bdf
    .section .bss,"aw",@nobits
    .balign 4
    .globl zero_area, signature, irq_count
zero_area: .space 8
signature: .space 4
irq_count: .space 4
recovery_pc: .space 4
nested_done: .space 4
    .section .note.GNU-stack,"",@progbits
