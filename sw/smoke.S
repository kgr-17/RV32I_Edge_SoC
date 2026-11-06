    .option norvc
    .option norelax
    .section .text.main,"ax",@progbits
    .globl main
    .type main,@function
main:
    addi sp, sp, -16
    sw ra, 12(sp)
    li t4, 0x10203040
    sw t4, 8(sp)
    lw t5, 8(sp)
    bne t4, t5, fail
    la t0, initial_data
    lw t1, 0(t0)
    li t2, 0xcafebabe
    bne t1, t2, fail
    lw t1, 4(t0)
    li t2, 0x13579bdf
    bne t1, t2, fail
    la t0, zero_area
    lw t1, 0(t0)
    bne t1, zero, fail
    lw t1, 4(t0)
    bne t1, zero, fail
    la t0, signature
    li t1, 0x600d600d
    sw t1, 0(t0)
    addi a0, zero, 0
    jal zero, done
fail:
    addi a0, zero, 1
done:
    lw ra, 12(sp)
    addi sp, sp, 16
    jalr zero, 0(ra)
    .size main, .-main
    .section .data,"aw",@progbits
    .balign 4
    .globl initial_data
initial_data:
    .word 0xcafebabe, 0x13579bdf
    .section .bss,"aw",@nobits
    .balign 4
    .globl zero_area, signature
zero_area:
    .space 8
signature:
    .space 4
    .section .note.GNU-stack,"",@progbits
