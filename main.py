# Integrantes do grupo (ordem alfabética):
# Dani Heart Basso - @dani-heart
# Mariana Alves da Silva - @himarialves
#
# Nome do grupo no Canvas: RA2-18

import sys
import os

from gramatica import construirTabelaLL1
from parser import ErroSintatico
from arvore import gerarArvore, imprimir_arvore, salvar_arvore_json
from assembly import gerarAssembly
from lexer import lerTokens


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
    print("*                   Árvore Sintática                   *")
    imprimir_arvore(arvore)
    print()

    salvar_arvore_json(arvore, caminho_saida_json)

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
