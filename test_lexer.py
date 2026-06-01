# Integrantes do grupo (ordem alfabética):
# Dani Heart Basso - @dani-heart
#
# Nome do grupo no Canvas: RA3-1

import pytest
from lexer import lerTokens, Token, _classificar_token
import tempfile, os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _arquivo_temp(conteudo: str) -> str:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8")
    f.write(conteudo)
    f.close()
    return f.name


# ---------------------------------------------------------------------------
# Caminho feliz — tokens individuais
# ---------------------------------------------------------------------------

def test_classificar_token_lparen():
    t = _classificar_token("(", 1)
    assert t.tipo == "LPAREN" and t.valor == "("

def test_classificar_token_rparen():
    t = _classificar_token(")", 1)
    assert t.tipo == "RPAREN" and t.valor == ")"

def test_classificar_token_start():
    t = _classificar_token("START", 1)
    assert t.tipo == "START"

def test_classificar_token_end():
    t = _classificar_token("END", 1)
    assert t.tipo == "END"

def test_classificar_token_num_int_positivo():
    t = _classificar_token("42", 1)
    assert t.tipo == "NUM_INT" and t.valor == "42"

def test_classificar_token_num_int_negativo():
    t = _classificar_token("-7", 1)
    assert t.tipo == "NUM_INT" and t.valor == "-7"

def test_classificar_token_num_real():
    t = _classificar_token("3.14", 1)
    assert t.tipo == "NUM_REAL" and t.valor == "3.14"

def test_classificar_token_num_real_negativo():
    t = _classificar_token("-1.5", 1)
    assert t.tipo == "NUM_REAL" and t.valor == "-1.5"

def test_classificar_token_mem_variavel():
    t = _classificar_token("VALOR", 1)
    assert t.tipo == "MEM" and t.valor == "VALOR"

def test_classificar_token_mem_variavel_uma_letra():
    t = _classificar_token("X", 1)
    assert t.tipo == "MEM"

def test_classificar_token_keyword_res():
    t = _classificar_token("RES", 1)
    assert t.tipo == "KEYWORD_RES"

def test_classificar_token_keyword_let():
    t = _classificar_token("LET", 1)
    assert t.tipo == "KEYWORD_LET"

def test_classificar_token_if():
    t = _classificar_token("IF", 1)
    assert t.tipo == "IF"

def test_classificar_token_while():
    t = _classificar_token("WHILE", 1)
    assert t.tipo == "WHILE"

def test_classificar_token_operadores_aritmeticos():
    casos = [("+", "OP_SOMA"), ("-", "OP_SUB"), ("*", "OP_MULT"),
             ("/", "OP_DIV_INT"), ("|", "OP_DIV_REAL"), ("%", "OP_MOD"), ("^", "OP_POT")]
    for valor, tipo_esperado in casos:
        t = _classificar_token(valor, 1)
        assert t.tipo == tipo_esperado, f"Falhou para operador '{valor}'"

def test_classificar_token_operadores_relacionais():
    casos = [("<", "OP_MENOR"), (">", "OP_MAIOR"), ("==", "OP_IGUAL"),
             ("!=", "OP_DIF"), (">=", "OP_MAIOR_IGUAL"), ("<=", "OP_MENOR_IGUAL")]
    for valor, tipo_esperado in casos:
        t = _classificar_token(valor, 1)
        assert t.tipo == tipo_esperado, f"Falhou para operador '{valor}'"


# ---------------------------------------------------------------------------
# Caminho feliz — lerTokens com arquivo
# ---------------------------------------------------------------------------

def test_ler_tokens_programa_minimo():
    caminho = _arquivo_temp("(START)\n(END)\n")
    try:
        tokens = lerTokens(caminho)
        tipos = [t.tipo for t in tokens]
        assert tipos == ["LPAREN", "START", "RPAREN", "LPAREN", "END", "RPAREN"]
    finally:
        os.unlink(caminho)

def test_ler_tokens_expressao_simples():
    caminho = _arquivo_temp("(START)\n(3 4 +)\n(END)\n")
    try:
        tokens = lerTokens(caminho)
        tipos = [t.tipo for t in tokens]
        assert "NUM_INT" in tipos
        assert "OP_SOMA" in tipos
    finally:
        os.unlink(caminho)

