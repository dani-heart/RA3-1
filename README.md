# Analisador Semântico e Gerador de Código (Fase 3)

## 1. Cabeçalho Acadêmico


Pontifícia Universidade Católica do Paraná
Linguagens Formais e Compiladores
Frank Coelho de Alcântara
Integrantes do grupo (ordem alfabética):
- Dani Heart Basso - @dani-heart
Nome do grupo no Canvas: RA3-1


---

## 2. Contexto e Evolução (De onde viemos)

Esta disciplina é estruturada de forma incremental, desenvolvendo um compilador completo passo a passo ao longo do semestre.

- **Fase 1 (Analisador Léxico):** Construímos a base de tokenização utilizando Expressões Regulares (Regex). O programa já funcionava como uma calculadora RPN (Notação Polonesa Reversa) avançada, com suporte a comandos de memória (`MEM`), histórico de resultados (`RES`) e geração direta de código Assembly ARMv7 (já arquitetado para utilizar registradores de precisão dupla F64 do coprocessador VFP).
- **Fase 2 (Analisador Sintático):** Implementamos um Parser Descendente Recursivo Preditivo do tipo **LL(1)**. Através do uso de fatoração à esquerda, eliminamos as ambiguidades causadas pelo uso massivo de parênteses da notação RPN. O parser passou a validar a ordem estrutural dos tokens e a gerar uma Árvore Sintática Abstrata (AST). Contudo, essa árvore ainda era estruturalmente "ingênua": ela garantia que a gramática estava correta, mas deixava passar absurdos lógicos (como tentar dividir um texto por um número).



---

## 3. O Desafio da Fase 3 (Para onde fomos)

Nesta terceira fase, o compilador ganhou o seu módulo de **Análise Semântica** — o verdadeiro "cérebro lógico" que atua como um validador entre o Parser e o Gerador de Código. O objetivo principal foi analisar a árvore gerada na fase anterior e barrar operações que, embora gramaticalmente perfeitas, são logicamente inválidas.

As principais adições desta fase incluem:
- **Analisador Semântico (Caminhada Bottom-Up):** Um motor que percorre a Árvore Sintática de baixo para cima, inferindo os tipos de cada nó folha e propagando-os até a raiz. Ele atua coletando inconsistências simultâneas, blindando a geração do Assembly contra quebras sistêmicas.
- **Tabela de Símbolos ($\Gamma$):** Um ambiente de memória encarregado de registrar o nascimento de cada variável, inferir e travar o seu tipo primitivo estrito na sua primeira atribuição, além de rastrear as exatas linhas onde a variável foi utilizada ou referenciada indevidamente.
- **Tipagem Estática e Rigorosa:** Introdução de validação estrita de tipos lógicos (`int`, `double` e `bool`), impossibilitando conversões implícitas ou misturas de numéricos diferentes em operações matemáticas primitivas.
- **Estruturas de Controle Semânticas:** Validação interna para estruturas de blocos, exigindo que as premissas formadas para os comandos condicionais (`IF` e `WHILE`) resultem invariavelmente em um tipo `bool`.
- **Comentários de Bloco Seguros:** O lexer foi adaptado para dar suporte aos comentários `*{ ... }*`. O grande diferencial foi a estratégia de limpar esses comentários substituindo-os por quebras de linha exatas, mantendo a contagem do "GPS" (linhas numéricas) intacta para a denúncia de erros semânticos.



---

## 4. Arquitetura e Mapa de Módulos

### `lexer.py`
- **COMO ERA ANTES:** Lia o texto bruto e, através de Expressões Regulares (`re.findall`), transformava strings em `Tokens` ignorando espaços.
- **COMO É AGORA:** Precisou ser adaptado para suportar os novos comentários em bloco `*{ ... }*`. A grande sacada foi que, ao invés de simplesmente deletar o comentário, o Lexer substitui o bloco por quebras de linha (`\n`). Isso preserva o "GPS" das linhas, garantindo que um erro na linha 50 seja reportado corretamente na linha 50, mesmo que haja 20 linhas de comentários antes.

### `parser.py` e `gramatica.py`
- **COMO ERA ANTES:** O nosso Analisador Sintático LL(1) já havia sido construído de forma robusta na Fase 2. Por meio de fatoração à esquerda, resolvemos ambiguidades dos parênteses e já suportávamos os comandos `IF` e `WHILE`.
- **COMO É AGORA:** Graças ao excelente planejamento da gramática anterior, **não precisamos alterar a estrutura sintática**. O parser continuou intacto, servindo de base confiável para a nova etapa semântica.

### `arvore.py`
- **COMO ERA ANTES:** Definia a estrutura de dados (nós e folhas) para a Árvore Sintática Abstrata (AST).
- **COMO É AGORA:** A AST evoluiu para uma **Árvore Atribuída**. Foi adicionada a propriedade `tipo_dado` aos nós. Isso permite que o Analisador Semântico cole "etiquetas" na árvore (ex: avisando que o nó de uma soma resultou num `int` ou num `double`).

### `semantico.py`
- **COMO ERA ANTES:** Esse arquivo não existia na Fase 2! O compilador ingênuo aceitava absurdos lógicos e gerava código Assembly para eles, desde que estivessem gramaticalmente corretos.
- **COMO É AGORA:** É o cérebro lógico (O Detetive). Ele faz uma travessia "Bottom-Up" (de baixo para cima) na árvore. Ele gerencia a **Tabela de Símbolos**, que funciona como um caderninho registrando o nascimento, o tipo e as linhas de uso de cada variável. Além disso, ele blinda o sistema contra erros em cascata, coletando todas as falhas semânticas de uma vez antes de abortar a compilação.

