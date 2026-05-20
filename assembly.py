# Integrantes do grupo (ordem alfabética):
# Dani Heart Basso - @dani-heart
# Mariana Alves da Silva - @himarialves
#
# Nome do grupo no Canvas: RA2-18


from arvore import No


# Convenções do gerador (F64 unificado — sem VCVT.S32.F64)
#
# - TODAS as expressões deixam resultado em D0 (VFP F64, 64 bits).
# - Pilha: VPUSH {D0} / VPOP {D1} (8 bytes). Esq em D1 após pop, dir em D0.
# - Variáveis MEM: .double 0.0 em .data. VLDR D0, [R1] para carregar;
#   VSTR D0, [R1] para salvar. Nunca trunca.
# - Histórico RES: .space 2048 (256 × 8 bytes). CMD_RES usa VLDR D0 — sem truncamento.
# - Inteiros literais: MOV/LDR R0 → VMOV S0 → VCVT.F64.S32 D0, S0 (lossless).
#   Floats literais: VLDR D0, label (.double em .data).
# - +, -, *: VADD.F64 / VSUB.F64 / VMUL.F64.
# - loop de subtração em F64 — D2=dividendo, D3=divisor, D4=contador,
#   D5=1.0 (incremento). VDIV não suportado no CPulator DEC1-SOC.
# - %: mesmo loop de subtração, retorna D2 (resto) em vez do contador D4.
# - ^: loop de multiplicação em F64 — D2=base, D3=expoente, D4=acumulador.
# - Relacionais: VCMP.F64 D1, D0 + VMRS APSR_nzcv, FPSCR →
#   VLDR D0, CONST_ZERO ou VLDR D0, CONST_ONE (evita VMOV.F64 #imm no CPulator).
# - IF/WHILE: VCMP.F64 D0, #0.0 + VMRS APSR_nzcv, FPSCR + BEQ.
# - CONST_ZERO e CONST_ONE: sempre em .data; usados por loops e relacionais.

_label_count = 0


def _novo_label(prefixo: str = "L") -> str:
    # Sem esse contador, dois IFs no mesmo programa gerariam IF_FIM duplicado.
    global _label_count
    _label_count += 1
    return f"{prefixo}_{_label_count}"


def _coletar_mem_ids(no: No, vistos: set[str]) -> None:
    if no.tipo == "MEM_ID" and no.valor is not None:
        vistos.add(no.valor)
    for filho in no.filhos:
        _coletar_mem_ids(filho, vistos)


def _coletar_floats(no: No, floats: dict[str, str]) -> None:
    # Apenas literais com '.' viram labels .double em .data.
    # Inteiros são convertidos inline; não precisam de label.
    if no.tipo == "OPERANDO" and no.valor is not None and "." in no.valor:
        label = f"FC_{no.valor.replace('.', '_').replace('-', 'N')}"
        floats[label] = no.valor
    for filho in no.filhos:
        _coletar_floats(filho, floats)


_float_labels: dict[str, str] = {}


def _label_para_float(val: str) -> str:
    return f"FC_{val.replace('.', '_').replace('-', 'N')}"


def _gerar_operando_em_d0(no: No) -> str:
    if no.tipo == "OPERANDO":
        val = no.valor or "0"
        if "." in val:
            # Constante double: VLDR carrega 8 bytes do label .double em .data.
            label = _label_para_float(val)
            return f"    LDR R6, ={label}\n    VLDR D0, [R6]  @ real {val}"
        else:
            # Inteiro: S0 é ponte obrigatória no ARMv7 (não existe VCVT Dd, Rn).
            # S0 carrega o padrão de bits inteiro; VCVT promove para F64 em D0.
            ival = int(val)
            if 0 <= ival <= 255:
                return (
                    f"    MOV R0, #{ival}\n"
                    f"    VMOV S0, R0\n"
                    f"    VCVT.F64.S32 D0, S0  @ int {val} -> F64"
                )
            else:
                return (
                    f"    LDR R0, ={ival}\n"
                    f"    VMOV S0, R0\n"
                    f"    VCVT.F64.S32 D0, S0  @ int {val} -> F64"
                )
    elif no.tipo == "MEM_ID":
        nome = no.valor or "?"
        return (
            f"    LDR R1, ={nome}\n"
            f"    VLDR D0, [R1]  @ MEM {nome} -> D0"
        )
    elif no.tipo == "EXPR":
        return _gerar_expr(no, salvar_res=False)
    else:
        return f"    @ operando desconhecido: {no.tipo}"


