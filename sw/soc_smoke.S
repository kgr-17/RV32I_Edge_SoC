/* RV32I/ILP32 SoC smoke under the reviewed fatal-halt EEI. */
    .option norvc
    .option norelax
    .section .text,"ax",@progbits
    .globl main
main:
    addi sp, sp, -16
    sw ra, 12(sp)
    la t0, initial_data
    lw t1, 0(t0)
    li t2, 0xcafebabe
    bne t1, t2, failed
    lw t1, 4(t0)
    li t2, 0x13579bdf
    bne t1, t2, failed
    la t0, zero_area
    lw t1, 0(t0)
    lw t2, 4(t0)
    or t1, t1, t2
    bne t1, zero, failed
    li t1, 0x80ff7f01
    sw t1, 0(t0)
    lb t2, 3(t0)
    li t3, -128
    bne t2, t3, failed
    lbu t2, 3(t0)
    li t3, 128
    bne t2, t3, failed
    li t1, 0x1234
    sh t1, 2(t0)
    lhu t2, 2(t0)
    bne t2, t1, failed
    li t1, 0x55
    sb t1, 1(t0)
    lw t2, 0(t0)
    li t3, 0x12345501
    bne t2, t3, failed
    /* This word lies outside linker runtime initialization and survives reset. */
    li t0, 0x0001e000
    lw t1, 0(t0)
    addi t1, t1, 1
    sw t1, 0(t0)
    li t0, 0x10000020
    lw t1, 4(t0)
    sw t1, 0(t0)
    li t2, 0xf0
    sb t2, 8(t0)
    li t2, 0x0f
    sb t2, 12(t0)
    ori t1, t1, 0xf0
    andi t1, t1, -16
    lw t2, 0(t0)
    bne t1, t2, failed
    li t0, 0x10000100
    sw zero, 8(t0)
    li t1, -4
    sw t1, 0(t0)
    sw zero, 4(t0)
    li t1, 1
    sw t1, 8(t0)
1:  lw t2, 12(t0)
    andi t2, t2, 1
    beq t2, zero, 1b
    sw t1, 12(t0)
    sw zero, 8(t0)
    lw t2, 12(t0)
    bne t2, zero, failed
    li t0, 0x10000000
2:  lw t1, 4(t0)
    andi t1, t1, 2
    beq t1, zero, 2b
    lbu t1, 8(t0)
    li t2, 0x41
    bne t1, t2, failed
    fence iorw, iorw
    la a1, pass_message
    jal ra, put_string
    la t0, signature
    li t1, 0x600d600d
    sw t1, 0(t0)
    li a0, 0
    jal zero, finished
failed:
    la a1, fail_message
    jal ra, put_string
    li a0, 1
finished:
    lw ra, 12(sp)
    addi sp, sp, 16
    jalr zero, 0(ra)
put_string:
    li t3, 0x10000000
3:  lbu t0, 0(a1)
    beq t0, zero, 4f
    /* A busy UART stalls the real CPU bus, exercising stable held requests. */
    sb t0, 0(t3)
    addi a1, a1, 1
    jal zero, 3b
4:  lw t0, 4(t3)
    andi t0, t0, 1
    beq t0, zero, 4b
    jalr zero, 0(ra)
    .section .rodata,"a",@progbits
pass_message: .asciz "PASS\r\n"
fail_message: .asciz "FAIL\r\n"
    .section .data,"aw",@progbits
    .balign 4
    .globl initial_data
initial_data: .word 0xcafebabe, 0x13579bdf
    .section .bss,"aw",@nobits
    .balign 4
    .globl zero_area, signature
zero_area: .space 8
signature: .space 4
    .section .note.GNU-stack,"",@progbits
