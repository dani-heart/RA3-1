# Integrantes do grupo (ordem alfabética):
# Dani Heart Basso - @dani-heart
# Mariana Alves da Silva - @himarialves
#
# Nome do grupo no Canvas: RA2-18

## CONSTRUIR GRAMÁTICA
# Essa função retorna a gramática livre de contexto, como um dicionário
# Chaves são Não-Terminais
# Valores são listas de produção (As regrinhas)
# O projeto é para uma gramática LL(1), no caso, só olha 1 à frente
# Usa fatoração à esquerda em não terminais, em (LPAREN), já que muitos caminhos poderiam começar com (
# [VAZIO] representa ε e indica uma produção vazia, para permitir que blocos sejam opcionais
def construirGramatica(): 
   
    gramatica = {
        # O programa global exige (START) no início. 
        # Em seguida, chama a lista de comandos que processará até achar o (END)
        "<Programa>": [
            ["LPAREN", "START", "RPAREN", "<ListaComandosGlobais>"]
        ],

        # Fatoração à esquerda, para evitar conflitos quando lê (
        # Todas as linhas de comando começam consumindo um parentesis e jogando a decisão pra frente
        "<ListaComandosGlobais>": [
            ["LPAREN", "<ConteudoGlobal>"]
        ],

        # Aqui "Decidimos" se é o fim do programa (END) ou um comando executável
        "<ConteudoGlobal>": [
            ["END", "RPAREN"],
            ["<ConteudoComando>", "RPAREN", "<ListaComandosGlobais>"]
        ],

        # Utilizado para comandos como IF/WHILE
        # Pode estar VAZIO no fim do bloco
        "<ListaComandosBloco>": [
            ["LPAREN", "<ConteudoComando>", "RPAREN", "<ListaComandosBloco>"],
            ["[VAZIO]"]
        ],
 
        # Esse bloco é complicado:
        # NUM_INT ou NUM_REAL pode ser parte de: Operação, Memória, ou Resultado Histórico
        # MEM sem ação significa que está puxando o valor
        # LPAREN indica uma expressão com parentesis ou estrutura de controle
        "<ConteudoComando>": [
            ["NUM_INT", "<AcaoNumero>"], # Numero pode ser uma conta, guardar valor através de MEM ou histórico (KEYWORD_RES)
            ["NUM_REAL", "<AcaoNumero>"], # Mesma coisa para REAL
            ["MEM"],
            ["LPAREN", "<ConteudoPar>", "RPAREN", "<AcaoPosPar>"] # Isso é para parentesis dentro de parentesis.  
        ],

        # Define a ação tomada depois de um token numerico ou outra expressão
        # KEYWORD_RES: Resultado do histórico
        # MEM: Guarda o valor na variável com esse ID
        # <Operando> <Operador>: Expressão matemática
        "<AcaoNumero>": [
            ["KEYWORD_RES"],
            ["MEM"],
            ["<Operando>", "<Operador>"]
        ],

        # PASSTHROUGH: Redireciona diretamente para <Expressao>.
        # Mantido na gramática para deixar a arquitetura aberta para futuras 
        # expansões do que pode existir dentro de blocos isolados de parênteses.
        "<ConteudoPar>": [
            ["<Expressao>"]
        ],

        # Determina o que acontece depois de fechar um parentesis
        # Pode ser desde um número para uma operação, ou um LPAREN (Que indica uma estrutura mais complexa)
        "<AcaoPosPar>": [
            ["NUM_INT", "<Operador>"], # Pode ser um inteiro
            ["NUM_REAL", "<Operador>"], # Um real
            ["LPAREN", "<ConteudoPosParLparen>"] # Esse operando abre um parentesis, então pode ser uma conta ou IF/WHILE
        ],
 
        # Só sabemos se é uma conta ao ler o primeiro token dentro do parentesis, então usamos KEYWORD_LET
        # Se KEYWORD_LET é encontrado, é um bloco de controle (IF/WHILE)
        # Se não, é um operando matemático
        "<ConteudoPosParLparen>": [
            ["KEYWORD_LET", "<ListaComandosBloco>", "RPAREN", "<Controle>"], # Achou KEYWORD_LET? Controle
            ["<ConteudoOperando>", "RPAREN", "<Operador>"] 
        ],

        ## A partir daqui temos operações bem mais simples

        # Representa as palavras possíveis de controle, usadas acima
        "<Controle>": [
            ["IF"],
            ["WHILE"]
        ],

        # Literalmente a definição de RPN: Expressão, Expressão, Operando
        "<Expressao>": [
            ["<Operando>", "<Operando>", "<Operador>"]
        ],

        # Define o que podem ser os tais operandos
        "<Operando>": [
            ["NUM_INT"],
            ["NUM_REAL"],
            ["LPAREN", "<ConteudoOperando>", "RPAREN"]
        ],

        # Define o que pode estar dentro do parentesis: MEM ou outra expressão
        "<ConteudoOperando>": [
            ["MEM"],
            ["<Expressao>"]
        ],

        # Todos os operadores suportados. Mais detalhes em Anotações.md e EBNF.md
        "<Operador>": [
            ["OP_SOMA"], ["OP_SUB"], ["OP_MULT"], ["OP_DIV_INT"], ["OP_DIV_REAL"], 
            ["OP_MOD"], ["OP_POT"], ["OP_MAIOR"], ["OP_MENOR"], ["OP_IGUAL"], 
            ["OP_DIF"], ["OP_MAIOR_IGUAL"], ["OP_MENOR_IGUAL"]
        ]
    }
    return gramatica