def _gerar_op(op: str) -> str:
    if op == "+":
        return "    VADD.F64 D0, D1, D0"
    elif op == "-":
        return "    VSUB.F64 D0, D1, D0"
    elif op == "*":
        return "    VMUL.F64 D0, D1, D0"

    elif op in ("|", "/"):
        # VDIV não suportado no CPulator DEC1-SOC — loop de subtração em F64.
        # D2=dividendo, D3=divisor, D4=contador, D5=incremento (1.0).
        # Sem VCVT: tudo permanece F64 do início ao fim.
        label_loop = _novo_label("DIV_LOOP")
        label_fim = _novo_label("DIV_FIM")
        return (
            f"    @ divisao via loop de subtracao em F64 (VDIV nao suportado)\n"
            f"    VMOV.F64 D2, D1         @ D2 = esq (dividendo)\n"
            f"    VMOV.F64 D3, D0         @ D3 = dir (divisor)\n"
            f"    LDR R6, =CONST_ZERO\n"
            f"    VLDR D4, [R6]           @ D4 = contador\n"
            f"    LDR R6, =CONST_ONE\n"
            f"    VLDR D5, [R6]           @ D5 = incremento\n"
            f"{label_loop}:\n"
            f"    VCMP.F64 D2, D3\n"
            f"    VMRS APSR_nzcv, FPSCR\n"
            f"    BLT {label_fim}\n"
            f"    VSUB.F64 D2, D2, D3\n"
            f"    VADD.F64 D4, D4, D5\n"
            f"    B {label_loop}\n"
            f"{label_fim}:\n"
            f"    VMOV.F64 D0, D4         @ quociente -> D0"
        )

    elif op == "%":
        # Módulo: mesmo loop do /, mas retorna D2 (o que sobrou no dividendo)
        # em vez do contador D4.
        label_loop = _novo_label("MOD_LOOP")
        label_fim = _novo_label("MOD_FIM")
        return (
            f"    @ modulo via loop de subtracao em F64\n"
            f"    VMOV.F64 D2, D1         @ D2 = esq (dividendo)\n"
            f"    VMOV.F64 D3, D0         @ D3 = dir (divisor)\n"
            f"{label_loop}:\n"
            f"    VCMP.F64 D2, D3\n"
            f"    VMRS APSR_nzcv, FPSCR\n"
            f"    BLT {label_fim}\n"
            f"    VSUB.F64 D2, D2, D3\n"
            f"    B {label_loop}\n"
            f"{label_fim}:\n"
            f"    VMOV.F64 D0, D2         @ resto -> D0"
        )

    elif op == "^":
        # Loop de multiplicação em F64. D2=base, D3=expoente (decrementado), D4=acumulador.
        label_loop = _novo_label("POT_LOOP")
        label_fim = _novo_label("POT_FIM")
        return (
            f"    @ potencia via loop de multiplicacao em F64\n"
            f"    VMOV.F64 D2, D1         @ D2 = base\n"
            f"    VMOV.F64 D3, D0         @ D3 = expoente (contador)\n"
            f"    LDR R6, =CONST_ONE\n"
            f"    VLDR D4, [R6]           @ D4 = acumulador\n"
            f"    LDR R6, =CONST_ONE\n"
            f"    VLDR D5, [R6]           @ D5 = decremento\n"
            f"{label_loop}:\n"
            f"    VCMP.F64 D3, #0.0\n"
            f"    VMRS APSR_nzcv, FPSCR\n"
            f"    BLE {label_fim}\n"
            f"    VMUL.F64 D4, D4, D2\n"
            f"    VSUB.F64 D3, D3, D5\n"
            f"    B {label_loop}\n"
            f"{label_fim}:\n"
            f"    VMOV.F64 D0, D4         @ resultado -> D0"
        )

    # Operadores relacionais: VCMP.F64 D1, D0 compara D1 (esq) com D0 (dir).
    # VMRS copia flags VFP para APSR, permitindo branches condicionais normais.
    # VMOV.F64 Dd, #imm carrega imediato F64 direto no registrador — sem passar por S0.
    # Resultado: D0 = 1.0 (verdadeiro) ou 0.0 (falso).
    elif op == ">":
        lt, le = _novo_label("GT_T"), _novo_label("GT_E")
        return (
            f"    VCMP.F64 D1, D0\n"
            f"    VMRS APSR_nzcv, FPSCR\n"
            f"    BGT {lt}\n"
            f"    LDR R6, =CONST_ZERO\n"
            f"    VLDR D0, [R6]\n"
            f"    B {le}\n"
            f"{lt}:\n"
            f"    LDR R6, =CONST_ONE\n"
            f"    VLDR D0, [R6]\n"
            f"{le}:"
        )
    elif op == "<":
        lt, le = _novo_label("LT_T"), _novo_label("LT_E")
        return (
            f"    VCMP.F64 D1, D0\n"
            f"    VMRS APSR_nzcv, FPSCR\n"
            f"    BLT {lt}\n"
            f"    LDR R6, =CONST_ZERO\n"
            f"    VLDR D0, [R6]\n"
            f"    B {le}\n"
            f"{lt}:\n"
            f"    LDR R6, =CONST_ONE\n"
            f"    VLDR D0, [R6]\n"
            f"{le}:"
        )
    elif op == "==":
        lt, le = _novo_label("EQ_T"), _novo_label("EQ_E")
        return (
            f"    VCMP.F64 D1, D0\n"
            f"    VMRS APSR_nzcv, FPSCR\n"
            f"    BEQ {lt}\n"
            f"    LDR R6, =CONST_ZERO\n"
            f"    VLDR D0, [R6]\n"
            f"    B {le}\n"
            f"{lt}:\n"
            f"    LDR R6, =CONST_ONE\n"
            f"    VLDR D0, [R6]\n"
            f"{le}:"
        )
    elif op == "!=":
        lt, le = _novo_label("NE_T"), _novo_label("NE_E")
        return (
            f"    VCMP.F64 D1, D0\n"
            f"    VMRS APSR_nzcv, FPSCR\n"
            f"    BNE {lt}\n"
            f"    LDR R6, =CONST_ZERO\n"
            f"    VLDR D0, [R6]\n"
            f"    B {le}\n"
            f"{lt}:\n"
            f"    LDR R6, =CONST_ONE\n"
            f"    VLDR D0, [R6]\n"
            f"{le}:"
        )
    elif op == ">=":
        lt, le = _novo_label("GE_T"), _novo_label("GE_E")
        return (
            f"    VCMP.F64 D1, D0\n"
            f"    VMRS APSR_nzcv, FPSCR\n"
            f"    BGE {lt}\n"
            f"    LDR R6, =CONST_ZERO\n"
            f"    VLDR D0, [R6]\n"
            f"    B {le}\n"
            f"{lt}:\n"
            f"    LDR R6, =CONST_ONE\n"
            f"    VLDR D0, [R6]\n"
            f"{le}:"
        )
    elif op == "<=":
        lt, le = _novo_label("LE_T"), _novo_label("LE_E")
        return (
            f"    VCMP.F64 D1, D0\n"
            f"    VMRS APSR_nzcv, FPSCR\n"
            f"    BLE {lt}\n"
            f"    LDR R6, =CONST_ZERO\n"
            f"    VLDR D0, [R6]\n"
            f"    B {le}\n"
            f"{lt}:\n"
            f"    LDR R6, =CONST_ONE\n"
            f"    VLDR D0, [R6]\n"
            f"{le}:"
        )
    else:
        return f"    @ operador desconhecido: {op}"


