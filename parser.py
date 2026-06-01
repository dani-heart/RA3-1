# Integrantes do grupo (ordem alfabética):
# Dani Heart Basso - @dani-heart
#
# Nome do grupo no Canvas: RA3-1

from typing import Any, Optional, Protocol

# Importante! Todas as decisoes de arquitetura que estao comentadas aqui, tambem estao no arquivo de suporte, 
# Dani, favor revisar arquivo de suporte antes de implementar aluno3. 

# O que é Protocol? E por que estamos usando protocol nesse projeto? 

# minha ref: https://docs.python.org/pt-br/3/library/typing.html#typing.Protocol
# also, https://typing.python.org/en/latest/spec/protocol.html#protocols
# entao, basicamente, o nosso objetivo é definir que a nossa classe Token precissa ter essa forma (esses atributos, que 
# tem valores desses tipos) para ser valida  ao inves de criar interdependencia com outros modulos do projeto por import.
class Token(Protocol):
    tipo: str
    valor: str
    linha: int

#Proxima decisao: por que nos usamos protocol para o contrutor da arvore? 
# mesmo motivo -> nosso parser apenas precisa saber como a arvore é representada no projeto. 
# Construir a arvore em si é tarefa de aluno4, mas parser precisa saber qual estrturua usar para a saida.

# Por que usamos Handles como Any? parser passa os retornos do builder sem inspecioná-los. 
# Não sabe e nem precisa saber o que está dentro.
class ConstrutorArvore(Protocol):
    def criar_operando_num(self, valor: str, linha: int) -> Any: ...
    def criar_operando_mem(self, nome: str, linha: int) -> Any: ...
    def criar_operador(self, simbolo: str, linha: int) -> Any: ...
    def criar_expr(self, esq: Any, dir: Any, op: Any, linha: int) -> Any: ...
    def criar_cmd_res(self, n: str, linha: int) -> Any: ...
    def criar_cmd_mem_store(self, valor_no: Any, nome: str, linha: int) -> Any: ...
    def criar_cmd_mem_load(self, nome: str, linha: int) -> Any: ...
    def criar_bloco(self, cmds: list, linha: int) -> Any: ...
    def criar_if(self, cond: Any, bloco: Any, linha: int) -> Any: ...
    def criar_while(self, cond: Any, bloco: Any, linha: int) -> Any: ...
    def criar_programa(self, cmds: list, linha: int) -> Any: ...
    

class ErroSintatico(Exception):
    pass

