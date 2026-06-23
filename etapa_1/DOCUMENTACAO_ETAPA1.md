# Resumo da Etapa 1 (ULA Mic-1)

 Resumo bem simples e rápido de como deixei o `main.py` funcionando.

## 1. O que já está pronto
- **A Lógica Central:** O código faz as 4 operações pedidas (Soma, AND, OR e NOT) usando aquelas instruções curtinhas de **6 bits**.
- **Entrada e Saída:** Ele lê as instruções do arquivo `programa_etapa1.txt` e salva tudo bonitinho numa tabela dentro do arquivo `saida_etapa1.txt`.

## 2. Por que o código ficou assim? (Minhas escolhas)
Eu preferi usar símbolos matemáticos diretos (`&, |, ^, ~`) ao invés de encher o código com `if` e `else`. Assim o código fica menor e imita a placa de verdade.

Olha as sacadas:
- **`MASK = 1`:** O Python gosta de somar `1+1` e responder `2`. Eu usei isso pra travar ele e forçar a resposta a ser sempre `0` ou `1`, do jeito que a tarefa pede.
- **Símbolo `^` (XOR):** Eu usei ele pra inverter o `A`. É só colocar o símbolo e ele inverte o valor na hora, sem dor de cabeça.
- **Somar o `INC` junto:** Coloquei a variável `INC` direto no meio da conta de soma porque ela funciona exatamente como aquele famoso "+1" da matemática de escola.
- **O `>> 1` para o Vai-um:** Pra saber se a conta estourou e gerou um "Vai-um", eu empurrei o resultado pra direita com o `>> 1`. Isso faz a resposta normal sumir e sobra só o valor do Vai-um, separadinho na tela.