def _gerar_expr(no: No, salvar_res: bool) -> str:
    op_esq, op_dir, op_no = no.filhos[0], no.filhos[1], no.filhos[2]
    op = op_no.valor or "?"

    linhas: list[str] = [f"    @ EXPR {op}"]

    # Padrão uniforme: avalia esq -> empilha -> avalia dir -> desempilha em D1 -> opera.
    # Resultado sempre em D0 (F64), independente de os operandos serem int ou float.
    linhas.append(_gerar_operando_em_d0(op_esq))
    linhas.append("    VPUSH {D0}  @ empilha esq (8 bytes)")
    linhas.append(_gerar_operando_em_d0(op_dir))
    linhas.append("    VPOP {D1}   @ desempilha esq em D1")
    linhas.append(_gerar_op(op))

    if salvar_res:
        # D0 é sempre F64 aqui — VSTR salva 8 bytes sem truncar.
        linhas.append("    @ salva resultado F64 no historico (8 bytes)")
        linhas.append("    LDR R3, =RES_IDX")
        linhas.append("    LDR R2, [R3]")
        linhas.append("    LDR R4, =RES_HIST")
        linhas.append("    ADD R6, R4, R2, LSL #3")
        linhas.append("    VSTR D0, [R6]")
        linhas.append("    ADD R2, R2, #1")
        linhas.append("    STR R2, [R3]")

    return "\n".join(linhas)


