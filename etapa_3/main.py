import os
import sys

"""
=============================================================================
  ETAPA 3 COMPLETA 
=============================================================================
"""


# =============================================================================
# CONSTANTES
# =============================================================================

WORD_MASK = 0xFFFFFFFF
WORD_SIGN = 0x80000000
MEM_SIZE = 16  # Aumentado para 16

# Mapeamento Barramento B
BARR_B_MAP = {
    0b0000: "MDR",  0b0001: "PC",   0b0010: "MBR",   0b0011: "MBRU",
    0b0100: "SP",   0b0101: "LV",   0b0110: "CPP",   0b0111: "TOS",
    0b1000: "OPC",  0b1001: "H",
}

# =============================================================================
# FUNÇÃO AUXILIAR PARA CONVERTER BINÁRIO
# =============================================================================

def converter_binario_para_int(valor_str: str) -> int:
    """
    Converte uma string binária para inteiro de 32 bits.
    Remove espaços, zeros à esquerda e caracteres especiais.
    """
    # Remove espaços e caracteres invisíveis
    valor_str = valor_str.strip()
    
    # Remove caracteres não-binários (exceto 0 e 1)
    valor_str = ''.join(c for c in valor_str if c in '01')
    
    if not valor_str:
        return 0
    
    # Converte para inteiro (base 2) e mantém 32 bits
    try:
        return int(valor_str, 2) & WORD_MASK
    except ValueError:
        return 0


# =============================================================================
# ULA DE 32 BITS (com 8 bits de controle)
# =============================================================================

def full_adder(a, b, cin):
    return a ^ b ^ cin, (a & b) | (cin & (a ^ b))

def ula_32(sll8, sra1, f0, f1, ena, enb, inva, inc, a, b):
    """ULA de 32 bits com 8 bits de controle."""
    
    # Determina operação
    op_map = {(0, 0): "AND", (0, 1): "OR", (1, 0): "NOT_B", (1, 1): "ADD"}
    op = op_map[(f0, f1)]
    
    carry = 0
    s_val = 0
    
    # Loop bit a bit
    for i in range(32):
        a_bit = (a >> i) & 1
        b_bit = (b >> i) & 1
        
        cin = inc if i == 0 else carry

        a_en = a_bit & ena
        b_en = b_bit & enb
        a_inv = a_en ^ inva
        
        if op == "AND":
            s_bit, c_out = full_adder(a_inv & b_en, 0, 0)
        elif op == "OR":
            s_bit, c_out = full_adder(a_inv | b_en, 0, 0)
        elif op == "NOT_B":
            s_bit, c_out = full_adder(b_en ^ 1, 0, 0)
        else:  # ADD
            s_bit, c_out = full_adder(a_inv, b_en, cin)
        
        s_val |= (s_bit << i)
        carry = c_out
    
    s_val &= WORD_MASK
    
    # Deslocamentos
    if sll8 and sra1:
        raise ValueError("SLL8 e SRA1 ativos simultaneamente!")
    elif sll8:
        sd = (s_val << 8) & WORD_MASK
    elif sra1:
        sd = ((s_val >> 1) | (s_val & WORD_SIGN)) & WORD_MASK
    else:
        sd = s_val
    
    # Flags
    n = (sd >> 31) & 1
    z = 1 if sd == 0 else 0
    
    return {
        "S_raw": s_val,
        "Sd": sd,
        "vai_um": carry,
        "N": n,
        "Z": z,
        "op": op
    }

# =============================================================================
# REGISTRADORES
# =============================================================================

class Registradores:
    NAMES = ["H", "OPC", "TOS", "CPP", "LV", "SP", "PC", "MDR", "MAR", "MBR"]
    
    def __init__(self):
        for n in self.NAMES:
            setattr(self, n, 0)
        self.MBR = 0
    
    def get(self, name):
        if name == "MBRU":
            return self.MBR & 0x000000FF
        elif name == "MBR":
            if self.MBR & 0x80:
                return self.MBR | 0xFFFFFF00
            else:
                return self.MBR & 0x000000FF
        return getattr(self, name, 0)
    
    def set(self, name, value):
        if name == "MBR":
            self.MBR = value & 0xFF
        else:
            setattr(self, name, value & WORD_MASK)
    
    def snapshot(self):
        return {n: self.get(n) for n in self.NAMES}
    
    def formatar(self):
        ordem = ["MAR", "MDR", "PC", "MBR", "SP", "LV", "CPP", "TOS", "OPC", "H"]
        resultado = []
        
        # Cabeçalho da tabela de registradores
        resultado.append(f"  {'REG':<3} | {'HEX':<10} | {'DEC':<5} | BINÁRIO")
        resultado.append("  " + "-"*65)
        
        for nome in ordem:
            valor = self.get(nome)
            if nome == "MBR":
                bin_str = format(valor, '08b')
                resultado.append(f"  {nome:<3} | 0x{valor:02X}{' '*8} | {valor:<5} | {bin_str}")
            else:
                bin_str = f"{valor:032b}"
                # Agrupa os bits de 8 em 8 para facilitar a leitura
                bin_fmt = f"{bin_str[:8]} {bin_str[8:16]} {bin_str[16:24]} {bin_str[24:]}"
                resultado.append(f"  {nome:<3} | 0x{valor:08X} | {valor:<5} | {bin_fmt}")
        return "\n".join(resultado)

