"""
    Teste_memoria.PY - testes do arquivo de Memoria.PY
"""

import unittest
import os
import tempfile
from memoria import GerenciadorArquivos, formatar_saida

class TesteGerenciadorArquivos(unittest.TestCase):

    def setUp(self):

        """Configuração antes de iniciar os testes"""

    self.ger = GerenciadorArquivos()

    # cria um arquivo temporário para ser usado nos testes
    self.temp_arquivo = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
    self.temp_arquivo.write("111110 \n 111100 \n 110101 \n")
    self.temp_arquivo.close()



    def limpar(self):

        """"Limpeza após cada teste"""

        os.unlink(self.temp_arquivo.name)  # remove o arquivo temporário

    

    def teste_ler_programa(self):

        """Testa a leitura do programa"""

        programa = self.ger.ler_programa(self.temp_arquivo.name)

        self.assertEqual(len(programa), 3)
        self.assertEqual(programa[0], "111110")
        self.assertEqual(programa[1], "111100")
        self.assertEqual(programa[2], "110101")



    def teste_arquivo_nao_encontrado(self):

        """Testa leitura de arquivo não encontrado/seja inexistente"""

        programa = self.ger.ler_programa("arquivo_inexistente.txt")  # tenta ler o arquivo não existente
        self.assertEqual(programa, [])  # tem que retornar vazio

    

    def teste_validar_instrucao(self):

        """Valida as instruções"""

        # válidas
        self.assertTrue(self.ger.validar_instrucao("111100"))
        self.assertTrue(self.ger.validar_instrucao("000000"))
        self.assertTrue(self.ger.validar_instrucao("111111"))

        # inválidas
        self.assertFalse(self.ger.validar_instrucao("11110"))  # só 5 bits
        self.assertFalse(self.ger.validar_instrucao("0000010"))  # 7 bits
        self.assertFalse(self.ger.validar_instrucao("1v1111"))  # caractere inválido
        self.assertFalse(self.ger.validar_instrucao(""))  # vazio
        self.assertFalse(self.ger.validar_instrucao(None))  # none



    def teste_formatar_saida(self):

        """Valida a formatação do arquivo de saída"""

        saida = formatar_saida(1, '111100', 0xFFFFFFFF, 0x00000001, 0, 1)

        self.assertIsInstance(saida, list)
        self.assertTrue(len(saida) >= 8)
        self.assertTrue(any('Cycle 1' in s for s in saida))
        self.assertTrue(any('IR = 111100' in s for s in saida))
        self.assertTrue(any('Carry Out = 1' in s for s in saida))

if __name__ == '__main__':
    unittest.main()