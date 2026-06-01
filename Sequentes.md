# Sistema de Regras de Tipos (Cálculo de Sequentes)

Este documento descreve as regras formais de inferência e validação de tipos implementadas no Analisador Semântico (Fase 3). Utilizamos a notação do Cálculo de Sequentes para demonstrar as condições necessárias para que uma expressão ou comando seja semanticamente válido.

## 1. O Ambiente $\Gamma$ (Tabela de Símbolos)

O símbolo $\Gamma$ (Gamma) representa o ambiente de tipagem estática corrente do programa, ou seja, a nossa **Tabela de Símbolos**. 
Ele mapeia o identificador único de uma variável para o seu tipo primitivo inferido. O nosso sistema atua sob tipagem estática, forte e com tipos fechados em: `int`, `double` e `bool`.

## 2. Tipos Literais Básicos
A linguagem infere o tipo dos numerais brutos baseando-se na presença ou ausência do ponto flutuante.

- **Literal Inteiro (`NUM_INT`):**
  $$ \Gamma \vdash NUM\_INT : int $$

- **Literal Real (`NUM_REAL`):**
  $$ \Gamma \vdash NUM\_REAL : double $$

## 3. Regras de Memória e Variáveis
A linguagem exige que o uso de variáveis respeite sua declaração inicial e bloqueia mudanças de tipo ou referências não inicializadas.

- **Armazenamento e Declaração (`CMD_MEM_STORE`):** Ao associar um valor a uma variável (`MEM`), a variável assume ou preserva o tipo da expressão avaliada.
  $$ \frac{\Gamma \vdash e : \tau}{\Gamma[MEM \mapsto \tau] \vdash (e \ MEM) : \tau} $$

- **Recuperação de Valor (`CMD_MEM_LOAD` / `MEM_ID`):** O uso da variável é permitido apenas se ela já consta no ambiente $\Gamma$.
  $$ \frac{MEM : \tau \in \Gamma}{\Gamma \vdash (MEM) : \tau} $$

## 4. Regras Aritméticas
Todas as operações aritméticas exigem paridade exata de tipos (não há coerção ou promoção implícita).

- **Adição, Subtração, Multiplicação e Potência (`+`, `-`, `*`, `^`):** Válidas uniformemente sob paridade para ambos:
  $$ \frac{\Gamma \vdash e_1 : \tau \quad \Gamma \vdash e_2 : \tau \quad \tau \in \{int, double\}}{\Gamma \vdash (e_1 \ e_2 \ op) : \tau} $$

- **Divisão Inteira (`/`) e Módulo (`%`):** Exclusivas e restritas a operandos do tipo primitivo inteiro.
  $$ \frac{\Gamma \vdash e_1 : int \quad \Gamma \vdash e_2 : int}{\Gamma \vdash (e_1 \ e_2 \ op\_int) : int} $$

- **Divisão Real Completa (`|`):** Exclusiva e restrita a operandos do tipo primitivo real.
  $$ \frac{\Gamma \vdash e_1 : double \quad \Gamma \vdash e_2 : double}{\Gamma \vdash (e_1 \ e_2 \ |) : double} $$

## 5. Regras Relacionais
Os comparadores (`==`, `!=`, `>`, `<`, `>=`, `<=`) exigem checagem paritária estrita dos operandos e sempre forçarão inferência final para um novo tipo Lógico/Booleano.

$$ \frac{\Gamma \vdash e_1 : \tau \quad \Gamma \vdash e_2 : \tau \quad \tau \in \{int, double\}}{\Gamma \vdash (e_1 \ e_2 \ op\_rel) : bool} $$

## 6. Controle de Fluxo (`IF` e `WHILE`)
As premissas condicionais de `IF` e `WHILE` rejeitam expressões numéricas diretas, exigindo obrigatoriamente a presença de uma avaliação que resulte no tipo `bool`. O retorno do bloco executado é vazio (`void`).

- **Condicional e Laço:**
  $$ \frac{\Gamma \vdash cond : bool \quad \Gamma \vdash bloco\_comandos : void}{\Gamma \vdash (cond \ (LET \ bloco\_comandos) \ IF/WHILE) : void} $$

## 7. Comando de Resultado Histórico (`RES`)
O comando especial de recuperação de histórico semântico `RES` em formato de recuo temporal exige que a expressão de índice fornecida seja um inteiro avaliado sempre como não-negativo.

$$ \frac{\Gamma \vdash e : int \quad e \ge 0}{\Gamma \vdash (e \ RES) : \tau\_historico} $$