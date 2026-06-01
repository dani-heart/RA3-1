# Integrantes do grupo (ordem alfabética):
# Dani Heart Basso - @dani-heart
#
# Nome do grupo no Canvas: RA3-1

import pytest
from dataclasses import dataclass
from parser import parsear, ErroSintatico


@dataclass
class Token:
    tipo: str
    valor: str
    linha: int


class BuilderStub:
    """Builder mínimo que registra chamadas e retorna strings descritivas."""
    def __init__(self):
        self.chamadas: list = []

    def _reg(self, nome, *args):
        self.chamadas.append((nome, *args))

    def criar_operando_num(self, valor, linha):
        self._reg("criar_operando_num", valor)
        return f"NUM:{valor}"

    def criar_operando_mem(self, nome, linha):
        self._reg("criar_operando_mem", nome)
        return f"MEM:{nome}"

    def criar_operador(self, simbolo, linha):
        self._reg("criar_operador", simbolo)
        return f"OP:{simbolo}"

    def criar_expr(self, esq, dir, op, linha):
        self._reg("criar_expr", esq, dir, op)
        return f"EXPR({esq},{dir},{op})"

    def criar_cmd_res(self, n, linha):
        self._reg("criar_cmd_res", n)
        return f"RES:{n}"

    def criar_cmd_mem_store(self, valor_no, nome, linha):
        self._reg("criar_cmd_mem_store", valor_no, nome)
        return f"STORE:{nome}={valor_no}"

    def criar_cmd_mem_load(self, nome, linha):
        self._reg("criar_cmd_mem_load", nome)
        return f"LOAD:{nome}"

    def criar_bloco(self, cmds, linha):
        self._reg("criar_bloco", cmds)
        return f"BLOCO{cmds}"

    def criar_if(self, cond, bloco, linha):
        self._reg("criar_if", cond, bloco)
        return f"IF({cond},{bloco})"

    def criar_while(self, cond, bloco, linha):
        self._reg("criar_while", cond, bloco)
        return f"WHILE({cond},{bloco})"

    def criar_programa(self, cmds, linha):
        self._reg("criar_programa", cmds)
        return f"PROG{cmds}"


def _tokens(*pares):
    """Cria lista de Token a partir de pares (tipo, valor)."""
    return [Token(tipo, valor, i + 1) for i, (tipo, valor) in enumerate(pares)]


def _cabecalho():
    return [Token("LPAREN","(",1), Token("START","START",1), Token("RPAREN",")",1)]

def _rodape(linha=99):
    return [Token("LPAREN","(",linha), Token("END","END",linha), Token("RPAREN",")",linha)]

def _programa(*cmds):
    return _cabecalho() + list(cmds) + _rodape()


# ---------------------------------------------------------------------------
# Caminho feliz — programa mínimo
# ---------------------------------------------------------------------------

def test_programa_minimo_sem_comandos():
    tokens = _programa()
    b = BuilderStub()
    parsear(tokens, {}, b)
    nomes = [c[0] for c in b.chamadas]
    assert "criar_programa" in nomes

def test_programa_minimo_chama_criar_programa_com_lista_vazia():
    tokens = _programa()
    b = BuilderStub()
    parsear(tokens, {}, b)
    prog = next(c for c in b.chamadas if c[0] == "criar_programa")
    assert prog[1] == []


# ---------------------------------------------------------------------------
# Caminho feliz — expressões aritméticas
# ---------------------------------------------------------------------------

def test_expressao_inteiros_simples():
    inner = _tokens(
        ("LPAREN","("), ("NUM_INT","3"), ("NUM_INT","4"), ("OP_SOMA","+"), ("RPAREN",")"),
    )
    tokens = _cabecalho() + inner + _rodape()
    b = BuilderStub()
    parsear(tokens, {}, b)
    nomes = [c[0] for c in b.chamadas]
    assert "criar_expr" in nomes
    assert "criar_operando_num" in nomes
    assert "criar_operador" in nomes

def test_expressao_operador_correto():
    inner = _tokens(
        ("LPAREN","("), ("NUM_INT","10"), ("NUM_INT","2"), ("OP_MULT","*"), ("RPAREN",")"),
    )
    tokens = _cabecalho() + inner + _rodape()
    b = BuilderStub()
    parsear(tokens, {}, b)
    ops = [c for c in b.chamadas if c[0] == "criar_operador"]
    assert ops[0][1] == "*"

def test_expressao_real():
    inner = _tokens(
        ("LPAREN","("), ("NUM_REAL","9.0"), ("NUM_REAL","3.0"), ("OP_DIV_REAL","|"), ("RPAREN",")"),
    )
    tokens = _cabecalho() + inner + _rodape()
    b = BuilderStub()
    parsear(tokens, {}, b)
    nums = [c for c in b.chamadas if c[0] == "criar_operando_num"]
    assert any("9.0" in str(n) for n in nums)

def test_todos_operadores_aritmeticos():
    operadores = [
        ("OP_SOMA","+"), ("OP_SUB","-"), ("OP_MULT","*"),
        ("OP_DIV_INT","/"), ("OP_DIV_REAL","|"), ("OP_MOD","%"), ("OP_POT","^"),
    ]
    for tipo, simbolo in operadores:
        inner = _tokens(
            ("LPAREN","("), ("NUM_INT","5"), ("NUM_INT","2"), (tipo, simbolo), ("RPAREN",")"),
        )
        tokens = _cabecalho() + inner + _rodape()
        b = BuilderStub()
        parsear(tokens, {}, b)
        ops = [c for c in b.chamadas if c[0] == "criar_operador"]
        assert ops[0][1] == simbolo, f"Falhou para operador {simbolo}"

