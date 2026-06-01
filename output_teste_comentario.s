.data

@ Historico de resultados (maximo 256 entradas x 8 bytes = F64)
RES_IDX: .word 0
RES_HIST: .space 2048

@ Constantes auxiliares para loops e relacionais
CONST_ZERO: .double 0.0
CONST_ONE:  .double 1.0

@ Pilha de software (1 KB)
STACK: .space 1024
STACK_TOP:

.text
@ Assembly ARMv7 gerado automaticamente — RA2-18
@ Plataforma: CPulator ARMv7 DEC1-SOC v16.1

.global _start
_start:

    @ Inicializa stack pointer
    LDR SP, =STACK_TOP

    @ Habilita coprocessador VFP
    LDR R0, =0x40000000
    FMXR FPEXC, R0

    @ Inicializa indice do historico RES
    LDR R4, =RES_IDX
    MOV R5, #0
    STR R5, [R4]

    @ EXPR +
    MOV R0, #10
    VMOV S0, R0
    VCVT.F64.S32 D0, S0  @ int 10 -> F64
    VPUSH {D0}  @ empilha esq (8 bytes)
    MOV R0, #20
    VMOV S0, R0
    VCVT.F64.S32 D0, S0  @ int 20 -> F64
    VPOP {D1}   @ desempilha esq em D1
    VADD.F64 D0, D1, D0
    @ salva resultado F64 no historico (8 bytes)
    LDR R3, =RES_IDX
    LDR R2, [R3]
    LDR R4, =RES_HIST
    ADD R6, R4, R2, LSL #3
    VSTR D0, [R6]
    ADD R2, R2, #1
    STR R2, [R3]

_end:
    B _end