# =============================================================================
# FUNÇÃO PARA CARREGAR REGISTRADORES
# =============================================================================

def carregar_registradores(regs, arquivo):
    """Carrega o estado dos registradores de um arquivo."""
    if not os.path.exists(arquivo):
        print(f"Aviso: Arquivo de registradores '{arquivo}' não encontrado.")
        return
    
    print(f"Carregando registradores de: {arquivo}")
    
    with open(arquivo, 'r', encoding='utf-8') as f:
        for num_linha, linha in enumerate(f, 1):
            linha = linha.split('#')[0].strip()
            if not linha:
                continue
                
            if '=' not in linha:
                print(f"Aviso: Linha {num_linha} ignorada (formato inválido): '{linha}'")
                continue
                
            nome, valor_str = linha.split('=')
            nome = nome.strip().upper()
            
            # Converte o valor binário
            valor_int = converter_binario_para_int(valor_str)
            
            if nome == 'MBR':
                regs.MBR = valor_int & 0xFF
                print(f"  {nome} = {format(regs.MBR, '08b')}")
            elif nome in regs.NAMES:
                setattr(regs, nome, valor_int)
                print(f"  {nome} = {format(valor_int, '032b')}")
            else:
                print(f"Aviso: Registrador '{nome}' não reconhecido")

# =============================================================================
# MEMÓRIA
# =============================================================================

class Memoria:
    def __init__(self, size=MEM_SIZE):
        self.size = size
        self.dados = [0] * size
    
    def ler(self, endereco):
        if not 0 <= endereco < self.size:
            raise IndexError(f"Endereço inválido: {endereco}")
        return self.dados[endereco]
    
    def escrever(self, endereco, valor):
        if not 0 <= endereco < self.size:
            raise IndexError(f"Endereço inválido: {endereco}")
        self.dados[endereco] = valor & WORD_MASK
    
    def carregar(self, arquivo):
        if os.path.exists(arquivo):
            with open(arquivo, 'r') as f:
                for i, linha in enumerate(f):
                    if i >= self.size:
                        break
                    linha = linha.split('#')[0].strip()
                    if linha:
                        self.dados[i] = converter_binario_para_int(linha)
    
    def formatar(self):
        linhas = []
        linhas.append(f"  {'END':<5} | {'HEX':<10} | {'DEC':<5} | BINÁRIO")
        linhas.append("  " + "-"*65)
        
        for i, v in enumerate(self.dados):
            # Mostra apenas as 11 primeiras posições ou qualquer endereço diferente de zero
            if i <= 10 or v != 0:
                bin_str = f"{v:032b}"
                bin_fmt = f"{bin_str[:8]} {bin_str[8:16]} {bin_str[16:24]} {bin_str[24:]}"
                linhas.append(f"  [{i:02d}]  | 0x{v:08X} | {v:<5} | {bin_fmt}")
            elif i == 11 and len(self.dados) > 11:
                linhas.append("  ...   | (endereços vazios ocultados)")
                
        return "\n".join(linhas)

# =============================================================================
# MIC-1 DATAPATH
# =============================================================================

