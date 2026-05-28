# Integrantes do grupo (ordem alfabética):
# Dani Heart Basso - @dani-heart
# Mariana Alves da Silva - @himarialves
#
# Nome do grupo no Canvas: RA2-18

"""Construtor de árvore sintática e utilitários de serialização.

Define No (nó da árvore), ConstrutorNo (implementação de ConstrutorArvore)
e gerarArvore(), que integra parser + builder para produzir a árvore.
"""

import json
from dataclasses import dataclass
from typing import Optional

from parser import parsear, ErroSintatico


# ---------------------------------------------------------------------------
# Dataclass do nó da árvore sintática
# ---------------------------------------------------------------------------

# No pertence a aluno 4. Parser não conhece esta classe — recebe e passa handles
# opacos (Any). A separação é garantida pelo ConstrutorArvore Protocol em parser.py.
#
# Por que dataclass? Gera __init__, __eq__ e __repr__ automaticamente.
# valor é Optional porque nós compostos (EXPR, IF, WHILE, BLOCO, PROGRAMA) não têm
# valor literal — só folhas (OPERANDO, MEM_ID, OP) têm.
@dataclass
class No:
    """Nó da árvore sintática do programa RPN."""
    tipo: str
    valor: Optional[str]
    filhos: list
    linha: int
    tipo_dado: Optional[str] = None # Fase 3: int, double ou bool (Árvore Atribuída)

    def __repr__(self) -> str:
        return f"No(tipo={self.tipo!r}, valor={self.valor!r}, tipo_dado={self.tipo_dado!r}, filhos={self.filhos!r}, linha={self.linha})"


# ---------------------------------------------------------------------------
# Construtor concreto — implementa ConstrutorArvore, produz nós No
# ---------------------------------------------------------------------------

# ConstrutorNo implementa o Protocol ConstrutorArvore definido em parser.py.
# O parser chama os métodos sem saber que existe esta classe — injeção de dependência.
class ConstrutorNo:
    """Implementação de ConstrutorArvore que produz nós No."""

    def criar_operando_num(self, valor: str, linha: int) -> No:
        return No(tipo="OPERANDO", valor=valor, filhos=[], linha=linha)

    def criar_operando_mem(self, nome: str, linha: int) -> No:
        return No(tipo="MEM_ID", valor=nome, filhos=[], linha=linha)

    def criar_operador(self, simbolo: str, linha: int) -> No:
        return No(tipo="OP", valor=simbolo, filhos=[], linha=linha)

    def criar_expr(self, esq: No, dir: No, op: No, linha: int) -> No:
        # Ordem dos filhos espelha a gramática RPN: [esq, dir, op].
        # assembly.py acessa por índice: filhos[0]=esq, filhos[1]=dir, filhos[2]=op.
        return No(tipo="EXPR", valor=None, filhos=[esq, dir, op], linha=linha)

    def criar_cmd_res(self, n: str, linha: int) -> No:
        # n é uma string numérica (ex: "1"). Embrulhamos num nó OPERANDO para manter
        # a árvore uniforme — assembly.py lê filhos[0].valor sem tratar casos especiais.
        n_no = No(tipo="OPERANDO", valor=n, filhos=[], linha=linha)
        return No(tipo="CMD_RES", valor=None, filhos=[n_no], linha=linha)

    def criar_cmd_mem_store(self, valor: str, nome: str, linha: int) -> No:
        # filhos[0] = valor a armazenar, filhos[1] = nome da variável.
        # Ordem importa: assembly.py desestrutura nessa sequência.
        valor_no = No(tipo="OPERANDO", valor=valor, filhos=[], linha=linha)
        mem_id = No(tipo="MEM_ID", valor=nome, filhos=[], linha=linha)
        return No(tipo="CMD_MEM_STORE", valor=None, filhos=[valor_no, mem_id], linha=linha)

    def criar_cmd_mem_load(self, nome: str, linha: int) -> No:
        mem_id = No(tipo="MEM_ID", valor=nome, filhos=[], linha=linha)
        return No(tipo="CMD_MEM_LOAD", valor=None, filhos=[mem_id], linha=linha)

    def criar_bloco(self, cmds: list, linha: int) -> No:
        return No(tipo="BLOCO", valor=None, filhos=cmds, linha=linha)

    def criar_if(self, cond: No, bloco: No, linha: int) -> No:
        return No(tipo="IF", valor=None, filhos=[cond, bloco], linha=linha)

    def criar_while(self, cond: No, bloco: No, linha: int) -> No:
        return No(tipo="WHILE", valor=None, filhos=[cond, bloco], linha=linha)

    def criar_programa(self, cmds: list, linha: int) -> No:
        return No(tipo="PROGRAMA", valor=None, filhos=cmds, linha=linha)


# ---------------------------------------------------------------------------
# Interface pública
# ---------------------------------------------------------------------------

def gerarArvore(tokens: list, tabela_ll1: dict) -> No:
    """Constrói a árvore sintática a partir dos tokens e da tabela LL(1)."""
    # Builder criado aqui (aluno 4) e injetado no parser (aluno 2).
    # Parser não sabe que ConstrutorNo existe — só conhece o Protocol.
    builder = ConstrutorNo()
    return parsear(tokens, tabela_ll1, builder)

def imprimir_arvore(no: No, indent: int = 0) -> None:
    """Imprime a árvore sintática de forma indentada no stdout."""
    # Recursiva porque a árvore é recursiva. indent cresce a cada nível de filho.
    # Nós sem valor (compostos) mostram só o tipo; folhas mostram o valor literal.
    prefixo = "  " * indent
    tipo_str = f" : {no.tipo_dado}" if no.tipo_dado else ""
    if no.valor is not None:
        print(f"{prefixo}[{no.tipo}{tipo_str}] '{no.valor}'  (linha {no.linha})")
    else:
        print(f"{prefixo}[{no.tipo}{tipo_str}]  (linha {no.linha})")
    for filho in no.filhos:
        imprimir_arvore(filho, indent + 1)

def _no_para_dict(no: No) -> dict:
    # Privada: detalhe de implementação da serialização JSON.
    # Recursiva pela mesma razão que imprimir_arvore — a estrutura é uma árvore.
    return {
        "tipo": no.tipo,
        "valor": no.valor,
        "linha": no.linha,
        "tipo_dado": no.tipo_dado,
        "filhos": [_no_para_dict(f) for f in no.filhos]
    }

def salvar_arvore_json(no: No, caminho: str) -> None:
    """Serializa a árvore sintática para um arquivo JSON."""
    dados = _no_para_dict(no)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print(f"Árvore salva em: {caminho}")
