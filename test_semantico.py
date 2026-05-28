# Integrantes do grupo (ordem alfabética):
# Dani Heart Basso - @dani-heart
#
# Nome do grupo no Canvas: RA3-1

"""Testes unitários e de integração para a Fase 3 - Analisador Semântico."""

import pytest
import tempfile
import os

from lexer import lerTokens
from gramatica import construirTabelaLL1
from arvore import gerarArvore
from semantico import AnalisadorSemantico
from parser import ErroSintatico

def _analisar_codigo(codigo: str):
    """Helper que roda o pipeline até a análise semântica e retorna a tabela e erros."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8")
    f.write(codigo)
    f.close()
    try:
        tokens = lerTokens(f.name)
        tabela = construirTabelaLL1()
        arvore = gerarArvore(tokens, tabela)
        analisador = AnalisadorSemantico(arvore)
        tabela_simbolos, erros = analisador.analisar()
        return tabela_simbolos, erros
    finally:
        os.unlink(f.name)

# ===========================================================================
# Nível 1: Validação Base (Regressão Léxica e Sintática)
# ===========================================================================

def test_t1_1_ignorar_comentario_linha_unica():
    codigo = "(START)\n*{ comentario inofensivo }*\n(10 VAR)\n(END)\n"
    tabela, erros = _analisar_codigo(codigo)
    assert len(erros) == 0
    assert "VAR" in tabela.simbolos

def test_t1_2_comentario_multilinha_preserva_linhas():
    # Linha 1: (START)
    # Linha 2 a 5: Comentário ocupando múltiplas quebras de linha
    # Linha 6: (3 +) -> O erro sintático deve apontar EXATAMENTE para a linha 6.
    codigo = "(START)\n*{\nlinha oculta 1\nlinha oculta 2\n}*\n(3 +)\n(END)\n"
    with pytest.raises(ErroSintatico) as exc_info:
        _analisar_codigo(codigo)
    assert "linha 6" in str(exc_info.value)

def test_t1_3_capturar_erro_lexico():
    codigo = "(START)\n(10 X)\n(&)\n(END)\n"
    with pytest.raises(ValueError, match="Erro léxico na linha 3"):
        _analisar_codigo(codigo)

def test_t1_4_capturar_erro_sintatico():
    codigo = "(START)\n(3 +)\n(END)\n"
    with pytest.raises(ErroSintatico, match="Erro sintático na linha 2"):
        _analisar_codigo(codigo)

# ===========================================================================
# Nível 2: Tabela de Símbolos e Escopo (Variáveis)
# ===========================================================================

def test_t2_1_declarar_e_usar_variavel():
    codigo = "(START)\n(10 X)\n(X)\n(END)\n"
    tabela, erros = _analisar_codigo(codigo)
    assert len(erros) == 0, f"Erros inesperados: {erros}"
    assert "X" in tabela.simbolos
    assert tabela.simbolos["X"].tipo_inferido == "int"
    assert len(tabela.simbolos["X"].linhas_uso) == 1

def test_t2_2_reatribuir_mesmo_tipo():
    codigo = "(START)\n(10.5 X)\n(X)\n(20.0 X)\n(END)\n"
    tabela, erros = _analisar_codigo(codigo)
    assert len(erros) == 0, f"Erros inesperados: {erros}"
    assert tabela.simbolos["X"].tipo_inferido == "double"

def test_t2_3_erro_uso_antes_de_declaracao():
    codigo = "(START)\n(Y)\n(10 Y)\n(END)\n"
    tabela, erros = _analisar_codigo(codigo)
    assert len(erros) == 1
    assert "utilizada antes de ser definida" in erros[0]
    assert "linha 2" in erros[0]

def test_t2_4_erro_reatribuicao_int_para_double():
    codigo = "(START)\n(10 Z)\n(5.5 Z)\n(END)\n"
    tabela, erros = _analisar_codigo(codigo)
    assert len(erros) == 1
    assert "não pode receber o tipo 'double'" in erros[0]
    assert "linha 3" in erros[0]

def test_t2_5_erro_reatribuicao_double_para_int():
    codigo = "(START)\n(3.14 W)\n(3 W)\n(END)\n"
    tabela, erros = _analisar_codigo(codigo)
    assert len(erros) == 1
    assert "não pode receber o tipo 'int'" in erros[0]
    assert "linha 3" in erros[0]

# ===========================================================================
# Nível 3: Inferência e Compatibilidade Básica (Operadores)
# ===========================================================================

def test_t3_1_aritmetica_pura_int():
    codigo = "(START)\n(10 2 +)\n(10 2 -)\n(10 2 *)\n(10 2 ^)\n(END)\n"
    tabela, erros = _analisar_codigo(codigo)
    assert len(erros) == 0, f"Erros inesperados: {erros}"

def test_t3_2_aritmetica_pura_double():
    codigo = "(START)\n(10.5 2.0 +)\n(10.5 2.0 -)\n(10.5 2.0 *)\n(10.5 2.0 ^)\n(END)\n"
    tabela, erros = _analisar_codigo(codigo)
    assert len(erros) == 0, f"Erros inesperados: {erros}"

def test_t3_3_erro_mistura_tipos_aritmetica():
    codigo = "(START)\n(10 2.5 +)\n(END)\n"
    tabela, erros = _analisar_codigo(codigo)
    assert len(erros) == 1
    assert "incompatível entre 'int' e 'double'" in erros[0]
    assert "linha 2" in erros[0]

def test_t3_4_divisao_inteira_e_resto_com_int():
    codigo = "(START)\n(10 3 /)\n(10 3 %)\n(END)\n"
    tabela, erros = _analisar_codigo(codigo)
    assert len(erros) == 0, f"Erros inesperados: {erros}"

def test_t3_5_erro_divisao_inteira_e_resto_com_double():
    codigo = "(START)\n(10.0 3.0 /)\n(END)\n"
    tabela, erros = _analisar_codigo(codigo)
    assert len(erros) == 1
    assert "exige operandos 'int'" in erros[0]
    assert "linha 2" in erros[0]

def test_t3_6_divisao_real_com_double():
    codigo = "(START)\n(10.0 3.0 |)\n(END)\n"
    tabela, erros = _analisar_codigo(codigo)
    assert len(erros) == 0, f"Erros inesperados: {erros}"

def test_t3_7_erro_divisao_real_com_int():
    codigo = "(START)\n(10 3 |)\n(END)\n"
    tabela, erros = _analisar_codigo(codigo)
    assert len(erros) == 1
    assert "exige operandos 'double'" in erros[0]
    assert "linha 2" in erros[0]

# ===========================================================================
# Nível 4: Operadores Relacionais e Lógicos
# ===========================================================================

def test_t4_1_comparacao_int_valida():
    codigo = "(START)\n(10 5 >)\n(10 5 <)\n(10 5 ==)\n(10 5 !=)\n(10 5 >=)\n(10 5 <=)\n(END)\n"
    tabela, erros = _analisar_codigo(codigo)
    assert len(erros) == 0, f"Erros inesperados: {erros}"

def test_t4_2_comparacao_double_valida():
    codigo = "(START)\n(10.5 5.5 >)\n(10.5 5.5 <)\n(10.5 5.5 ==)\n(10.5 5.5 !=)\n(10.5 5.5 >=)\n(10.5 5.5 <=)\n(END)\n"
    tabela, erros = _analisar_codigo(codigo)
    assert len(erros) == 0, f"Erros inesperados: {erros}"

def test_t4_3_erro_comparacao_tipos_diferentes():
    codigo = "(START)\n(10 5.5 >)\n(END)\n"
    tabela, erros = _analisar_codigo(codigo)
    assert len(erros) == 1
    assert "Comparação '>' inválida entre 'int' e 'double'" in erros[0]
    assert "linha 2" in erros[0]

def test_t4_4_erro_aritmetica_com_bool():
    # Tenta somar o resultado de uma comparação (bool) com um inteiro (int)
    # A árvore disso é: ( (10 5 >) 2 + )
    codigo = "(START)\n((10 5 >) 2 +)\n(END)\n"
    tabela, erros = _analisar_codigo(codigo)
    assert len(erros) == 1
    # O operando esquerdo da soma será 'bool' e o direito será 'int'
    assert "incompatível entre 'bool' e 'int'" in erros[0]
    assert "linha 2" in erros[0]

# ===========================================================================
# Nível 5: Estruturas de Controle e Comandos Especiais
# ===========================================================================

def test_t5_1_if_while_com_bool():
    codigo = "(START)\n( (10 5 >) (LET (1 X) ) IF )\n( (10 5 <) (LET (2 Y) ) WHILE )\n(END)\n"
    tabela, erros = _analisar_codigo(codigo)
    assert len(erros) == 0, f"Erros inesperados: {erros}"

def test_t5_2_erro_if_com_int():
    # A condição (1 1 +) retorna 'int', o IF deve rejeitar.
    codigo = "(START)\n( (1 1 +) (LET (1 X) ) IF )\n(END)\n"
    tabela, erros = _analisar_codigo(codigo)
    assert len(erros) == 1
    assert "exige um tipo 'bool', mas recebeu 'int'" in erros[0]
    assert "linha 2" in erros[0]

def test_t5_3_erro_while_com_double():
    # A condição (1.5 2.5 +) retorna 'double', o WHILE deve rejeitar.
    codigo = "(START)\n( (1.5 2.5 +) (LET (1 X) ) WHILE )\n(END)\n"
    tabela, erros = _analisar_codigo(codigo)
    assert len(erros) == 1
    assert "exige um tipo 'bool', mas recebeu 'double'" in erros[0]
    assert "linha 2" in erros[0]

def test_t5_4_res_valido():
    codigo = "(START)\n(0 RES)\n(1 RES)\n(5 RES)\n(END)\n"
    tabela, erros = _analisar_codigo(codigo)
    assert len(erros) == 0, f"Erros inesperados: {erros}"

def test_t5_5_erro_res_com_double():
    codigo = "(START)\n(2.5 RES)\n(END)\n"
    tabela, erros = _analisar_codigo(codigo)
    assert len(erros) == 1
    assert "O comando 'RES' exige um argumento 'int'" in erros[0]
    assert "linha 2" in erros[0]

def test_t5_6_erro_res_negativo():
    codigo = "(START)\n(-1 RES)\n(END)\n"
    tabela, erros = _analisar_codigo(codigo)
    assert len(erros) == 1
    assert "exige um valor não negativo" in erros[0]
    assert "linha 2" in erros[0]

# ===========================================================================
# Nível 6: "The Deep Web" (Aninhamento e Propagação)
# ===========================================================================

def test_t6_1_aninhamento_profundo_valido():
    codigo = "(START)\n( ((3 4 +) 2 *) ((10 5 /) 1 -) == )\n(END)\n"
    tabela, erros = _analisar_codigo(codigo)
    assert len(erros) == 0, f"Erros inesperados: {erros}"

def test_t6_2_erro_aninhamento_profundo():
    # A subexpressão ((10.0 5.0 |) 1 -) tenta subtrair int de double
    codigo = "(START)\n( ((3 4 +) 2 *) ((10.0 5.0 |) 1 -) == )\n(END)\n"
    tabela, erros = _analisar_codigo(codigo)
    assert len(erros) >= 1
    assert any("incompatível entre 'double' e 'int'" in erro for erro in erros)

def test_t6_3_erros_multiplos_sem_panico():
    # 1. Reatribuição inválida: (10 X) depois (10.0 X)
    # 2. Operação incompatível: 10 que é int somado a (Y) que é double
    # 3. Uso antes da declaração: (Z)
    codigo = "(START)\n(10 X)\n(10.0 X)\n(3.5 Y)\n( 10 (Y) + )\n(Z)\n(END)\n"
    tabela, erros = _analisar_codigo(codigo)
    assert len(erros) == 3
    assert any("não pode receber o tipo 'double'" in e for e in erros)
    assert any("incompatível entre 'int' e 'double'" in e for e in erros)
    assert any("utilizada antes de ser definida" in e for e in erros)