class Mic1Datapath:
    def __init__(self):
        self.regs = Registradores()
        self.memoria = Memoria()
    
    def ler_barramento_b(self, barramento_b):
        codigo = int(barramento_b, 2)
        nome = BARR_B_MAP.get(codigo, f"DESCONHECIDO({codigo:04b})")
        valor = self.regs.get(nome)
        return nome, valor
    
    def escrever_barramento_c(self, barramento_c, resultado):
        mapa = [
            ('H', 0), ('OPC', 1), ('TOS', 2), ('CPP', 3),
            ('LV', 4), ('SP', 5), ('PC', 6), ('MDR', 7), ('MAR', 8)
        ]
        escritos = []
        for i, (nome, pos) in enumerate(mapa):
            if barramento_c[i] == '1':
                if nome != 'MBR':
                    self.regs.set(nome, resultado)
                    escritos.append(nome)
        return escritos
    
    def executar_microinstrucao(self, ir):
        ir = ir.replace(" ", "").strip()
        
        if len(ir) != 23:
            raise ValueError(f"Microinstrução inválida ({len(ir)} bits): {ir}")
        
        log = []
        
        estado_inicial = self.regs.formatar()
        memoria_inicial = self.memoria.formatar()
        
        ula_ctrl = ir[0:8]
        barramento_c = ir[8:17]
        memoria_ctrl = ir[17:19]
        barramento_b = ir[19:23]
        
        nome_b, valor_b = self.ler_barramento_b(barramento_b)
        valor_a = self.regs.get("H")
        
        sll8 = int(ula_ctrl[0])
        sra1 = int(ula_ctrl[1])
        f0 = int(ula_ctrl[2])
        f1 = int(ula_ctrl[3])
        ena = int(ula_ctrl[4])
        enb = int(ula_ctrl[5])
        inva = int(ula_ctrl[6])
        inc = int(ula_ctrl[7])
        
        resultado_ula = ula_32(sll8, sra1, f0, f1, ena, enb, inva, inc, valor_a, valor_b)
        resultado = resultado_ula["Sd"]
        
        escritos = self.escrever_barramento_c(barramento_c, resultado)
        
        write_bit = memoria_ctrl[0]
        read_bit = memoria_ctrl[1]
        
        operacao = "NENHUMA"
        if write_bit == '1' and read_bit == '1':
            raise ValueError("WRITE e READ ativos simultaneamente!")
        elif write_bit == '1':
            endereco = self.regs.get("MAR")
            if 0 <= endereco < self.memoria.size:
                self.memoria.escrever(endereco, self.regs.get("MDR"))
            operacao = "WRITE"
        elif read_bit == '1':
            endereco = self.regs.get("MAR")
            if 0 <= endereco < self.memoria.size:
                self.regs.set("MDR", self.memoria.ler(endereco))
            operacao = "READ"
        
        estado_final = self.regs.formatar()
        memoria_final = self.memoria.formatar()
        
        # Formatação do Log do Ciclo
        log.append("╭" + "─" * 85 + "╮")
        log.append(f"│ IR: {ir[:8]} {ir[8:17]} {ir[17:19]} {ir[19:]} {'':<39} │")
        log.append("├" + "─" * 85 + "┤")
        
        log.append("  [ ESTADO ANTES ]")
        log.append(estado_inicial)
        log.append("")
        
        # Destaca o que aconteceu no ciclo
        log.append("  [ AÇÃO DO CICLO ]")
        log.append(f"  ▸ Barramento B : {nome_b}")
        log.append(f"  ▸ ULA          : {resultado_ula['op']} → Resultado= {resultado} (0x{resultado:08X})")
        log.append(f"  ▸ Flags        : N={resultado_ula['N']}  Z={resultado_ula['Z']}  Vai-um={resultado_ula['vai_um']}")
        log.append(f"  ▸ Barramento C : {', '.join(escritos) if escritos else 'NENHUM'}")
        log.append(f"  ▸ Memória      : {operacao}")
        log.append("")
        
        log.append("  [ ESTADO DEPOIS ]")
        log.append(estado_final)
        log.append("")
        if operacao != "NENHUMA":
            log.append("  [ ESTADO DA MEMÓRIA ATUALIZADO ]")
            log.append(memoria_final)
            log.append("")
            
        return log
    
    def estado_memoria(self):
        return self.memoria.formatar()

# =============================================================================
# INTERPRETADOR IJVM
# =============================================================================

def traduzir_iload(x):
    micros = []
    
    # 1. H = LV
    micros.append("00110100" + "100000000" + "00" + "0101")
    
    # 2. H = H + 1 
    for _ in range(x):
        micros.append("00111101" + "100000000" + "00" + "1001")
    
    # 3. MAR = H
    micros.append("00110100" + "000000001" + "01" + "1001")
    
    # 4. MAR = SP = SP + 1
    micros.append("00111101" + "000001001" + "10" + "0100")
    
    # 5. TOS = MDR
    micros.append("00110100" + "001000000" + "00" + "0000")
    
    return micros

def traduzir_dup():
    micros = []
    
    # 1. MAR = SP; rd
    # ULA: S = SP (B=SP)
    # C: MAR (bit 8) → 000000001
    # MEM: READ → 01
    # B: SP → 0100
    micros.append("00110100" + "000000001" + "01" + "0100")
    
    # 2. SP = SP + 1; MAR = SP; wr
    # ULA: S = SP + 1
    # C: SP (bit 5), MAR (bit 8) → 000001001
    # MEM: WRITE → 10
    # B: SP → 0100
    micros.append("00111101" + "000001001" + "10" + "0100")
    
    # 3. TOS = MDR
    # ULA: S = MDR (B=MDR)
    # C: TOS (bit 6) → 001000000
    # MEM: NENHUMA → 00
    # B: MDR → 0000
    micros.append("00110100" + "001000000" + "00" + "0000")
    
    return micros

