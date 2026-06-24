"""
    Memoria.PY - responsável pela leitura do arquivo de entrada com as instruções e criação do arquivo de saída com os resultados das instruções.
"""

import os

# classe para gerenciamento dos arquivos de entrada e saída
class GerenciadorArquivos:
    
    def __init__(self):

        # inicializa a classe
        self.programa = []
        self.entradas = {}
        self.saida = []
        
    def ler_programa(self, nome_arquivo):

        """
        Lê o arquivo com as intruções
        
        Args:
            nome_arquivo (str): nome do arquivo .txt
            
        Returns:
            list: lista com as instruções
        """
        
        try:

            with open(nome_arquivo, 'r', encoding='utf-8') as arquivo:
                self.programa = [linha.strip() for linha in arquivo if linha.strip()]  # ignora as linhas vazias
            return self.programa
        

        # erro de arquivo não encontrado/inexistente
        except FileNotFoundError:
            print(f"Arquivo '{nome_arquivo}' não encontrado ou não existe. Dê um jeito no arquivo.")
            return []
        
        # erro na leitura do arquivo
        except Exception as e:
            print(f"Erro '{e}' ao ler o arquivo '{nome_arquivo}'")
            return []



    def ler_entradas(self, nome_arquivo, formato = 'binario'):

        """
        Lê os arquivos de entrada A e B

        Args:
            nome_arquivo (str): nome do arquivo . txt
            formato (str): 'binário'

        Returns:
            dict: dicionário com as entradas A e B
        
        """

        try:

            with open(nome_arquivo, 'r', encoding='utf-8') as arquivo:
                linhas = [linha.strip() for linha in arquivo if linha.strip()]  # ignora as linhas vazias
            
            if len(linhas) >= 2:

                if formato == 'binario':
                    self.entradas['A'] = int(linhas[0], 2)
                    self.entradas['B'] = int(linhas[1], 2)
                else:   # caso seja decimal e não binário
                    self.entradas['A'] = int(linhas[0])
                    self.entradas['B'] = int(linhas[1])

            else:
                print(f"Arquivo '{nome_arquivo}' não contém as entradas necessárias. Resolva esse problema.")
                self.entradas = {'A':0, 'B':0}

            return self.entradas
        
        
        # erro de A e B não encontrados
        except FileNotFoundError:
            print("Arquivo '{nome_arquivo}' não encontrado ou não existe. Usando A e B = 0.")
            self.entradas = {'A':0, 'B':0}
            return self.entradas
        
        # erro na leitura do arquivo
        except Exception as e:
            print(f"Erro '{e}' ao ler as entradas")
            self.entradas = {'A':0, 'B':0}
            return self.entradas



    def escrever_saida(self, nome_arquivo, linhas):

        """
        Escreve o arquivo de saída com as respostas
        
        Args:
            nome_arquivo (str): nome do arquivo .txt
            linhas (list): lista de strings com a escrita
            
        Returns:
            bool: true se conseguir escrever o arquivo, false se houver algum erro
        """
        
        try:

            with open(nome_arquivo, 'w', encoding='utf-8') as arquivo:
                arquivo.write('\n'.join(linhas))  # escreve o conteúdo de 'linhas' com uma quebra de linha entre cada escrita
            return True


        # erro na criação do arquivo
        except Exception as e:
            print(f"Erro '{e}' ao criar o arquivo de saída. Resolva esse problema.")
            return False


    
    def ler_entrada_usuario(self):

        """
        Lê as entradas A e B de maneira interativa
        
        Returns:
            tupla: tupla com A e B (A, B)
        """

        print("---- Configuração das Entradas A e B ----")

        try:

            a_input = input("Digite o valor de A em decimal: ")
            b_input = input("Digite o valor de B em decimal: ")

            A = int(a_input) & 0xFFFFFFFF
            B = int(b_input) & 0xFFFFFFFF
            
            return A, B
        

        # erro de valor inválido
        except ValueError:
            print("Entrada inválida. Usando A e B = 0.")
            return 0, 0



    def validar_instrucao(self, instrucao_str):

        """
        Valida a instrução binária do arquivo 

        Args:
            instrucao_str (str): string com 0s e 1s

        Returns:
            bool: true se for válido, false se inválido       
        """

        # verifica se é uma string
        if not isinstance(instrucao_str, str):
            return False
        
        # verifica se o comprimento tá correto
        if len(instrucao_str) != 6:
            return False
        
        # verifica se só tem 0 e 1
        if not all(c in '01' for c in instrucao_str):
            return False
        
        return True
    


    def validar_programa(self):

        """
        Valida todas as intruções do programa até agora

        Returns:
            bool: true se todas foram válidas, false se deu alguma invalidez
        """

        # verifica se as instruções são válidas e diz a linha se deu algum problema
        for i, instrucao in enumerate(self.programa):
            if not self.validar_instrucao(instrucao):
                print(f"Foi notado uma instrução inválida na linha {i+1}: '{instrucao}' ")
                return False
        return True



# ========== FUNÇÃO AUXILIAR ==========

def formatar_saida(PC, IR, A, B, S, carry):

    """
    Formata a saída para o arquivo de saída

    Args:
        PC(int): contador do programa
        IR(str): instrução binária
        A(int): valor de A
        B(int): valor de B
        S(int): resultado da ULA
        carry(int): carry-out

    Returns:
        list: lista de strings já formatadinhas direitinhas
    """

    from ula import formatar_binario # importado de outro arquivo

    saida = []
    saida.append(f"Ciclo {PC}")
    saida.append("")
    saida.append(f"PC = {PC}")
    saida.append(f"IR = {IR}")
    saida.append(f"B = {formatar_binario(B)}")
    saida.append(f"A = {formatar_binario(A)}")
    saida.append(f"S = {formatar_binario(S)}")
    saida.append(f"Carry Out = {carry}")
    saida.append(f"=" * 60)

    return saida