# Por que Parser eh uma classe interna? aq usamos encapsulamento de estado (pos, tokens,
#   builder). A única interface pública é parsear(). Quem chama não gerencia objetos.
class _Parser:
    OPERADORES = {
        "OP_SOMA", "OP_SUB", "OP_MULT", "OP_DIV_INT", "OP_DIV_REAL",
        "OP_MOD", "OP_POT", "OP_MAIOR", "OP_MENOR", "OP_IGUAL",
        "OP_DIF", "OP_MAIOR_IGUAL", "OP_MENOR_IGUAL"
    }
    OP_VALOR = {
        "OP_SOMA": "+", "OP_SUB": "-", "OP_MULT": "*",
        "OP_DIV_INT": "/", "OP_DIV_REAL": "|", "OP_MOD": "%",
        "OP_POT": "^", "OP_MAIOR": ">", "OP_MENOR": "<",
        "OP_IGUAL": "==", "OP_DIF": "!=",
        "OP_MAIOR_IGUAL": ">=", "OP_MENOR_IGUAL": "<="
    }
    def __init__(self, tokens: list[Token], tabela_ll1: dict, builder: ConstrutorArvore) -> None:
        self._tokens = tokens
        self._pos = 0
        self._tabela = tabela_ll1
        self._builder = builder
        
    def _atual(self) -> Optional[Token]:
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def _linha_atual(self) -> int:
        t = self._atual()
        return t.linha if t else -1

    # Aqui temos ErroSintatico com número de linha: mensagem inclui linha,
    # token esperado e token encontrado para facilitar debug (RF de projeto)
    
    def _consumir(self, tipo_esperado: str) -> Token:
        tok = self._atual()
        if tok is None:
            raise ErroSintatico(
                f"Erro sintático na linha {self._linha_atual()}: "
                f"esperado '{tipo_esperado}', mas chegou ao fim da entrada."
            )
        if tok.tipo != tipo_esperado:
            raise ErroSintatico(
                f"Erro sintático na linha {tok.linha}: "
                f"esperado '{tipo_esperado}', encontrado '{tok.tipo}' ('{tok.valor}')."
            )
        self._pos += 1
        return tok

    def _tipo_atual(self) -> Optional[str]:
        t = self._atual()
        return t.tipo if t else None

    # Regras gramaticais — uma função por não-terminal
    # Por que cada não-terminal da gramática vira uma função privada? Facilita rastrear erros e corresponde diretamente ao EBNF documentado.
    
    def _programa(self) -> Any:
        linha = self._linha_atual()
        self._consumir("LPAREN")
        self._consumir("START")
        self._consumir("RPAREN")
        cmds = self._lista_comandos_globais()
        return self._builder.criar_programa(cmds, linha)

    def _lista_comandos_globais(self) -> list:
        self._consumir("LPAREN")
        return self._conteudo_global()

    def _conteudo_global(self) -> list:
        tipo = self._tipo_atual()
        
        # END fecha o bloco (caso base), qualquer início de comando
        # continua recursivamente. 
        # O RPAREN que fecha o comando corrente já foi
        # consumido por _lista_comandos_globais antes de chamar _conteudo_global.
        if tipo == "END":
            self._consumir("END")
            self._consumir("RPAREN")  # fecha o (END)
            return []
        elif tipo in ("NUM_INT", "NUM_REAL", "MEM", "LPAREN"):
            cmd = self._conteudo_comando()
            self._consumir("RPAREN")   # fecha o ( cmd )
            resto = self._lista_comandos_globais()  # abre o próximo (
            return [cmd] + resto
        else:
            tok = self._atual()
            raise ErroSintatico(
                f"Erro sintático na linha {self._linha_atual()}: "
                f"esperado comando ou END, encontrado "
                f"'{tok.tipo if tok else 'EOF'}' ('{tok.valor if tok else ''}')."
            )

    # Por que usamos loop em vez de recursão para blocos IF/WHILE?
    #   produção com ε, mais legível e sem risco de stack overflow em blocos grandes.
    def _lista_comandos_bloco(self) -> list:
        cmds: list = []
        while self._tipo_atual() == "LPAREN":
            self._consumir("LPAREN")
            cmd = self._conteudo_comando()
            self._consumir("RPAREN")
            cmds.append(cmd)
        return cmds

    def _conteudo_comando(self) -> Any:
        tipo = self._tipo_atual()
        linha = self._linha_atual()

        if tipo == "NUM_INT":
            tok = self._consumir("NUM_INT")
            return self._acao_numero(tok)

        elif tipo == "NUM_REAL":
            tok = self._consumir("NUM_REAL")
            return self._acao_numero(tok)

        elif tipo == "MEM":
            tok = self._consumir("MEM")
            return self._builder.criar_cmd_mem_load(tok.valor, tok.linha)

        elif tipo == "LPAREN":
            self._consumir("LPAREN")
            expr_no = self._conteudo_par()
            self._consumir("RPAREN")
            return self._acao_pos_par(expr_no, linha)

        else:
            tok = self._atual()
            raise ErroSintatico(
                f"Erro sintático na linha {linha}: "
                f"esperado início de comando (NUM_INT, NUM_REAL, MEM ou LPAREN), "
                f"encontrado '{tok.tipo if tok else 'EOF'}'."
            )

    def _acao_numero(self, primeiro: Token) -> Any:
        # Chegamos aqui depois de consumir um NUM_INT ou NUM_REAL. O token seguinte
        # (lookahead) determina qual caso seguir:
        #   KEYWORD_RES comando (N RES): retorna N resultado anterior
        #   MEM         comando (V MEM): armazena valor numa variável V
        #   NUM/LPAREN  expressão com dois operandos: (esq dir op)
        tipo = self._tipo_atual()
        linha = primeiro.linha

        if tipo == "KEYWORD_RES":
            self._consumir("KEYWORD_RES")
            return self._builder.criar_cmd_res(primeiro.valor, linha)

        elif tipo == "MEM":
            tok_mem = self._consumir("MEM")
            valor_no = self._builder.criar_operando_num(primeiro.valor, linha)
            return self._builder.criar_cmd_mem_store(valor_no, tok_mem.valor, linha)

        elif tipo in ("NUM_INT", "NUM_REAL", "LPAREN"):
            # Expressão RPN: primeiro já foi lido, agora lemos segundo operando e operador.
            # Ordem na gramática: esq dir op.
            op_esq = self._builder.criar_operando_num(primeiro.valor, linha)
            op_dir = self._operando()
            op_no = self._operador()
            return self._builder.criar_expr(op_esq, op_dir, op_no, linha)

        else:
            tok = self._atual()
            raise ErroSintatico(
                f"Erro sintático na linha {linha}: "
                f"após número esperado RES, variável MEM ou segundo operando, "
                f"encontrado '{tok.tipo if tok else 'EOF'}'."
            )

    def _conteudo_par(self) -> Any:
        # Dentro do parêntese aberto por _conteudo_comando, a gramática só
        # permite uma expressão completa (esq dir op). 
        return self._expressao()

    def _acao_pos_par(self, expr_esq: Any, linha: int) -> Any:
        # Chegamos aqui com expr_esq já construída (sub-expressão entre parênteses).
        # O próximo token decide se ela é o operando esquerdo de uma expressão maior
        # ou se é a condição de um IF/WHILE (caso LPAREN → _conteudo_pos_par_lparen).
        tipo = self._tipo_atual()

        if tipo == "NUM_INT":
            tok = self._consumir("NUM_INT")
            op_dir = self._builder.criar_operando_num(tok.valor, tok.linha)
            op_no = self._operador()
            return self._builder.criar_expr(expr_esq, op_dir, op_no, linha)

        elif tipo == "NUM_REAL":
            tok = self._consumir("NUM_REAL")
            op_dir = self._builder.criar_operando_num(tok.valor, tok.linha)
            op_no = self._operador()
            return self._builder.criar_expr(expr_esq, op_dir, op_no, linha)

        elif tipo == "LPAREN":
            self._consumir("LPAREN")
            return self._conteudo_pos_par_lparen(expr_esq, linha)

        else:
            tok = self._atual()
            raise ErroSintatico(
                f"Erro sintático na linha {linha}: "
                f"após expressão entre parênteses esperado NUM_INT, NUM_REAL ou LPAREN, "
                f"encontrado '{tok.tipo if tok else 'EOF'}'."
            )

    def _conteudo_pos_par_lparen(self, expr_esq: Any, linha: int) -> Any:
        # Neste ponto consumimos dois LPAREN seguidos e expr_esq já está construída.
        # KEYWORD_LET → estrutura de controle: (( cond (LET cmds) IF/WHILE ))
        #   qualquer outro início de operando -> expressão aninhada: (( esq dir op ))
        tipo = self._tipo_atual()

        if tipo == "KEYWORD_LET":
            self._consumir("KEYWORD_LET")
            cmds = self._lista_comandos_bloco()
            self._consumir("RPAREN")   # fecha o (LET ...)
            controle_tipo = self._controle()  # IF ou WHILE decide qual nó criar
            bloco = self._builder.criar_bloco(cmds, linha)
            if controle_tipo == "IF":
                return self._builder.criar_if(expr_esq, bloco, linha)
            else:
                return self._builder.criar_while(expr_esq, bloco, linha)

        elif tipo in ("MEM", "NUM_INT", "NUM_REAL", "LPAREN"):
            op_dir = self._conteudo_operando_no()
            self._consumir("RPAREN")
            op_no = self._operador()
            return self._builder.criar_expr(expr_esq, op_dir, op_no, linha)

        else:
            tok = self._atual()
            raise ErroSintatico(
                f"Erro sintático na linha {linha}: "
                f"dentro de parêntese duplo esperado LET ou operando, "
                f"encontrado '{tok.tipo if tok else 'EOF'}'."
            )

    # Por que _controle() retorna string, não nó? IF/WHILE sozinhos não têm significado isolado. 
    # A string direciona qual método do builder chamar.
    def _controle(self) -> str:
        tipo = self._tipo_atual()
        if tipo == "IF":
            self._consumir("IF")
            return "IF"
        elif tipo == "WHILE":
            self._consumir("WHILE")
            return "WHILE"
        else:
            tok = self._atual()
            raise ErroSintatico(
                f"Erro sintático na linha {self._linha_atual()}: "
                f"esperado IF ou WHILE, encontrado '{tok.tipo if tok else 'EOF'}'."
            )

    def _expressao(self) -> Any:
        # Gramática RPN: operando esquerdo, operando direito, operador (nessa ordem).
        # Diferente de infix (esq op dir) — o operador sempre vem por último.
        linha = self._linha_atual()
        op_esq = self._operando()
        op_dir = self._operando()
        op_no = self._operador()
        return self._builder.criar_expr(op_esq, op_dir, op_no, linha)

    def _operando(self) -> Any:
        tipo = self._tipo_atual()
        linha = self._linha_atual()

        if tipo == "NUM_INT":
            tok = self._consumir("NUM_INT")
            return self._builder.criar_operando_num(tok.valor, tok.linha)

        elif tipo == "NUM_REAL":
            tok = self._consumir("NUM_REAL")
            return self._builder.criar_operando_num(tok.valor, tok.linha)

        elif tipo == "LPAREN":
            self._consumir("LPAREN")
            no = self._conteudo_operando_no()
            self._consumir("RPAREN")
            return no

        else:
            tok = self._atual()
            raise ErroSintatico(
                f"Erro sintático na linha {linha}: "
                f"esperado operando (NUM_INT, NUM_REAL ou LPAREN), "
                f"encontrado '{tok.tipo if tok else 'EOF'}'."
            )

    def _conteudo_operando_no(self) -> Any:
        # Dentro de parênteses como operando, há dois casos distintos:
        #   MEM   -> referência a variável: (VAR) lê o valor armazenado
        #   resto -> expressão completa aninhada: (esq dir op) usada como sub-valor
        tipo = self._tipo_atual()
        linha = self._linha_atual()

        if tipo == "MEM":
            tok = self._consumir("MEM")
            return self._builder.criar_operando_mem(tok.valor, tok.linha)

        elif tipo in ("NUM_INT", "NUM_REAL", "LPAREN"):
            return self._expressao()

        else:
            tok = self._atual()
            raise ErroSintatico(
                f"Erro sintático na linha {linha}: "
                f"esperado MEM ou expressão dentro de parênteses, "
                f"encontrado '{tok.tipo if tok else 'EOF'}'."
            )

    def _operador(self) -> Any:
        # OPERADORES é um set com todos os tipos de token de operador (aritmético e relacional).
        # OP_VALOR mapeia tipo do token -> símbolo legível que o builder vai receber.
        # Ex: "OP_DIV_INT" -> "/" e "OP_DIV_REAL" -> "|" (divisão real usa pipe na linguagem).
        tipo = self._tipo_atual()
        linha = self._linha_atual()

        if tipo in self.OPERADORES:
            tok = self._consumir(tipo)
            return self._builder.criar_operador(self.OP_VALOR[tok.tipo], tok.linha)

        else:
            tok = self._atual()
            raise ErroSintatico(
                f"Erro sintático na linha {linha}: "
                f"esperado operador aritmético ou relacional, "
                f"encontrado '{tok.tipo if tok else 'EOF'}'."
            )


# Interface pública do parser. 

#   Aqui temos a assinatura parsear(tokens, tabela_ll1, builder): tabela recebida
#   por contrato (produzida por aluno 1), builder injetado de fora (aluno 4).
#   Parser não cria o builder; não sabe o que ele produz.
#   Por que retorna Any? Decisao de arquitetura, o retorno é o que o builder produz. 
#   Parser não importa no nem conhece a representação interna, estamos evitando dependência circular.

def parsear(tokens: list[Token], tabela_ll1: dict, builder: ConstrutorArvore) -> Any:
    """Analisa a lista de tokens e constrói a saída via callbacks ao builder."""
    parser = _Parser(tokens, tabela_ll1, builder)
    resultado = parser._programa()
    tok_restante = parser._atual()
    if tok_restante is not None:
        raise ErroSintatico(
            f"Erro sintático na linha {tok_restante.linha}: "
            f"tokens inesperados após o fim do programa: "
            f"'{tok_restante.tipo}' ('{tok_restante.valor}')."
        )
    return resultado