def _gerar_mem_load(no: No) -> str:
    nome = no.valor or "?"
    return (
        f"    @ carregar MEM {nome} -> D0\n"
        f"    LDR R1, ={nome}\n"
        f"    VLDR D0, [R1]"
    )


def _gerar_cmd_mem_store(no: No) -> str:
    valor_no, mem_id_no = no.filhos[0], no.filhos[1]
    nome = mem_id_no.valor or "?"
    linhas = [f"    @ CMD_MEM_STORE: {nome} = {valor_no.valor}"]
    linhas.append(_gerar_operando_em_d0(valor_no))
    linhas.append(f"    LDR R1, ={nome}")
    linhas.append(f"    VSTR D0, [R1]  @ salva F64 em {nome}")
    return "\n".join(linhas)


def _gerar_cmd_mem_load(no: No) -> str:
    mem_id_no = no.filhos[0]
    nome = mem_id_no.valor or "?"
    return (
        f"    @ CMD_MEM_LOAD: D0 = {nome}\n"
        f"    LDR R1, ={nome}\n"
        f"    VLDR D0, [R1]"
    )


def _gerar_cmd_res(no: No) -> str:
    # RES_HIST armazena F64 (8 bytes por entrada). LSL #3 = índice × 8.
    # VLDR D0 carrega 8 bytes sem truncar — resultado permanece F64.
    n_no = no.filhos[0]
    n_val = int(n_no.valor or "0")
    linhas = [f"    @ CMD_RES: resultado de {n_val} posicao(oes) atras -> D0"]
    linhas.append("    LDR R3, =RES_IDX")
    linhas.append("    LDR R2, [R3]")
    if n_val > 0:
        linhas.append(f"    SUB R2, R2, #{n_val}")
    linhas.append("    LDR R4, =RES_HIST")
    linhas.append("    ADD R6, R4, R2, LSL #3")
    linhas.append("    VLDR D0, [R6]")
    return "\n".join(linhas)


def _gerar_programa(no: No) -> str:
    linhas: list[str] = []

    linhas.append(".text")
    linhas.append("@ Assembly ARMv7 gerado automaticamente — RA2-18")
    linhas.append("@ Plataforma: CPulator ARMv7 DEC1-SOC v16.1")
    linhas.append("")
    linhas.append(".global _start")
    linhas.append("_start:")
    linhas.append("")

    # CPulator bare-metal não inicializa SP — sem isso VPUSH/VPOP corrompem memória.
    linhas.append("    @ Inicializa stack pointer")
    linhas.append("    LDR SP, =STACK_TOP")
    linhas.append("")

    # FPEXC bit 30 (EN) = 1 habilita o coprocessador VFP.
    # Sem isso qualquer VLDR/VADD.F64/VCMP.F64 gera undefined instruction fault.
    linhas.append("    @ Habilita coprocessador VFP")
    linhas.append("    LDR R0, =0x40000000")
    linhas.append("    FMXR FPEXC, R0")
    linhas.append("")

    # Inicializa RES_IDX em zero. Índice conta entradas (não bytes).
    linhas.append("    @ Inicializa indice do historico RES")
    linhas.append("    LDR R4, =RES_IDX")
    linhas.append("    MOV R5, #0")
    linhas.append("    STR R5, [R4]")
    linhas.append("")

    for filho in no.filhos:
        linhas.append(_gerar_cmd_topo(filho))
        linhas.append("")

    linhas.append("_end:")
    linhas.append("    B _end")
    linhas.append("")

    return "\n".join(linhas)


def _gerar_cmd_topo(no: No) -> str:
    # Só EXPR produz um valor numérico que vai para o histórico RES.
    if no.tipo == "EXPR":
        return _gerar_expr(no, salvar_res=True)
    else:
        return _gerar_no(no)


def _gerar_no(no: No) -> str:
    if no.tipo == "PROGRAMA":
        raise ValueError("_gerar_no nao deve receber PROGRAMA diretamente.")
    elif no.tipo == "EXPR":
        return _gerar_expr(no, salvar_res=False)
    elif no.tipo == "OPERANDO":
        return _gerar_operando_em_d0(no)
    elif no.tipo == "MEM_ID":
        return _gerar_mem_load(no)
    elif no.tipo == "CMD_MEM_STORE":
        return _gerar_cmd_mem_store(no)
    elif no.tipo == "CMD_MEM_LOAD":
        return _gerar_cmd_mem_load(no)
    elif no.tipo == "CMD_RES":
        return _gerar_cmd_res(no)
    elif no.tipo == "IF":
        return _gerar_if(no)
    elif no.tipo == "WHILE":
        return _gerar_while(no)
    elif no.tipo == "BLOCO":
        return _gerar_bloco(no)
    elif no.tipo == "OP":
        return f"    @ OP {no.valor}"
    else:
        return f"    @ [no desconhecido: {no.tipo}]"


