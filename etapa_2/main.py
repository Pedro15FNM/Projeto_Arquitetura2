import os

"""
=============================================================================
  SIMULADOR MIC-1 - ETAPA 2 (TAREFA 2)
=============================================================================
"""

# =============================================================================
# 1. CLASSE REGISTRADORES (Baseada no código fornecido pelo usuário)
# =============================================================================
class Registradores:
    """ Gerencia os 10 registradores da Mic-1 """

    def __init__(self):
        # registradores 32 bits
        self.H = 0          # entrada do A   
        self.OPC = 0        # código das operações 
        self.TOS = 0        # topo da pilha
        self.CPP = 0        # ponteiro para constante pool
        self.LV = 0         # base do quadro local
        self.SP = 0         # ponteiro da pilha
        self.PC = 0         # contador de programa
        self.MDR = 0        # dado de memória
        self.MAR = 0        # endereço de memória

        # registrador 8 bits
        self.MBR = 0        # buffer de memória

    def carregar_estado(self, arquivo: str) -> None:
        if not os.path.exists(arquivo):
            print(f"Aviso: Arquivo de registradores '{arquivo}' não encontrado.")
            return

        with open(arquivo, 'r', encoding='utf-8') as f:
            for linha in f:
                linha = linha.split('#')[0].strip() # Ignora comentários
                if '=' in linha:
                    nome, valor = linha.strip().split('=')
                    nome = nome.strip().upper()
                    valor = int(valor.strip(), 2) # Lê em binário

                    if hasattr(self, nome):
                        if nome == 'MBR':
                            setattr(self, nome, valor & 0xFF)
                        else:
                            setattr(self, nome, valor & 0xFFFFFFFF)
                    else:
                        print(f"Aviso: registrador '{nome}' não reconhecido")

    def estender_mbr_com_sinal(self) -> int:
        """ Estende MBR (8 bits) para 32 bits com sinal. """
        if self.MBR & 0x80: # Se bit 7 for 1 (negativo)
            return (self.MBR | 0xFFFFFF00) & 0xFFFFFFFF
        else:               # Se bit 7 for 0 (positivo)
            return self.MBR & 0x000000FF

    def estender_mbr_zero(self) -> int:
        """ Estende MBR para 32 bits com 0 (MBRU). """
        return self.MBR & 0x000000FF
    
    def formatar_registradores(self) -> str:
        """ Retorna string única formatada para o log da Etapa 2 """
        ordem = ['H', 'OPC', 'TOS', 'CPP', 'LV', 'SP', 'PC', 'MDR', 'MAR', 'MBR']
        resultado = []
        for nome in ordem:
            valor = getattr(self, nome)
            if nome == 'MBR':
                resultado.append(f"{nome}={format(valor, '08b')}")
            else:
                resultado.append(f"{nome}={format(valor, '032b')}")
        return " | ".join(resultado)


# =============================================================================
# 2. NÚCLEO DA ULA DE 32 BITS
# =============================================================================
def full_adder_1bit(a: int, b: int, cin: int) -> tuple[int, int]:
    s = a ^ b ^ cin
    cout = (a & b) | (cin & (a ^ b))
    return s, cout

def decode_operation(f0: int, f1: int) -> str:
    return {(0,0):"AND", (0,1):"OR", (1,0):"NOT_B", (1,1):"ADD"}[(f0, f1)]

def ula_32bit_core(f0: int, f1: int, ena: int, enb: int, inva: int, inc: int, a: int, b: int) -> tuple[int, int]:
    op = decode_operation(f0, f1)
    carry = inc
    s_val = 0

    for i in range(32):
        a_en = ((a >> i) & 1) & ena
        b_en = ((b >> i) & 1) & enb
        a_inv = a_en ^ inva
        
        if op == "AND":
            s_bit, c_out = full_adder_1bit(a_inv & b_en, 0, 0)
        elif op == "OR":
            s_bit, c_out = full_adder_1bit(a_inv | b_en, 0, 0)
        elif op == "NOT_B":
            s_bit, c_out = full_adder_1bit(b_en ^ 1, 0, 0)
        else: # ADD
            s_bit, c_out = full_adder_1bit(a_inv, b_en, carry)

        s_val |= (s_bit << i)
        carry = c_out

    return s_val & 0xFFFFFFFF, carry

def shifter_32bit(s: int, sll8: int, sra1: int) -> int:
    if sll8:
        return (s << 8) & 0xFFFFFFFF
    elif sra1:
        sign_bit = s & 0x80000000
        return ((s >> 1) | sign_bit) & 0xFFFFFFFF
    return s & 0xFFFFFFFF