def test_ler_tokens_numero_real():
    caminho = _arquivo_temp("(START)\n(9.0 3.0 |)\n(END)\n")
    try:
        tokens = lerTokens(caminho)
        reais = [t for t in tokens if t.tipo == "NUM_REAL"]
        assert len(reais) == 2
        assert reais[0].valor == "9.0"
    finally:
        os.unlink(caminho)

def test_ler_tokens_variavel_mem():
    caminho = _arquivo_temp("(START)\n(10 VALOR)\n(VALOR)\n(END)\n")
    try:
        tokens = lerTokens(caminho)
        mems = [t for t in tokens if t.tipo == "MEM"]
        assert all(t.valor == "VALOR" for t in mems)
    finally:
        os.unlink(caminho)

def test_ler_tokens_if():
    caminho = _arquivo_temp("(START)\n( ((1) 0 >) (LET (1 X) ) IF )\n(END)\n")
    try:
        tokens = lerTokens(caminho)
        tipos = [t.tipo for t in tokens]
        assert "IF" in tipos
        assert "KEYWORD_LET" in tipos
    finally:
        os.unlink(caminho)

def test_ler_tokens_while():
    caminho = _arquivo_temp("(START)\n( ((1) 1 ==) (LET (0 X) ) WHILE )\n(END)\n")
    try:
        tokens = lerTokens(caminho)
        tipos = [t.tipo for t in tokens]
        assert "WHILE" in tipos
    finally:
        os.unlink(caminho)

def test_ler_tokens_numero_de_linha_correto():
    caminho = _arquivo_temp("(START)\n(3 4 +)\n(END)\n")
    try:
        tokens = lerTokens(caminho)
        start = next(t for t in tokens if t.tipo == "START")
        assert start.linha == 1
        soma = next(t for t in tokens if t.tipo == "OP_SOMA")
        assert soma.linha == 2
    finally:
        os.unlink(caminho)

def test_ler_tokens_linhas_vazias_ignoradas():
    caminho = _arquivo_temp("(START)\n\n\n(END)\n")
    try:
        tokens = lerTokens(caminho)
        assert len(tokens) == 6
    finally:
        os.unlink(caminho)

def test_ler_tokens_teste1():
    tokens = lerTokens(os.path.join(BASE_DIR, "teste1.txt"))
    tipos = [t.tipo for t in tokens]
    assert "START" in tipos
    assert "END" in tipos
    assert "NUM_REAL" in tipos
    assert "MEM" in tipos
    assert "IF" in tipos
    assert "WHILE" in tipos

def test_ler_tokens_teste2():
    tokens = lerTokens(os.path.join(BASE_DIR, "teste2.txt"))
    tipos = [t.tipo for t in tokens]
    assert "START" in tipos and "END" in tipos

def test_ler_tokens_teste3():
    tokens = lerTokens(os.path.join(BASE_DIR, "teste3.txt"))
    tipos = [t.tipo for t in tokens]
    assert "START" in tipos and "END" in tipos


# ---------------------------------------------------------------------------
# Entradas inválidas
# ---------------------------------------------------------------------------

def test_classificar_token_erro_lexico_arroba():
    with pytest.raises(ValueError, match="Erro léxico"):
        _classificar_token("@", 5)

def test_classificar_token_erro_lexico_minuscula():
    with pytest.raises(ValueError, match="Erro léxico"):
        _classificar_token("var", 3)

def test_classificar_token_erro_lexico_misto():
    with pytest.raises(ValueError, match="Erro léxico"):
        _classificar_token("Var1", 2)

def test_ler_tokens_arquivo_nao_encontrado():
    with pytest.raises(FileNotFoundError):
        lerTokens("nao_existe.txt")

def test_ler_tokens_erro_lexico_no_arquivo():
    caminho = _arquivo_temp("(START)\n(@ 3 +)\n(END)\n")
    try:
        with pytest.raises(ValueError, match="Erro léxico"):
            lerTokens(caminho)
    finally:
        os.unlink(caminho)