## CALCULAR FIRST
# Retorna os firsts
# Um first representa os conjuntos de tokens terminais que podem ser derivados de um não-terminal

#COMO FUNCIONA UM FIRST SET
#-> Para um Terminal (t): FIRST(t) = {t}
#-> Para um Não Terminal A: (Complexo)
#---> Se A -> [VAZIO] é uma produção, então [VAZIO] está em FIRST(A)
#---> Se A -> X1 X2 X3... é uma pdrodução
#-----> Adicionar todos os terminais de FIRST (X1) a FIRST(A) (Tirando o [VAZIO])
#-----> Se VAZIO está em FIRST (X1), então adicione todos os terminais de FIRST (X2) à FIRST (A) (Novamente, tirando [VAZIO])
#-----> Continuar o processo enquanto tiver [VAZIO] em não-First

#Nessa implementação os conjuntos FIRST são pré calculados e codificados diretamente
#Em um parser automático esses conjuntos seriam gerados a partir das regras de construirGramatica()
def calcularFirst():

    first = {
        "<Programa>": {"LPAREN"},
        "<ListaComandosGlobais>": {"LPAREN"},
        "<ConteudoGlobal>": {"END", "NUM_INT", "NUM_REAL", "MEM", "LPAREN"},
        "<ListaComandosBloco>": {"LPAREN", "[VAZIO]"},
        "<ConteudoComando>": {"NUM_INT", "NUM_REAL", "MEM", "LPAREN"},
        "<AcaoNumero>": {"KEYWORD_RES", "MEM", "NUM_INT", "NUM_REAL", "LPAREN"},
        "<ConteudoPar>": {"NUM_INT", "NUM_REAL", "LPAREN"},
        "<AcaoPosPar>": {"NUM_INT", "NUM_REAL", "LPAREN"},
        "<ConteudoPosParLparen>": {"KEYWORD_LET", "MEM", "NUM_INT", "NUM_REAL", "LPAREN"},
        "<Controle>": {"IF", "WHILE"},
        "<Expressao>": {"NUM_INT", "NUM_REAL", "LPAREN"},
        "<Operando>": {"NUM_INT", "NUM_REAL", "LPAREN"},
        "<ConteudoOperando>": {"MEM", "NUM_INT", "NUM_REAL", "LPAREN"},
        "<Operador>": {"OP_SOMA", "OP_SUB", "OP_MULT", "OP_DIV_INT", "OP_DIV_REAL", 
                       "OP_MOD", "OP_POT", "OP_MAIOR", "OP_MENOR", "OP_IGUAL", 
                       "OP_DIF", "OP_MAIOR_IGUAL", "OP_MENOR_IGUAL"}
    }
    return first

## CALCULAR FOLLOW
# Retorna os conjuntos Follow

#Como funciona Follow:
#   1) Para o simbolo inícial S: Adiciona $ a FOLLOW(S)
#   2) Para cada produção A -> \alpha B \beta onde B não é terminal
#       Adicione todos os terminais de FIRST(\beta) à Follow(B) (Tirando [VAZIO])
#       Se tiver [VAZIO] em FIRST(\beta), então adicione todos os terminais de FOLLOW(A) e FOLLOW(B)
#   3) Para cada produção A -> \alphaB : (B não sendo terminal)
#       Adicione todos os terminais de FOLLOW(A) a FOLLOW(B)

#Repetir passos 2 e 3 até que nenhum terminal novo possa ser adicionado a nenhum FOLLOW

#Assim como em calcularFirst(), os conjuntos FOLLOW são pré calculados e codificados
#Especialmente importantes para construir a tabela LL(1)
def calcularFollow():

    follow = {
        "<Programa>": {"$"},
        "<ListaComandosGlobais>": {"$"},
        "<ConteudoGlobal>": {"$"},
        "<ListaComandosBloco>": {"RPAREN"},
        "<ConteudoComando>": {"RPAREN"},
        "<AcaoNumero>": {"RPAREN"},
        "<ConteudoPar>": {"RPAREN"},
        "<AcaoPosPar>": {"RPAREN"},
        "<ConteudoPosParLparen>": {"RPAREN"},
        "<Controle>": {"RPAREN"},
        "<Expressao>": {"RPAREN"},
        "<Operando>": {"NUM_INT", "NUM_REAL", "LPAREN", "OP_SOMA", "OP_SUB", "OP_MULT", "OP_DIV_INT", "OP_DIV_REAL", "OP_MOD", "OP_POT", "OP_MAIOR", "OP_MENOR", "OP_IGUAL", "OP_DIF", "OP_MAIOR_IGUAL", "OP_MENOR_IGUAL"},
        "<ConteudoOperando>": {"RPAREN"},
        "<Operador>": {"RPAREN"}
    }
    return follow

