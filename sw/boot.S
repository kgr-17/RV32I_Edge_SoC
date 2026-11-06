/* RV32I/ILP32 initial fatal-halt EEI. No CSRs, privileged mode, libc or UART. */
    .option norvc
    .option norelax
    .section .text.init,"ax",@progbits
    .globl _start, halt_ecall
    .type _start,@function
_start:
    la sp, __stack_top
    la t0, __data_load
    la t1, __data_start
    la t2, __data_end
1:  bgeu t1, t2, 2f
    lw t3, 0(t0)
    sw t3, 0(t1)
    addi t0, t0, 4
    addi t1, t1, 4
    jal zero, 1b
2:  la t0, __bss_start
    la t1, __bss_end
3:  bgeu t0, t1, 4f
    sw zero, 0(t0)
    addi t0, t0, 4
    jal zero, 3b
4:  jal ra, main
halt_ecall:
    ecall
5:  jal zero, 5b
    .size _start, .-_start
    .section .note.GNU-stack,"",@progbits
