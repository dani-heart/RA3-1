# Integrantes do grupo (ordem alfabética):
# Dani Heart Basso - @dani-heart
#
# Nome do grupo no Canvas: RA3-1



import re
from dataclasses import dataclass

# @dataclass gera automaticamente o __init__, __repr__ e __eq__ da classe.
# É perfeito para classes que servem apenas para carregar dados.
@dataclass
class Token:
    tipo: str
    valor: str
    linha: int

# ETAPA 1: Mapeamento de Tokens Fixos

#Tudo que isso aqui faz é mapear o que significa cada token. mantém muitos indicativos iguais,
#como "START": "START", mas é parte do jogo isso
MAPA_TOKENS_FIXOS = {
      #Tokens de estrutura e ordenação
    "(": "LPAREN",
    ")": "RPAREN",
    "START": "START",
    "END": "END",
    
    # Palavras de controle e comando, todas são reservadas
    "RES": "KEYWORD_RES",
    "LET": "KEYWORD_LET",
    "IF": "IF",
    "WHILE": "WHILE",
    
    # Operadores Matemáticos
    "+": "OP_SOMA", 
    "-": "OP_SUB", 
    "*": "OP_MULT", 
    "/": "OP_DIV_INT", 
    "|": "OP_DIV_REAL", 
    "%": "OP_MOD", 
    "^": "OP_POT",
    

    # Operadores de comparação, utilizados para tomar decisões
    ">": "OP_MAIOR", "<": "OP_MENOR",
    "==": "OP_IGUAL", "!=": "OP_DIF",
    ">=": "OP_MAIOR_IGUAL", "<=": "OP_MENOR_IGUAL"
}

# ETAPA 2: Função Classificadora
#Classifica uma string para o tipo de token 

def _classificar_token(valor: str, linha: int) -> Token:
    """Classifica uma string bruta no tipo de Token correspondente."""
    
    #Verifica se é palavra reservada ou operador fixo.
    # Usamos um dicionário (MAPA_TOKENS_FIXOS) para facilitar a legibilidade do código
    if valor in MAPA_TOKENS_FIXOS:
        return Token(MAPA_TOKENS_FIXOS[valor], valor, linha)
    
    #Verifica se é Número Inteiro (pode ter sinal de negativo)
    #Aqui estamos utilizando Regex. 
    ## ^ -> Início
    ## -? -> Se for negativo
    ## \d+ -> Se tiver 1 ou mais números
    ## $ -> Fim
    if re.match(r'^-?\d+$', valor):
        return Token("NUM_INT", valor, linha)   
    #Verifica se é Número Real (com ponto flutuante e possível sinal)
    # Regex: igual ao de cima, mas exige um ponto (\.) seguido de mais números.
    if re.match(r'^-?\d+\.\d+$', valor):
        return Token("NUM_REAL", valor, linha)
        
    #Verifica se é Variável de Memória (apenas letras MAIÚSCULAS)
    #
    # Regex: ^[A-Z]+$ significa "De A até Z, sem números, sem minúsculas, só isso"
    # Importante: palavras reservadas (IF, WHILE, RES, etc.) chegam aqui também,
    # mas são capturadas pelo MAPA_TOKENS_FIXOS acima — a ordem das verificações garante isso.
    if re.match(r'^[A-Z]+$', valor):
        return Token("MEM", valor, linha)
        
    # Se não encaixou em nenhuma regra acima, é Erro! (Lexico)
    raise ValueError(f"Erro léxico na linha {linha}: caractere ou palavra não reconhecida '{valor}'")

# ETAPA 3: Função Principal de Leitura

#Lê o arquivo e gera a estrutura de Tokens. Principal pedida do Aluno3
def lerTokens(caminho_arquivo: str) -> list[Token]:
    
    tokens: list[Token] = [] #Inicializa vazio e vai incrementando
    
    try:#Tenta abrir o arquivo
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            conteudo_completo = f.read()

        # Fase 3: Remove comentários em bloco *{ ... }* antes de tokenizar.
        # Para não quebrar a contagem de linhas em caso de erros posteriores, 
        # substituímos o bloco pela exata quantidade de quebras de linha que ele possuía.
        def _preservar_linhas(match):
            return '\n' * match.group(0).count('\n')
            
        conteudo_sem_comentarios = re.sub(r'\*\{.*?\}\*', _preservar_linhas, conteudo_completo, flags=re.DOTALL)

        for num_linha, linha_texto in enumerate(conteudo_sem_comentarios.splitlines(), start=1):
                
            # Remove espaços em branco nas pontas e ignora linhas vazias
            linha_limpa = linha_texto.strip()
            if not linha_limpa:
                continue
            
            partes = re.findall(r'\(|\)|[^\s()]+', linha_limpa)
            for parte in partes:
                token = _classificar_token(parte, num_linha)
                tokens.append(token)
                    
    except FileNotFoundError:
        raise FileNotFoundError(f"Erro: O arquivo '{caminho_arquivo}' não foi encontrado.")
        
    return tokens