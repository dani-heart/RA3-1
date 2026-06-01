# Gramática EBNF - Fase 3 (Analisador Semântico)

Este documento descreve a gramática livre de contexto adotada pela linguagem na Fase 3 do nosso compilador. A gramática foi modelada para ser analisada por um *Parser Top-Down* Preditivo Descendente Recursivo do tipo **LL(1)**.

## 1. Regras e Convenções (Requisitos da Fase 3)
Conforme exigido na **Seção 28.3.1** da documentação do projeto, a gramática adota o formato padrão de EBNF com a seguinte regra de nomenclatura obrigatória:
- **`não_terminais`**: Representados inteiramente com letras **minúsculas**.
- **`TERMINAIS`**: Representados inteiramente com letras **MAIÚSCULAS** (são os Tokens retornados pelo nosso Analisador Léxico).
- **`[VAZIO]`**: Representa uma produção vazia (ε), permitindo o escape de uma derivação opcional (usado em blocos aninhados).

> **Nota sobre Comentários:** Conforme a Seção 28.2.1, os comentários em bloco `*{ ... }*` não constam na gramática, visto que o nosso Analisador Léxico já os processa, transforma em quebras de linha e limpa a entrada antes que os tokens alcancem a análise sintática.

## 2. Produções da Gramática Fatorada à Esquerda

### Fluxo Global e Estrutura Principal
```ebnf
programa ::= LPAREN START RPAREN lista_comandos_globais

lista_comandos_globais ::= LPAREN conteudo_global

conteudo_global ::= END RPAREN
                  | conteudo_comando RPAREN lista_comandos_globais
```

### Comandos Básicos e Blocos
```ebnf
lista_comandos_bloco ::= LPAREN conteudo_comando RPAREN lista_comandos_bloco 
                       | [VAZIO]

conteudo_comando ::= NUM_INT acao_numero
                   | NUM_REAL acao_numero
                   | MEM
                   | LPAREN conteudo_par RPAREN acao_pos_par
```

### Ações e Resoluções Pós-Operandos
```ebnf
acao_numero ::= KEYWORD_RES
              | MEM
              | operando operador

conteudo_par ::= expressao

acao_pos_par ::= NUM_INT operador
               | NUM_REAL operador
               | LPAREN conteudo_pos_par_lparen

conteudo_pos_par_lparen ::= KEYWORD_LET lista_comandos_bloco RPAREN controle
                          | conteudo_operando RPAREN operador
```

### Estruturas de Controle e Expressões Matemáticas
```ebnf
controle ::= IF | WHILE
expressao ::= operando operando operador
operando ::= NUM_INT | NUM_REAL | LPAREN conteudo_operando RPAREN
conteudo_operando ::= MEM | expressao
operador ::= OP_SOMA | OP_SUB | OP_MULT | OP_DIV_INT | OP_DIV_REAL | OP_MOD | OP_POT | OP_MAIOR | OP_MENOR | OP_IGUAL | OP_DIF | OP_MAIOR_IGUAL | OP_MENOR_IGUAL
```