def traduzir_bipush(byte):
    micros = []
    
    # 1. SP = SP + 1; MAR = SP; wr
    micros.append("00111101" + "000001001" + "10" + "0100")
    
    # 2. TOS = byte (coloca o byte diretamente em TOS)
    byte_bits = format(byte & 0xFF, '08b')
    # C: TOS (bit 6) → 001000000
    # O byte está nos 8 primeiros bits, a ULA é o byte
    # A ULA deve produzir 0 (ENA=0, ENB=0, INVA=0, INC=0)
    # Mas o byte é a ULA, então... 
    micros.append(byte_bits + "001000000" + "00" + "0000")
    
    return micros

def interpretar_ijvm(arquivo):
    if not os.path.exists(arquivo):
        raise FileNotFoundError(f"Arquivo IJVM não encontrado: {arquivo}")
    
    micros = []
    with open(arquivo, 'r') as f:
        for linha in f:
            linha = linha.split('#')[0].strip()
            if not linha:
                continue
            partes = linha.split()
            op = partes[0].upper()
            
            if op == 'ILOAD' and len(partes) > 1:
                micros.extend(traduzir_iload(int(partes[1])))
            elif op == 'DUP':
                micros.extend(traduzir_dup())
            elif op == 'BIPUSH' and len(partes) > 1:
                byte_str = partes[1]
                if len(byte_str) == 8 and all(c in '01' for c in byte_str):
                    micros.extend(traduzir_bipush(int(byte_str, 2)))
                else:
                    micros.extend(traduzir_bipush(int(byte_str)))
            else:
                raise ValueError(f"Instrução IJVM desconhecida: '{linha}'")
    
    return micros

# =============================================================================
# EXECUÇÃO
# =============================================================================

def executar_programa(cpu, programa, mostrar_memoria_inicial=True):
    log = []
    
    if mostrar_memoria_inicial:
        log.append("=" * 90)
        log.append("ESTADO INICIAL DA MEMÓRIA")
        log.append(cpu.estado_memoria())
        log.append("")
        log.append("INÍCIO DO PROGRAMA")
        log.append("=" * 90)
    
    ciclo = 1
    for instrucao in programa:
        log.append(f"CICLO {ciclo}")
        log.extend(cpu.executar_microinstrucao(instrucao))
        ciclo += 1
    
    return log

# =============================================================================
# MAIN
# =============================================================================

def main():
    args = sys.argv[1:]
    
    if len(args) < 1:
        print("Uso:")
        print("  python main.py [microinstrucoes.txt] [registradores.txt] [saida.txt]")
        print("  python main.py [ijvm.txt] [registradores.txt] [saida.txt]")
        return
    
    arquivo = args[0]
    regs_file = args[1] if len(args) > 1 else None
    saida = args[2] if len(args) > 2 else "saida_etapa3.txt"
    
    # Verifica se é IJVM
    is_ijvm = False
    try:
        with open(arquivo, 'r') as f:
            conteudo = f.read().upper()
            is_ijvm = any(op in conteudo for op in ['BIPUSH', 'DUP', 'ILOAD'])
    except:
        pass
    
    cpu = Mic1Datapath()
    
    # Carrega registradores se existir
    if regs_file and os.path.exists(regs_file):
        carregar_registradores(cpu.regs, regs_file)
    elif os.path.exists('registradores.txt'):
        carregar_registradores(cpu.regs, 'registradores.txt')
    
    # Carrega dados iniciais se existir
    if os.path.exists('dados.txt'):
        print("Carregando memória de: dados.txt")
        cpu.memoria.carregar('dados.txt')
    
    if is_ijvm:
        print(f"Interpretando IJVM: {arquivo}")
        programa = interpretar_ijvm(arquivo)
        print(f"{len(programa)} microinstruções geradas")
    else:
        print(f"Carregando microinstruções: {arquivo}")
        with open(arquivo, 'r') as f:
            programa = [linha.strip() for linha in f if linha.strip()]
    
    log = executar_programa(cpu, programa)
    
    with open(saida, 'w', encoding='utf-8') as f:
        f.write('\n'.join(log))
    
    print(f"Execução concluída. Log salvo em '{saida}'.")

if __name__ == "__main__":
    main()
