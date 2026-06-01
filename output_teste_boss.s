.data

@ Historico de resultados (maximo 256 entradas x 8 bytes = F64)
RES_IDX: .word 0
RES_HIST: .space 2048

@ Constantes auxiliares para loops e relacionais
CONST_ZERO: .double 0.0
CONST_ONE:  .double 1.0

@ Variaveis de memoria (F64, 8 bytes cada)
ATIVO: .double 0.0
X: .double 0.0

@ Constantes de ponto flutuante (F64)
FC_0_0: .double 0.0
FC_10_0: .double 10.0
FC_1_0: .double 1.0
FC_2_0: .double 2.0
FC_3_0: .double 3.0
FC_4_0: .double 4.0
FC_5_0: .double 5.0

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

    @ CMD_MEM_STORE: X = 4.0
    LDR R6, =FC_4_0
    VLDR D0, [R6]  @ real 4.0
    LDR R1, =X
    VSTR D0, [R1]  @ salva F64 em X

    @ EXPR -
    @ EXPR +
    @ EXPR -
    @ EXPR *
    LDR R6, =FC_3_0
    VLDR D0, [R6]  @ real 3.0
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ EXPR ^
    LDR R1, =X
    VLDR D0, [R1]  @ MEM X -> D0
    VPUSH {D0}  @ empilha esq (8 bytes)
    LDR R6, =FC_3_0
    VLDR D0, [R6]  @ real 3.0
    VPOP {D1}   @ desempilha esq em D1
    @ potencia via loop de multiplicacao em F64
    VMOV.F64 D2, D1         @ D2 = base
    VMOV.F64 D3, D0         @ D3 = expoente (contador)
    LDR R6, =CONST_ONE
    VLDR D4, [R6]           @ D4 = acumulador
    LDR R6, =CONST_ONE
    VLDR D5, [R6]           @ D5 = decremento
POT_LOOP_1:
    VCMP.F64 D3, #0.0
    VMRS APSR_nzcv, FPSCR
    BLE POT_FIM_2
    VMUL.F64 D4, D4, D2
    VSUB.F64 D3, D3, D5
    B POT_LOOP_1
POT_FIM_2:
    VMOV.F64 D0, D4         @ resultado -> D0
    VPOP {D1}   @ desempilha esq em D1
    VMUL.F64 D0, D1, D0
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ EXPR *
    LDR R6, =FC_5_0
    VLDR D0, [R6]  @ real 5.0
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ EXPR ^
    LDR R1, =X
    VLDR D0, [R1]  @ MEM X -> D0
    VPUSH {D0}  @ empilha esq (8 bytes)
    LDR R6, =FC_2_0
    VLDR D0, [R6]  @ real 2.0
    VPOP {D1}   @ desempilha esq em D1
    @ potencia via loop de multiplicacao em F64
    VMOV.F64 D2, D1         @ D2 = base
    VMOV.F64 D3, D0         @ D3 = expoente (contador)
    LDR R6, =CONST_ONE
    VLDR D4, [R6]           @ D4 = acumulador
    LDR R6, =CONST_ONE
    VLDR D5, [R6]           @ D5 = decremento
POT_LOOP_3:
    VCMP.F64 D3, #0.0
    VMRS APSR_nzcv, FPSCR
    BLE POT_FIM_4
    VMUL.F64 D4, D4, D2
    VSUB.F64 D3, D3, D5
    B POT_LOOP_3
POT_FIM_4:
    VMOV.F64 D0, D4         @ resultado -> D0
    VPOP {D1}   @ desempilha esq em D1
    VMUL.F64 D0, D1, D0
    VPOP {D1}   @ desempilha esq em D1
    VSUB.F64 D0, D1, D0
    VPUSH {D0}  @ empilha esq (8 bytes)
    @ EXPR *
    LDR R6, =FC_2_0
    VLDR D0, [R6]  @ real 2.0
    VPUSH {D0}  @ empilha esq (8 bytes)
    LDR R1, =X
    VLDR D0, [R1]  @ MEM X -> D0
    VPOP {D1}   @ desempilha esq em D1
    VMUL.F64 D0, D1, D0
    VPOP {D1}   @ desempilha esq em D1
    VADD.F64 D0, D1, D0
    VPUSH {D0}  @ empilha esq (8 bytes)
    LDR R6, =FC_10_0
    VLDR D0, [R6]  @ real 10.0
    VPOP {D1}   @ desempilha esq em D1
    VSUB.F64 D0, D1, D0
    @ salva resultado F64 no historico (8 bytes)
    LDR R3, =RES_IDX
    LDR R2, [R3]
    LDR R4, =RES_HIST
    ADD R6, R4, R2, LSL #3
    VSTR D0, [R6]
    ADD R2, R2, #1
    STR R2, [R3]

    @ CMD_MEM_STORE: ATIVO = 1
    MOV R0, #1
    VMOV S0, R0
    VCVT.F64.S32 D0, S0  @ int 1 -> F64
    LDR R1, =ATIVO
    VSTR D0, [R1]  @ salva F64 em ATIVO

    @ WHILE
