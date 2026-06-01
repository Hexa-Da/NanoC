extern printf, atoi
global main

section .data
argv: dq 0
format: db "%lld", 10, 0
DECL_VARS

section .text
main:
push rbp
mov rbp, rsp
mov [argv], rsi
INIT_VARS
COMMAND
RETURN
mov rsp, rbp
pop rbp
ret

FUNCTION_DEFS
