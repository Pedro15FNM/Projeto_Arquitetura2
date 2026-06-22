# memoria.py - responsável por ler o arquivo de instruções e criar o arquivo de saída

import sys
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

            print("Arquivo '{nome_arquivo}' não encontrado ou não existe. Dê um jeito no arquivo.")
            return []
        
        # erro na leitura do arquivo
        except Exception as e:

            print("Erro '{e}' ao ler o arquivo '{nome_arquivo}'")
            return []