WHILE_LOOP_5:
    @ avalia condicao -> D0
    @ EXPR ==
    LDR R1, =ATIVO
    VLDR D0, [R1]  @ MEM ATIVO -> D0
    VPUSH {D0}  @ empilha esq (8 bytes)
    MOV R0, #1
    VMOV S0, R0
    VCVT.F64.S32 D0, S0  @ int 1 -> F64
    VPOP {D1}   @ desempilha esq em D1
    VCMP.F64 D1, D0
    VMRS APSR_nzcv, FPSCR
    BEQ EQ_T_7
    LDR R6, =CONST_ZERO
    VLDR D0, [R6]
    B EQ_E_8
EQ_T_7:
    LDR R6, =CONST_ONE
    VLDR D0, [R6]
EQ_E_8:
    VCMP.F64 D0, #0.0
    VMRS APSR_nzcv, FPSCR
    BEQ WHILE_FIM_6  @ sai se falso (D0 == 0.0)
    @ corpo do WHILE
    @ BLOCO (2 comando(s))
    @ IF -- avalia condicao -> D0
    @ EXPR >
    LDR R1, =X
    VLDR D0, [R1]  @ MEM X -> D0
    VPUSH {D0}  @ empilha esq (8 bytes)
    LDR R6, =FC_0_0
    VLDR D0, [R6]  @ real 0.0
    VPOP {D1}   @ desempilha esq em D1
    VCMP.F64 D1, D0
    VMRS APSR_nzcv, FPSCR
    BGT GT_T_10
    LDR R6, =CONST_ZERO
    VLDR D0, [R6]
    B GT_E_11
GT_T_10:
    LDR R6, =CONST_ONE
    VLDR D0, [R6]
GT_E_11:
    VCMP.F64 D0, #0.0
    VMRS APSR_nzcv, FPSCR
    BEQ IF_FIM_9  @ pula se falso (D0 == 0.0)
    @ bloco IF
    @ BLOCO (1 comando(s))
    @ EXPR |
    @ EXPR +
    @ EXPR ^
    LDR R1, =X
    VLDR D0, [R1]  @ MEM X -> D0
    VPUSH {D0}  @ empilha esq (8 bytes)
    LDR R6, =FC_2_0
    VLDR D0, [R6]  @ real 2.0
    VPOP {D1}   @ desempilha esq em D1
    @ potencia via loop de multiplicacao em F64
    VMOV.F64 D2, D1         @ D2 = base
    VMOV.F64 D3, D0         @ D3 = expoente (contador)
    LDR R6, =CONST_ONE
    VLDR D4, [R6]           @ D4 = acumulador
    LDR R6, =CONST_ONE
    VLDR D5, [R6]           @ D5 = decremento
POT_LOOP_12:
    VCMP.F64 D3, #0.0
    VMRS APSR_nzcv, FPSCR
    BLE POT_FIM_13
    VMUL.F64 D4, D4, D2
    VSUB.F64 D3, D3, D5
    B POT_LOOP_12
POT_FIM_13:
    VMOV.F64 D0, D4         @ resultado -> D0
    VPUSH {D0}  @ empilha esq (8 bytes)
    LDR R6, =FC_1_0
    VLDR D0, [R6]  @ real 1.0
    VPOP {D1}   @ desempilha esq em D1
    VADD.F64 D0, D1, D0
    VPUSH {D0}  @ empilha esq (8 bytes)
    LDR R6, =FC_2_0
    VLDR D0, [R6]  @ real 2.0
    VPOP {D1}   @ desempilha esq em D1
    @ divisao via loop de subtracao em F64 (VDIV nao suportado)
    VMOV.F64 D2, D1         @ D2 = esq (dividendo)
    VMOV.F64 D3, D0         @ D3 = dir (divisor)
    LDR R6, =CONST_ZERO
    VLDR D4, [R6]           @ D4 = contador
    LDR R6, =CONST_ONE
    VLDR D5, [R6]           @ D5 = incremento
DIV_LOOP_14:
    VCMP.F64 D2, D3
    VMRS APSR_nzcv, FPSCR
    BLT DIV_FIM_15
    VSUB.F64 D2, D2, D3
    VADD.F64 D4, D4, D5
    B DIV_LOOP_14
DIV_FIM_15:
    VMOV.F64 D0, D4         @ quociente -> D0
IF_FIM_9:
    @ CMD_MEM_STORE: ATIVO = 0
    MOV R0, #0
    VMOV S0, R0
    VCVT.F64.S32 D0, S0  @ int 0 -> F64
    LDR R1, =ATIVO
    VSTR D0, [R1]  @ salva F64 em ATIVO
    B WHILE_LOOP_5
WHILE_FIM_6:

_end:
    B _end
