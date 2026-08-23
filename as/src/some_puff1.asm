; Copyright (C) 2026 Lenik <zephyr@bodz.net>
; SPDX-License-Identifier: AGPL-3.0-or-later

%include "commons.inc"

section .bss
    buffer: resb BUF_SIZE

section .text
global _start

_start:
.read_loop:
    mov rax, SYS_read
    mov rdi, STDIN
    mov rsi, buffer
    mov rdx, BUF_SIZE
    syscall
    cmp rax, 0
    jle .done
    mov rdx, rax
    mov rax, SYS_write
    mov rdi, STDOUT
    mov rsi, buffer
    syscall
    jmp .read_loop

.done:
    mov rax, SYS_exit
    xor rdi, rdi
    syscall
