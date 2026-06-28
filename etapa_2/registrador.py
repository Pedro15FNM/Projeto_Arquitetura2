"""
=================================================================
    Registradores da Mic-1
    Responsável por gerenciar todos os registradores do sistema.
=================================================================
"""

import os

class Registradores:
    """ Gerencia os 10 registradores da Mic 1"""

    def __init__(self):
        # inicializa os registradores com valor default 0

        # registradores 32 bits
        self.H = 0          # entrada do A   
        self.OPC = 0        # código das operações 
        self.TOS = 0        # todo da pilha (copia)
        self.CPP = 0        # ponteiro para constante pool
        self.LV = 0         # base do quadro local
        self.SP = 0         # ponteiro da pilha
        self.PC = 0         # contador 
        self.MDR = 0        # dado de memória
        self.MAR = 0        # endereço de memória

        # registrador 8 bits
        self.MBR = 0        # buffer de memória

    def carregar_estado(self, arquivo: str) -> None:
        # carrega o estado dos registradores de um arquivo

        with open(arquivo, 'r') as f:
            for linha in f:
                if '=' in linha:
                    nome, valor = linha.strip().split('=')
                    nome = nome.strip().upper()
                    valor = int(valor.strip(), 0)

                    if hasattr(self, nome):
                        setattr(self, nome, valor)
                    elif nome == 'MBR':
                        self.MBR = valor & 0xFF
                    else:
                        print(f"Aviso: registrador '{nome}' não reconhecido")


    def estender_mbr_com_sinal(self) -> int:
        """
            estende MBR (8 bits) para 32 bits com sinal.
            se bit 7 = 1 → preenche com 1s (negativo)
            se bit 7 = 0 → preenche com 0s (positivo)
        """

        if self.MBR & 0x80: # bit 7 -> 1
            return self.MBR | 0xFFFFFF00
        else:               # bit 7 -> 0
            return self.MBR & 0x000000FF

    def estender_mbr_zero(self) -> int:
        """ estender MBR para 32 bits com 0"""
        return self.MBR & 0x000000FF
    
    def para_dict(self) -> dict:
        """ retorna todos os registradores como dicionário"""

        return{
            'H': self.H,
            'OPC': self.OPC,
            'TOS': self.TOS,
            'CPP': self.CPP,
            'LV': self.LV,     
            'SP': self.SP,         
            'PC': self.PC,         
            'MDR': self.MDR,      
            'MAR': self.MAR,
            'MBR': self.MBR
        }

    def formatar_registradores(self) -> list[str]:
        """ retorna lista de strings formatadas para o log"""

        ordem = ['MAR', 'MDR', 'PC', 'MBR', 'SP', 'LV', 'CPP', 'TOS', 'OPC', 'H']
        resultado = []

        for nome in ordem:
            valor = getattr(self, nome)
            if nome == 'MBR':
                resultado.append(f"{nome.lower()} = {format(valor, '08b')}")
            else:
                resultado.append(f"{nome.lower()} = {format(valor, '032b')}")
        return resultado
    
    def clonar(self) -> 'Registradores':
        """ cria uma cópia do estado atual dos registradores"""

        import copy
        return copy.deepcopy(self)