## CONSTRUIR TABELA LL1
# Uma gramática é LL(1) se cada célula da tabela M[A,a] tiver no máximo uma produção
def construirTabelaLL1():

    tabela = {
        "<Programa>": {
            "LPAREN": ["LPAREN", "START", "RPAREN", "<ListaComandosGlobais>"]
        },
        "<ListaComandosGlobais>": {
            "LPAREN": ["LPAREN", "<ConteudoGlobal>"]
        },
        "<ConteudoGlobal>": {
            "END": ["END", "RPAREN"],
            "NUM_INT": ["<ConteudoComando>", "RPAREN", "<ListaComandosGlobais>"],
            "NUM_REAL": ["<ConteudoComando>", "RPAREN", "<ListaComandosGlobais>"],
            "MEM": ["<ConteudoComando>", "RPAREN", "<ListaComandosGlobais>"],
            "LPAREN": ["<ConteudoComando>", "RPAREN", "<ListaComandosGlobais>"]
        },
        "<ListaComandosBloco>": {
            "LPAREN": ["LPAREN", "<ConteudoComando>", "RPAREN", "<ListaComandosBloco>"],
            "RPAREN": ["[VAZIO]"]
        },
        "<ConteudoComando>": {
            "NUM_INT": ["NUM_INT", "<AcaoNumero>"],
            "NUM_REAL": ["NUM_REAL", "<AcaoNumero>"],
            "MEM": ["MEM"],
            "LPAREN": ["LPAREN", "<ConteudoPar>", "RPAREN", "<AcaoPosPar>"]
        },
        "<AcaoNumero>": {
            "KEYWORD_RES": ["KEYWORD_RES"],
            "MEM": ["MEM"],
            "NUM_INT": ["<Operando>", "<Operador>"],
            "NUM_REAL": ["<Operando>", "<Operador>"],
            "LPAREN": ["<Operando>", "<Operador>"]
        },
        "<ConteudoPar>": {
            "NUM_INT": ["<Expressao>"],
            "NUM_REAL": ["<Expressao>"],
            "LPAREN": ["<Expressao>"]
        },
        "<AcaoPosPar>": {
            "NUM_INT": ["NUM_INT", "<Operador>"],
            "NUM_REAL": ["NUM_REAL", "<Operador>"],
            "LPAREN": ["LPAREN", "<ConteudoPosParLparen>"]
        },
        "<ConteudoPosParLparen>": {
            "KEYWORD_LET": ["KEYWORD_LET", "<ListaComandosBloco>", "RPAREN", "<Controle>"],
            "MEM": ["<ConteudoOperando>", "RPAREN", "<Operador>"],
            "NUM_INT": ["<ConteudoOperando>", "RPAREN", "<Operador>"],
            "NUM_REAL": ["<ConteudoOperando>", "RPAREN", "<Operador>"],
            "LPAREN": ["<ConteudoOperando>", "RPAREN", "<Operador>"]
        },
        "<Controle>": {
            "IF": ["IF"],
            "WHILE": ["WHILE"]
        },
        "<Expressao>": {
            "NUM_INT": ["<Operando>", "<Operando>", "<Operador>"],
            "NUM_REAL": ["<Operando>", "<Operando>", "<Operador>"],
            "LPAREN": ["<Operando>", "<Operando>", "<Operador>"]
        },
        "<Operando>": {
            "NUM_INT": ["NUM_INT"],
            "NUM_REAL": ["NUM_REAL"],
            "LPAREN": ["LPAREN", "<ConteudoOperando>", "RPAREN"]
        },
        "<ConteudoOperando>": {
            "MEM": ["MEM"],
            "NUM_INT": ["<Expressao>"],
            "NUM_REAL": ["<Expressao>"],
            "LPAREN": ["<Expressao>"]
        },
        "<Operador>": {
            "OP_SOMA": ["OP_SOMA"], "OP_SUB": ["OP_SUB"], "OP_MULT": ["OP_MULT"], "OP_DIV_INT": ["OP_DIV_INT"], 
            "OP_DIV_REAL": ["OP_DIV_REAL"], "OP_MOD": ["OP_MOD"], "OP_POT": ["OP_POT"], 
            "OP_MAIOR": ["OP_MAIOR"], "OP_MENOR": ["OP_MENOR"], "OP_IGUAL": ["OP_IGUAL"], 
            "OP_DIF": ["OP_DIF"], "OP_MAIOR_IGUAL": ["OP_MAIOR_IGUAL"], "OP_MENOR_IGUAL": ["OP_MENOR_IGUAL"]
        }
    }
    return tabela