### `assembly.py`
- **COMO ERA ANTES:** Na Fase 2, nosso gerador já era maduro. Ele já estava duramente adaptado para gerar código em ARMv7 VFP (F64 nativo) e suportava integralmente estruturas de controle (`BEQ`, `BGT`) integradas a comparações (`VCMP.F64`).
- **COMO É AGORA:** Nossa arquitetura se provou tão sólida que o módulo foi reaproveitado de forma intacta na Fase 3. A diferença reside na **blindagem**: agora, a compilação só alcança a fase de Assembly caso o Analisador Semântico não levante nenhuma bandeira vermelha, prevenindo geração de código mal-formado logicamente.
---

## 5. Tipagem e Regras da Linguagem

A linguagem agora possui tipagem estática e forte, dividida em três tipos primitivos: `int`, `double` e `bool`. O arquivo `semantico.py` aplica as seguintes regras:

- **Declaração e Escopo:** Variáveis nascem ao receber um valor via `(VALOR VARIAVEL)`. O tipo da variável fica travado para sempre na Tabela de Símbolos baseando-se na primeira atribuição. Tentar mudar o tipo depois gera Erro Semântico.
- **Operações Aritméticas Gerais (`+`, `-`, `*`, `^`):** Exigem que os dois operandos sejam *exatamente* do mesmo tipo (só `int` com `int`, ou `double` com `double`). O retorno mantém o tipo dos operandos.
- **Divisão Inteira (`/`) e Módulo (`%`):** Extremamente estritos. Só aceitam operandos do tipo `int`.
- **Divisão Real (`|`):** Extremamente estrita. Só aceita operandos do tipo `double`.
- **Operações Relacionais (`>`, `<`, `==`, `!=`, `>=`, `<=`):** Exigem operandos do mesmo tipo (paridade) e **sempre** retornam o tipo `bool`.
- **Controle de Fluxo (`IF`, `WHILE`):** O nó de condição que antecede o bloco precisa obrigatoriamente resultar no tipo `bool`.
- **Histórico (`RES`):** O comando `RES` exige obrigatoriamente um valor `int` não-negativo para buscar o histórico de expressões.

---

## 6. Instruções de Uso

Para executar o compilador completo contra um código-fonte, utilize o comando abaixo no terminal:
```bash
python main.py caminho/do/arquivo.txt
```
Caso o código passe pelas 3 fases sem erros, o compilador gerará os seguintes arquivos:
- `arvore_<nome>.json`: A representação visual da Árvore Atribuída.
- `tabela_simbolos_<nome>.json`: O dicionário com o mapeamento e tipos das variáveis.
- `output_<nome>.s`: O código Assembly ARMv7 completo, pronto para ser colado e rodado no CPulator.

---

## 7. Testes e Validação

Para garantir a resiliência do compilador em todas as fases, implementamos uma suíte completa de testes utilizando o framework `pytest`. No total, dezenas de cenários validam a corretude do código, divididos nos seguintes módulos:

| Arquivo de Teste | Funcionalidade Validada |
| --- | --- |
| `test_lexer.py` | Garante que tokens isolados são classificados corretamente, regex não falha em números com ponto flutuante e que erros léxicos não quebram o script. |
| `test_parser.py` | Utiliza *Stubs* (Mocks) para testar a Tabela LL(1) de forma isolada, garantindo que erros sintáticos acusem a linha exata. |
| `test_semantico.py` | Testa exaustivamente as regras de negócio: rejeição de variáveis não declaradas, tipagem forte (`int` vs `double`), proteção do IF/WHILE exigindo `bool`. |
| `test_integracao.py` | Pipeline de ponta a ponta. Lê o `.txt`, gera árvore, passa pelo Semântico e verifica se o Assembly gerado contém as marcações cruciais do ARMv7 VFP (`.text`, `VSTR`, `D0`, etc). |

### O Arquivo `teste_boss.txt`
Trata-se de um teste de estresse criado para o CPulator. Ele implementa o cálculo e avaliação polinomial: $P(x) = 3x^3 - 5x^2 + 2x - 10$.
Ele mescla literais reais (double), variáveis na memória, potenciação, blocos aninhados profundos numa única árvore (O Monstro) e laços `WHILE` com premissas condicionais severas, testando o limite do loop de execução em coprocessamento F64 no hardware final simulado.

---

## 8. Divisão de Tarefas

Como o grupo é composto por um único integrante, todas as responsabilidades foram concentradas. Para fins de avaliação, o mapeamento de funções foi desempenhado da seguinte forma:

- **Aluno 1 / Dani Heart Basso (Preparação e Integração das Fases):** `lexer.py` foi atualizado para tratar `*{ ... }*` de forma a preservar os números originais das linhas. O orquestrador em `main.py` foi expandido para conectar a AST gerada pelo Parser ao Analisador Semântico.
- **Aluno 2 / Dani Heart Basso (Tabela de Símbolos e Declarações):** Implementado através da classe `TabelaSimbolos` (em `semantico.py`), encarregada de registrar variáveis ativas, garantir consistência contra reatribuições inválidas e impedir uso precoce.
- **Aluno 3 / Dani Heart Basso (Sistema de Regras Semânticas e Validação):** Mapeado na documentação `Sequentes.md` e materializado no fluxo *Bottom-Up* (`_visitar`) do `AnalisadorSemantico` (`semantico.py`), validando tipos de operandos e protegendo premissas `bool` em condicionais.
- **Aluno 4 / Dani Heart Basso (Árvore Atribuída, Assembly e Testes):** Expansão do construtor em `arvore.py` (adicionando a propriedade `tipo_dado` aos nós). Revisão da geração de código em `assembly.py` garantindo que só emite ARMv7 se limpo de erros lógicos. Criação e mapeamento da robusta suíte de testes com a biblioteca `pytest` garantindo a solidez dos 7 Níveis da pipeline.
