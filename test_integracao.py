# Integrantes do grupo (ordem alfabética):
# Dani Heart Basso - @dani-heart
# Mariana Alves da Silva - @himarialves
#
# Nome do grupo no Canvas: RA2-18

"""Testes de integração: pipeline completo lexer → parser → árvore → assembly."""

import pytest
from lexer import lerTokens
from gramatica import construirTabelaLL1
from arvore import gerarArvore, No
from assembly import gerarAssembly
from parser import ErroSintatico


def _pipeline(caminho: str):
    tokens = lerTokens(caminho)
    tabela = construirTabelaLL1()
    arvore = gerarArvore(tokens, tabela)
    asm = gerarAssembly(arvore)
    return arvore, asm


# ---------------------------------------------------------------------------
# Caminho feliz — os três arquivos de teste obrigatórios
# ---------------------------------------------------------------------------

def test_pipeline_completo_teste1():
    arvore, asm = _pipeline("teste1.txt")
    assert isinstance(arvore, No)
    assert arvore.tipo == "PROGRAMA"
    assert ".text" in asm
    assert ".data" in asm
    assert "_start:" in asm

def test_pipeline_completo_teste2():
    arvore, asm = _pipeline("teste2.txt")
    assert arvore.tipo == "PROGRAMA"
    assert len(arvore.filhos) > 0

def test_pipeline_completo_teste3():
    arvore, asm = _pipeline("teste3.txt")
    assert arvore.tipo == "PROGRAMA"
    assert "_start:" in asm


# ---------------------------------------------------------------------------
# Caminho feliz — verificações de conteúdo do assembly
# ---------------------------------------------------------------------------

def test_assembly_tem_inicializacao_sp():
    _, asm = _pipeline("teste1.txt")
    assert "STACK_TOP" in asm

def test_assembly_tem_vfp_habilitado():
    _, asm = _pipeline("teste1.txt")
    assert "FPEXC" in asm

def test_assembly_tem_secao_data_com_res_hist():
    _, asm = _pipeline("teste1.txt")
    assert "RES_HIST" in asm
    assert "RES_IDX" in asm

def test_assembly_tem_variaveis_mem_em_data():
    _, asm = _pipeline("teste1.txt")
    assert "VALOR:" in asm or "CONT:" in asm

def test_assembly_tem_constante_float_como_double():
    _, asm = _pipeline("teste1.txt")
    assert ".double" in asm

def test_assembly_tem_if():
    _, asm = _pipeline("teste1.txt")
    assert "IF_FIM" in asm

def test_assembly_tem_while():
    _, asm = _pipeline("teste1.txt")
    assert "WHILE_LOOP" in asm
    assert "WHILE_FIM" in asm

def test_assembly_usa_vstr_para_salvar_resultado():
    _, asm = _pipeline("teste1.txt")
    assert "VSTR" in asm

def test_assembly_usa_vldr_para_carregar_float():
    _, asm = _pipeline("teste1.txt")
    assert "VLDR" in asm

def test_assembly_usa_f64():
    _, asm = _pipeline("teste1.txt")
    assert "F64" in asm or "D0" in asm

def test_assembly_termina_com_branch_infinito():
    _, asm = _pipeline("teste1.txt")
    assert "B _end" in asm


# ---------------------------------------------------------------------------
# Árvore sintática — estrutura de nós
# ---------------------------------------------------------------------------

def test_arvore_raiz_e_programa():
    arvore, _ = _pipeline("teste1.txt")
    assert arvore.tipo == "PROGRAMA"

def test_arvore_tem_filhos():
    arvore, _ = _pipeline("teste1.txt")
    assert len(arvore.filhos) > 0

def test_arvore_contem_no_expr():
    arvore, _ = _pipeline("teste1.txt")
    tipos = {f.tipo for f in arvore.filhos}
    assert "EXPR" in tipos

def test_arvore_contem_no_if():
    arvore, _ = _pipeline("teste1.txt")
    tipos = {f.tipo for f in arvore.filhos}
    assert "IF" in tipos

def test_arvore_contem_no_while():
    arvore, _ = _pipeline("teste1.txt")
    tipos = {f.tipo for f in arvore.filhos}
    assert "WHILE" in tipos

def test_arvore_expr_tem_tres_filhos():
    arvore, _ = _pipeline("teste1.txt")
    exprs = [f for f in arvore.filhos if f.tipo == "EXPR"]
    assert all(len(e.filhos) == 3 for e in exprs)

def test_arvore_contem_cmd_mem_store():
    arvore, _ = _pipeline("teste1.txt")
    tipos = {f.tipo for f in arvore.filhos}
    assert "CMD_MEM_STORE" in tipos

def test_arvore_contem_cmd_res():
    arvore, _ = _pipeline("teste1.txt")
    tipos = {f.tipo for f in arvore.filhos}
    assert "CMD_RES" in tipos


# ---------------------------------------------------------------------------
# Entradas inválidas
# ---------------------------------------------------------------------------

def test_erro_sintatico_propaga_corretamente():
    import tempfile, os
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8")
    f.write("(START)\n(3 +)\n(END)\n")
    f.close()
    try:
        tokens = lerTokens(f.name)
        tabela = construirTabelaLL1()
        with pytest.raises(ErroSintatico):
            gerarArvore(tokens, tabela)
    finally:
        os.unlink(f.name)