def _gerar_if(no: No) -> str:
    # Condição avaliada em D0. VCMP.F64 D0, #0.0 testa se é zero (falso).
    # VMRS copia flags VFP para APSR para permitir BEQ.
    cond_no, bloco_no = no.filhos[0], no.filhos[1]
    label_fim = _novo_label("IF_FIM")

    linhas = ["    @ IF -- avalia condicao -> D0"]
    linhas.append(_gerar_no(cond_no))
    linhas.append("    VCMP.F64 D0, #0.0")
    linhas.append("    VMRS APSR_nzcv, FPSCR")
    linhas.append(f"    BEQ {label_fim}  @ pula se falso (D0 == 0.0)")
    linhas.append("    @ bloco IF")
    linhas.append(_gerar_bloco(bloco_no))
    linhas.append(f"{label_fim}:")
    return "\n".join(linhas)


def _gerar_while(no: No) -> str:
    # Mesmo esquema do IF: condição em D0, VCMP + VMRS + BEQ para sair.
    cond_no, bloco_no = no.filhos[0], no.filhos[1]
    label_loop = _novo_label("WHILE_LOOP")
    label_fim = _novo_label("WHILE_FIM")

    linhas = ["    @ WHILE"]
    linhas.append(f"{label_loop}:")
    linhas.append("    @ avalia condicao -> D0")
    linhas.append(_gerar_no(cond_no))
    linhas.append("    VCMP.F64 D0, #0.0")
    linhas.append("    VMRS APSR_nzcv, FPSCR")
    linhas.append(f"    BEQ {label_fim}  @ sai se falso (D0 == 0.0)")
    linhas.append("    @ corpo do WHILE")
    linhas.append(_gerar_bloco(bloco_no))
    linhas.append(f"    B {label_loop}")
    linhas.append(f"{label_fim}:")
    return "\n".join(linhas)


def _gerar_bloco(no: No) -> str:
    partes = [f"    @ BLOCO ({len(no.filhos)} comando(s))"]
    for filho in no.filhos:
        partes.append(_gerar_no(filho))
    return "\n".join(partes)


def _gerar_secao_dados(mem_ids: list[str], floats: dict[str, str]) -> str:
    linhas = [".data"]
    linhas.append("")
    linhas.append("@ Historico de resultados (maximo 256 entradas x 8 bytes = F64)")
    linhas.append("RES_IDX: .word 0")
    linhas.append("RES_HIST: .space 2048")
    linhas.append("")
    # Constantes usadas nos loops F64 e nos operadores relacionais.
    # VLDR é mais seguro que VMOV.F64 #imm no CPulator (suporte a imediatos limitado).
    linhas.append("@ Constantes auxiliares para loops e relacionais")
    linhas.append("CONST_ZERO: .double 0.0")
    linhas.append("CONST_ONE:  .double 1.0")
    linhas.append("")

    if mem_ids:
        # .double 0.0 garante 8-byte alignment — necessário para VLDR/VSTR D0, [R1].
        linhas.append("@ Variaveis de memoria (F64, 8 bytes cada)")
        for nome in sorted(mem_ids):
            linhas.append(f"{nome}: .double 0.0")
        linhas.append("")

    if floats:
        linhas.append("@ Constantes de ponto flutuante (F64)")
        for label, val in sorted(floats.items()):
            linhas.append(f"{label}: .double {val}")
        linhas.append("")

    linhas.append("@ Pilha de software (1 KB)")
    linhas.append("STACK: .space 1024")
    linhas.append("STACK_TOP:")
    linhas.append("")

    return "\n".join(linhas)


def gerarAssembly(arvore: No) -> str:
    global _label_count, _float_labels
    _label_count = 0

    mem_ids: set[str] = set()
    _coletar_mem_ids(arvore, mem_ids)
    mem_lista = sorted(mem_ids)

    _float_labels = {}
    _coletar_floats(arvore, _float_labels)

    secao_dados = _gerar_secao_dados(mem_lista, _float_labels)
    secao_texto = _gerar_programa(arvore)

    return secao_dados + "\n" + secao_texto