# =============================================================================
# 3. CAMINHO DE DADOS (Mic-1)
# =============================================================================
class Mic1Datapath:
    def __init__(self):
        self.regs = Registradores()
        self.flags = {'N': 0, 'Z': 0, 'Vai_um': 0}

    def decode_barramento_b(self, bits_4: int) -> tuple[int, str]:
        """ Implementa a tabela de decodificação da Tarefa 2 para o Barramento B """
        decodificacao = {
            0: 'MDR', 1: 'PC', 2: 'MBR', 3: 'MBRU', 
            4: 'SP', 5: 'LV', 6: 'CPP', 7: 'TOS', 8: 'OPC'
        }
        nome = decodificacao.get(bits_4, "NENHUM")
        
        if nome == 'MBR':
            return self.regs.estender_mbr_com_sinal(), nome
        elif nome == 'MBRU':
            return self.regs.estender_mbr_zero(), nome
        elif nome != "NENHUM":
            return getattr(self.regs, nome), nome
        return 0, nome

    def executar_ciclo(self, ir: str) -> list[str]:
        # Limpa espaços em branco para garantir que o tamanho seja verificado estritamente sobre os bits
        ir = ir.replace(" ", "")
        
        if len(ir) != 21:
            raise ValueError(f"Instrução inválida. Esperado 21 bits, recebido {len(ir)} bits: '{ir}'")
            
        log = []
        
        # O PDF exige: registradores no INÍCIO
        estado_inicial = self.regs.formatar_registradores()

        # Parsing da instrução de 21 bits
        ula_ctrl = ir[0:8]
        bus_c_ctrl = ir[8:17]
        bus_b_ctrl = ir[17:21]

        # 1. Barramento B (Leitura)
        val_b, nome_b = self.decode_barramento_b(int(bus_b_ctrl, 2))
        
        # 2. ULA (A = H)
        val_a = self.regs.H
        sll8, sra1, f0, f1, ena, enb, inva, inc = [int(bit) for bit in ula_ctrl]
        
        s_raw, carry = ula_32bit_core(f0, f1, ena, enb, inva, inc, val_a, val_b)
        saida_sd = shifter_32bit(s_raw, sll8, sra1)

        # Atualiza Flags (sobre os 32 bits deslocados)
        self.flags['N'] = (saida_sd >> 31) & 1
        self.flags['Z'] = 1 if saida_sd == 0 else 0
        self.flags['Vai_um'] = carry

        # 3. Barramento C (Escrita) - Ordem do PDF: 8=H ... 0=MAR
        nomes_bus_c = ['MAR', 'MDR', 'PC', 'SP', 'LV', 'CPP', 'TOS', 'OPC', 'H']
        bits_c_int = int(bus_c_ctrl, 2)
        regs_escritos = []

        for i in range(9):
            if (bits_c_int >> i) & 1:
                nome_reg = nomes_bus_c[i]
                if nome_reg == 'MBR':
                    setattr(self.regs, nome_reg, saida_sd & 0xFF)
                else:
                    setattr(self.regs, nome_reg, saida_sd)
                regs_escritos.append(nome_reg)

        if not regs_escritos:
            regs_escritos.append("NENHUM")

        # O PDF exige: registradores no FIM
        estado_final = self.regs.formatar_registradores()

        # --- LOG CONFORME EXIGIDO PELO PDF (Pág 6) ---
        log.append(f"IR (Instrução)        : {ir}")
        log.append(f"Regs. Início          : {estado_inicial}")
        log.append(f"Comanda Barramento B  : {nome_b}")
        log.append(f"Escreve Barramento C  : {', '.join(regs_escritos)}")
        log.append(f"Flags                 : N={self.flags['N']} | Z={self.flags['Z']} | Vai-um={self.flags['Vai_um']}")
        log.append(f"Regs. Fim             : {estado_final}")
        log.append("-" * 100)

        return log

# =============================================================================
# 4. EXECUÇÃO
# =============================================================================
def criar_arquivos_exemplo():
    arq_regs = 'registradores_etapa2_tarefa2.txt'
    if not os.path.exists(arq_regs):
        with open(arq_regs, 'w', encoding='utf-8') as f:
            f.write("H   = 00000000000000000000000000000000\n")
            f.write("MDR = 00000000000000000000000000000101\n")
            f.write("LV  = 00000000000000000000000000001010\n")
            f.write("MBR = 00000000\n")

    arq_prog = 'programa_etapa2_tarefa2.txt'
    if not os.path.exists(arq_prog):
        with open(arq_prog, 'w', encoding='utf-8') as f:
            f.write("001101001010000000000 # H = MDR e TOS = MDR\n")
            f.write("001111000000000100100 # MDR = H + LV\n")

def main():
    criar_arquivos_exemplo()
    
    arq_prog = 'programa_etapa2_tarefa2.txt'
    arq_regs = 'registradores_etapa2_tarefa2.txt'
    arq_saida = 'saida_etapa2_tarefa2.txt'

    # Carrega as instruções limpando comentários em linha de forma segura
    instrucoes = []
    if os.path.exists(arq_prog):
        with open(arq_prog, 'r', encoding='utf-8') as f:
            for linha in f:
                linha_limpa = linha.split('#')[0].strip()
                if linha_limpa:
                    instrucoes.append(linha_limpa)

    cpu = Mic1Datapath()
    cpu.regs.carregar_estado(arq_regs)

    log_completo = ["="*100, " LOG DE EXECUÇÃO - MIC-1 (Etapa 2 - Tarefa 2)", "="*100]

    for i, inst in enumerate(instrucoes):
        log_completo.append(f"--- CICLO {i+1} ---")
        log_completo.extend(cpu.executar_ciclo(inst))

    with open(arq_saida, 'w', encoding='utf-8') as f:
        f.write("\n".join(log_completo))
    
    print(f"Execução concluída! Log gravado em '{arq_saida}'.")

if __name__ == '__main__':
    main()