def test_todos_operadores_relacionais():
    operadores = [
        ("OP_MAIOR",">"), ("OP_MENOR","<"), ("OP_IGUAL","=="),
        ("OP_DIF","!="), ("OP_MAIOR_IGUAL",">="), ("OP_MENOR_IGUAL","<="),
    ]
    for tipo, simbolo in operadores:
        inner = _tokens(
            ("LPAREN","("), ("NUM_INT","1"), ("NUM_INT","0"), (tipo, simbolo), ("RPAREN",")"),
        )
        tokens = _cabecalho() + inner + _rodape()
        b = BuilderStub()
        parsear(tokens, {}, b)
        ops = [c for c in b.chamadas if c[0] == "criar_operador"]
        assert ops[0][1] == simbolo


# ---------------------------------------------------------------------------
# Caminho feliz — comandos especiais
# ---------------------------------------------------------------------------

def test_cmd_res():
    inner = _tokens(
        ("LPAREN","("), ("NUM_INT","1"), ("KEYWORD_RES","RES"), ("RPAREN",")"),
    )
    tokens = _cabecalho() + inner + _rodape()
    b = BuilderStub()
    parsear(tokens, {}, b)
    res = [c for c in b.chamadas if c[0] == "criar_cmd_res"]
    assert len(res) == 1 and res[0][1] == "1"

def test_cmd_mem_store():
    inner = _tokens(
        ("LPAREN","("), ("NUM_INT","10"), ("MEM","VALOR"), ("RPAREN",")"),
    )
    tokens = _cabecalho() + inner + _rodape()
    b = BuilderStub()
    parsear(tokens, {}, b)
    stores = [c for c in b.chamadas if c[0] == "criar_cmd_mem_store"]
    assert stores[0][1] == "NUM:10" and stores[0][2] == "VALOR"

def test_cmd_mem_load():
    inner = _tokens(
        ("LPAREN","("), ("MEM","VALOR"), ("RPAREN",")"),
    )
    tokens = _cabecalho() + inner + _rodape()
    b = BuilderStub()
    parsear(tokens, {}, b)
    loads = [c for c in b.chamadas if c[0] == "criar_cmd_mem_load"]
    assert loads[0][1] == "VALOR"


# ---------------------------------------------------------------------------
# Caminho feliz — estruturas de controle
# ---------------------------------------------------------------------------

def test_if_chama_criar_if():
    # ( (1 0 >) (LET ) IF )
    # outer ( consumed by _lista_comandos_globais
    # cond ( consumed by _conteudo_comando; 1 0 > by _expressao
    cond = [
        Token("LPAREN","(",2),
        Token("NUM_INT","1",2), Token("NUM_INT","0",2), Token("OP_MAIOR",">",2),
        Token("RPAREN",")",2),
    ]
    bloco = [
        Token("LPAREN","(",2), Token("KEYWORD_LET","LET",2), Token("RPAREN",")",2),
    ]
    controle = [Token("IF","IF",2), Token("RPAREN",")",2)]
    inner = [Token("LPAREN","(",2)] + cond + bloco + controle
    tokens = _cabecalho() + inner + _rodape()
    b = BuilderStub()
    parsear(tokens, {}, b)
    assert any(c[0] == "criar_if" for c in b.chamadas)

def test_while_chama_criar_while():
    # ( (1 1 ==) (LET ) WHILE )
    cond = [
        Token("LPAREN","(",2),
        Token("NUM_INT","1",2), Token("NUM_INT","1",2), Token("OP_IGUAL","==",2),
        Token("RPAREN",")",2),
    ]
    bloco = [
        Token("LPAREN","(",2), Token("KEYWORD_LET","LET",2), Token("RPAREN",")",2),
    ]
    controle = [Token("WHILE","WHILE",2), Token("RPAREN",")",2)]
    inner = [Token("LPAREN","(",2)] + cond + bloco + controle
    tokens = _cabecalho() + inner + _rodape()
    b = BuilderStub()
    parsear(tokens, {}, b)
    assert any(c[0] == "criar_while" for c in b.chamadas)


# ---------------------------------------------------------------------------
# Erros sintáticos — verificam linha e tipo
# ---------------------------------------------------------------------------

def test_erro_token_inesperado_apos_programa():
    tokens = _programa() + [Token("NUM_INT", "5", 50)]
    with pytest.raises(ErroSintatico) as exc:
        parsear(tokens, {}, BuilderStub())
    assert "linha 50" in str(exc.value)

def test_erro_falta_start():
    tokens = [Token("LPAREN","(",1), Token("END","END",1), Token("RPAREN",")",1)]
    with pytest.raises(ErroSintatico) as exc:
        parsear(tokens, {}, BuilderStub())
    assert "linha" in str(exc.value)

def test_erro_falta_rparen():
    tokens = [Token("LPAREN","(",1), Token("START","START",1)]
    with pytest.raises(ErroSintatico) as exc:
        parsear(tokens, {}, BuilderStub())
    assert "linha" in str(exc.value)

def test_erro_token_invalido_no_comando():
    inner = _tokens(("LPAREN","("), ("IF","IF"), ("RPAREN",")"))
    tokens = _cabecalho() + inner + _rodape()
    with pytest.raises(ErroSintatico) as exc:
        parsear(tokens, {}, BuilderStub())
    assert "linha" in str(exc.value)

def test_erro_fim_inesperado():
    tokens = [Token("LPAREN","(",1), Token("START","START",1)]
    with pytest.raises(ErroSintatico) as exc:
        parsear(tokens, {}, BuilderStub())
    assert "fim da entrada" in str(exc.value)
