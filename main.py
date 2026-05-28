# Integrantes do grupo (ordem alfabética):
# Dani Heart Basso - @dani-heart
#
# Nome do grupo no Canvas: RA3-1

import sys
import os

from gramatica import construirTabelaLL1
from parser import ErroSintatico
from arvore import gerarArvore, imprimir_arvore, salvar_arvore_json
from assembly import gerarAssembly
from lexer import lerTokens
from semantico import AnalisadorSemantico, salvar_tabela_json


def main() -> None:
    #Pipeline de trabalho: tokens -> parse ->  árvore -> assembly."""
    if len(sys.argv) < 2:
        print("Uso: python main.py <arquivo.txt>")
        sys.exit(1)

    caminho = sys.argv[1]
    if not os.path.isfile(caminho):
        print(f"Erro: arquivo '{caminho}' não encontrado.")
        sys.exit(1)

    print(f"[1/4] Lendo tokens de '{caminho}'...")
    tokens = lerTokens(caminho)
    print(f"      {len(tokens)} token(s) carregados.")

    base = os.path.splitext(os.path.basename(caminho))[0]
    caminho_saida_asm = f"output_{base}.s"
    caminho_saida_json = f"arvore_{base}.json"
    caminho_saida_tabela = f"tabela_simbolos_{base}.json"

    print("[2/4] Construindo tabela LL(1)...")
    tabela = construirTabelaLL1()

    print("[3/4] Analisando sintaticamente...")
    try:
        arvore = gerarArvore(tokens, tabela)
    except ErroSintatico as e:
        print(f"\n{e}")
        sys.exit(1)

    print("Árvore sintática construída.")
    print()

    print("[3.5/4] Analisando semanticamente...")
    analisador_semantico = AnalisadorSemantico(arvore)
    tabela_simbolos, erros_semanticos = analisador_semantico.analisar()

    if erros_semanticos:
        print("\n*                   Erros Semânticos                   *")
        for erro in erros_semanticos:
            print(f" -> {erro}")
        print("********************************************************\n")
        print("Aviso: Geração de Assembly interrompida devido a erros semânticos.")
        sys.exit(1)

    print("Análise semântica concluída sem erros.")
    print()

    print("*                   Árvore Sintática                   *")
    imprimir_arvore(arvore)
    print()

    salvar_arvore_json(arvore, caminho_saida_json)
    salvar_tabela_json(tabela_simbolos, caminho_saida_tabela)

    print("[4/4] Gerando Assembly ARMv7...")
    codigo_asm = gerarAssembly(arvore)

    with open(caminho_saida_asm, "w", encoding="utf-8") as f:
        f.write(codigo_asm)

    print(f"Assembly salvo em: {caminho_saida_asm}")
    print()
    print("*                   *Assembly Gerado*                   *")
    print(codigo_asm)
    print("*                   *Fim*                   *")


if __name__ == "__main__":
    main()
