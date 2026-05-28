# Integrantes do grupo (ordem alfabética):
# Dani Heart Basso - @dani-heart
#
# Nome do grupo no Canvas: RA3-1

import json
from dataclasses import dataclass, field, asdict
from typing import Optional
from arvore import No

@dataclass
class Simbolo:
    """Representa uma variável armazenada na Tabela de Símbolos."""
    nome: str
    linha_definicao: int
    tipo_inferido: Optional[str] = None
    linhas_uso: list[int] = field(default_factory=list)

class TabelaSimbolos:
    """Gerencia o escopo global de variáveis do programa."""
    def __init__(self):
        self.simbolos: dict[str, Simbolo] = {}

    def declarar(self, nome: str, linha: int, tipo: str) -> Optional[str]:
        """Registra a criação de uma variável via comando (V MEM)."""
        if nome not in self.simbolos:
            self.simbolos[nome] = Simbolo(nome=nome, linha_definicao=linha, tipo_inferido=tipo)
            return None
        else:
            simbolo = self.simbolos[nome]
            if simbolo.tipo_inferido != tipo:
                return f"Erro na linha {linha}: Variável '{nome}' tipada como '{simbolo.tipo_inferido}' não pode receber o tipo '{tipo}'."
            return None

    def registrar_uso(self, nome: str, linha: int) -> Optional[str]:
        """Registra que uma variável foi usada e verifica se ela existe."""
        if nome not in self.simbolos:
            return f"Erro na linha {linha}: Variável '{nome}' utilizada antes de ser definida."
        
        self.simbolos[nome].linhas_uso.append(linha)
        return None

    def obter_tipo(self, nome: str) -> Optional[str]:
        """Retorna o tipo de uma variável previamente declarada."""
        if nome in self.simbolos:
            return self.simbolos[nome].tipo_inferido
        return None

class AnalisadorSemantico:
    """Caminha pela Árvore Sintática validando regras e preenchendo a Tabela de Símbolos."""
    def __init__(self, arvore: No):
        self.arvore = arvore
        self.tabela = TabelaSimbolos()
        self.erros: list[str] = []

    def analisar(self) -> tuple[TabelaSimbolos, list[str]]:
        """Inicia a caminhada pela árvore e retorna a tabela construída e os erros encontrados."""
        self._visitar(self.arvore)
        return self.tabela, self.erros

    def _visitar(self, no: No) -> Optional[str]:
        """
        Método dispatcher: Caminhada Bottom-Up. 
        Visita os filhos primeiro, infere o tipo do nó atual e o retorna.
        """
        # 1. Desce na árvore primeiro (Bottom-Up)
        tipos_filhos = []
        for filho in no.filhos:
            # Evita registrar a declaração como "uso" da variável
            if no.tipo == "CMD_MEM_STORE" and filho.tipo == "MEM_ID":
                tipos_filhos.append(None)
            else:
                tipos_filhos.append(self._visitar(filho))
            
        tipo_inferido = None
        
        # 2. Infere o tipo do nó atual
        if no.tipo == "OPERANDO":
            if no.valor and "." in no.valor:
                tipo_inferido = "double"
            else:
                tipo_inferido = "int"
                
        elif no.tipo == "MEM_ID":
            nome_var = no.valor
            erro = self.tabela.registrar_uso(nome_var, no.linha)
            if erro:
                self.erros.append(erro)
            else:
                tipo_inferido = self.tabela.obter_tipo(nome_var)
                
        elif no.tipo == "CMD_MEM_STORE":
            # filhos[0] é o valor, filhos[1] é o nome da variável (MEM_ID)
            valor_tipo = tipos_filhos[0]
            nome_var = no.filhos[1].valor
            
            if valor_tipo:
                erro = self.tabela.declarar(nome_var, no.linha, valor_tipo)
                if erro:
                    self.erros.append(erro)
            tipo_inferido = valor_tipo
            
        elif no.tipo == "CMD_MEM_LOAD":
            # O nó filho MEM_ID já foi visitado, realizou o registro do uso
            # e retornou o tipo na subida da recursão
            tipo_inferido = tipos_filhos[0]

        elif no.tipo == "EXPR":
            tipo_esq = tipos_filhos[0]
            tipo_dir = tipos_filhos[1]
            op = no.filhos[2].valor
            
            # Só validamos se os dois lados tiverem tipos válidos (evita erros em cascata)
            if tipo_esq and tipo_dir:
                if op in ("+", "-", "*", "^"):
                    if tipo_esq == tipo_dir and tipo_esq in ("int", "double"):
                        tipo_inferido = tipo_esq
                    else:
                        self.erros.append(f"Erro na linha {no.linha}: Operação '{op}' incompatível entre '{tipo_esq}' e '{tipo_dir}'.")
                elif op in ("/", "%"):
                    if tipo_esq == "int" and tipo_dir == "int":
                        tipo_inferido = "int"
                    else:
                        self.erros.append(f"Erro na linha {no.linha}: Operação '{op}' exige operandos 'int', recebidos '{tipo_esq}' e '{tipo_dir}'.")
                elif op == "|":
                    if tipo_esq == "double" and tipo_dir == "double":
                        tipo_inferido = "double"
                    else:
                        self.erros.append(f"Erro na linha {no.linha}: Operação '{op}' exige operandos 'double', recebidos '{tipo_esq}' e '{tipo_dir}'.")
                elif op in (">", "<", "==", "!=", ">=", "<="):
                    if tipo_esq == tipo_dir:
                        tipo_inferido = "bool"
                    else:
                        self.erros.append(f"Erro na linha {no.linha}: Comparação '{op}' inválida entre '{tipo_esq}' e '{tipo_dir}'.")
                
        elif no.tipo in ("IF", "WHILE"):
            tipo_condicao = tipos_filhos[0]
            # A condição precisa existir e ser obrigatoriamente "bool"
            if tipo_condicao and tipo_condicao != "bool":
                self.erros.append(f"Erro na linha {no.linha}: A condição do comando '{no.tipo}' exige um tipo 'bool', mas recebeu '{tipo_condicao}'.")
                
        elif no.tipo == "CMD_RES":
            tipo_n = tipos_filhos[0]
            n_valor = no.filhos[0].valor
            if tipo_n != "int":
                self.erros.append(f"Erro na linha {no.linha}: O comando 'RES' exige um argumento 'int', mas recebeu '{tipo_n}'.")
            elif n_valor and int(n_valor) < 0:
                self.erros.append(f"Erro na linha {no.linha}: O comando 'RES' exige um valor não negativo, mas recebeu '{n_valor}'.")
                
        # 3. Guarda o tipo inferido no nó (Árvore Atribuída)
        no.tipo_dado = tipo_inferido
        return tipo_inferido

def salvar_tabela_json(tabela: TabelaSimbolos, caminho: str) -> None:
    """Serializa a tabela de símbolos para um arquivo JSON."""
    dados = {nome: asdict(simbolo) for nome, simbolo in tabela.simbolos.items()}
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print(f"Tabela de símbolos salva em: {caminho}")