# Projeto_Arquitetura2

O projeto implementa a arquitetura de uma máquina Mic-1 modificada capaz de receber instruções IJVM e fornecer as saídas correspondentes.

A Mic-1 recebe instruções IJVM em um arquivo .txt e traduz em uma microinstrução de 23 bits. Esses 23 bits são divididos em 4 campos: 

* **4 bits para o Barramento B**, que seleciona um registrador para a entrada B da ULA;

* **8 bits para a ULA**, responsável pela operação escolhida (AND/OR/NOT_B/ADD); 

* **9 bits para o Barramento C**, que escreve o resultado nos registradores selecionados; 

* **e 2 bits para a Memória** que executa READ ou WRITE.

sendo a saída um outro arquivo .txt de log completo com registradores, memória e flags.
