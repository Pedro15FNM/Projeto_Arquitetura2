"""
=============================================================================
  ULA DE 8 BITS — Mic-1  (Etapa 2 do Projeto de Arquitetura de Computadores)
=============================================================================

  Extensão da ULA de 1 bit da Etapa 1.
  A palavra de controle passa a ter 8 bits:

        SLL8  SRA1  F0  F1  ENA  ENB  INVA  INC
         X0    X1   X2  X3   X4   X5    X6   X7

  Novos sinais em relação à Etapa 1:
  ┌────────┬──────────────────────────────────────────────────────────────┐
  │ SLL8   │ Deslocamento lógico à ESQUERDA de 8 bits na saída Sd.        │
  │        │ O byte inferior é zerado; os 8 bits da saída S original      │
  │        │ passam a ocupar os 8 bits superiores.                        │
  │        │ (Aplicado APÓS o cálculo da ULA, sobre a saída S de 8 bits.) │
  ├────────┼──────────────────────────────────────────────────────────────┤
  │ SRA1   │ Deslocamento aritmético à DIREITA de 1 bit na saída Sd.      │
  │        │ O bit de sinal (MSB) é preservado (extensão de sinal).       │
  │        │ (Aplicado APÓS o cálculo da ULA, sobre a saída S de 8 bits.) │
  ├────────┼──────────────────────────────────────────────────────────────┤
  │ N      │ Flag: 1 se a saída deslocada Sd é NEGATIVA (MSB = 1).        │
  ├────────┼──────────────────────────────────────────────────────────────┤
  │ Z      │ Flag: 1 se a saída deslocada Sd é ZERO (todos os bits = 0).  │
  └────────┴──────────────────────────────────────────────────────────────┘

  Restrição da especificação:
    • SLL8 e SRA1 NUNCA são 1 ao mesmo tempo.
    • O deslocador atua DEPOIS da saída da ULA ser calculada.
    • As flags N e Z são calculadas sobre a saída DESLOCADA (Sd).

  Saídas da ULA (Etapa 2):
    Sd, Vai-um, N, Z

  Formato do arquivo de entrada (programa_etapa2_tarefa1.txt):
    Uma instrução por linha, 8 caracteres '0' ou '1' sem espaços.
    Opcionalmente seguido de comentário após '#'.
    Ex.:
      00110110   # ADD A+B (sem deslocamento)
      10110110   # ADD A+B com SLL8

  Formato do arquivo de log (saida_etapa2_tarefa1.txt):
    PC | IR       | A  | B  | Sd  | Vai-um | N | Z
    (uma linha por instrução executada)

  Uso:
    python ula_mic1_etapa2.py                         # usa arquivos padrão
    python ula_mic1_etapa2.py prog.txt saida.txt A B  # arquivos customizados
=============================================================================
"""

from __future__ import annotations
import sys
import os

# ─────────────────────────────────────────────────────────────────────────────
# Cores ANSI
# ─────────────────────────────────────────────────────────────────────────────
RST  = "\033[0m"
BOLD = "\033[1m"
CYN  = "\033[96m"
GRN  = "\033[92m"
YLW  = "\033[93m"
RED  = "\033[91m"
BLU  = "\033[94m"
GRY  = "\033[90m"
MAG  = "\033[95m"

def H(s):   return f"{BOLD}{CYN}{s}{RST}"
def G(s):   return f"{GRN}{s}{RST}"
def Y(s):   return f"{YLW}{s}{RST}"
def B(s):   return f"{BLU}{s}{RST}"
def D(s):   return f"{GRY}{s}{RST}"
def HL(s):  return f"{BOLD}{MAG}{s}{RST}"
def RD(s):  return f"{RED}{s}{RST}"

# ─────────────────────────────────────────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────────────────────────────────────────
BITS = 8          # largura de palavra da ULA
MASK = 0xFF       # máscara de 8 bits
MSB  = 0x80       # bit de sinal (bit 7)

# ─────────────────────────────────────────────────────────────────────────────
# Somador completo de 1 bit (reutilizado da Etapa 1)
# ─────────────────────────────────────────────────────────────────────────────

def full_adder_1bit(a: int, b: int, cin: int) -> tuple[int, int]:
    """
    Somador completo de 1 bit.
      S    = A XOR B XOR Cin
      Cout = (A AND B) OR (Cin AND (A XOR B))
    """
    s    = a ^ b ^ cin
    cout = (a & b) | (cin & (a ^ b))
    return s, cout


# ─────────────────────────────────────────────────────────────────────────────
# ULA de 8 bits — encadeia 8 somadores de 1 bit
# ─────────────────────────────────────────────────────────────────────────────

def decode_operation(f0: int, f1: int) -> str:
    """
    Decodificador F0/F1 → operação.
    Mesma tabela da Etapa 1:
      F1F0 = 00 → AND
      F1F0 = 01 → OR
      F1F0 = 10 → NOT_B
      F1F0 = 11 → ADD  (somador completo)
    
    Atenção: na palavra de controle, F0=X2 e F1=X3.
    O decodificador recebe (f0, f1) onde f0 é X2 e f1 é X3.
    """
    return {(0,0):"AND", (0,1):"OR", (1,0):"NOT_B", (1,1):"ADD"}[(f0, f1)]


def ula_8bit_core(
    f0: int, f1: int,
    ena: int, enb: int,
    inva: int, inc: int,
    a: int, b: int,
) -> tuple[int, int]:
    """
    Núcleo da ULA de 8 bits: encadeia 8 instâncias de ULA de 1 bit.

    Parâmetros
    ----------
    f0, f1  : seleção de operação
    ena     : habilita entrada A (inteiro 8 bits)
    enb     : habilita entrada B (inteiro 8 bits)
    inva    : inverte A bit a bit
    inc     : injeta carry-in = 1 no LSB
    a, b    : operandos inteiros de 8 bits (0..255)

    Retorna
    -------
    (S, vai_um)
      S        : resultado de 8 bits (unsigned)
      vai_um   : carry-out do MSB
    """
    op    = decode_operation(f0, f1)
    carry = inc          # INC injeta carry=1 apenas no bit 0 (LSB)
    s_val = 0

    for i in range(BITS):           # i=0 → LSB, i=7 → MSB
        # extrai o bit i de cada operando
        a_bit = (a >> i) & 1
        b_bit = (b >> i) & 1

        # ── Passo 1: ENA / ENB ──────────────────────────────────────────────
        # ENA/ENB são sinais de 1 bit que habilitam TODOS os bits de A ou B.
        # Se ENA=0, todos os bits de A são forçados a 0.
        a_en  = a_bit & ena
        b_en  = b_bit & enb

        # ── Passo 2: INVA ───────────────────────────────────────────────────
        # INVA=1 inverte todos os bits de A (XOR com 1 em cada bit)
        a_inv = a_en ^ inva

        # ── Passo 3: Vem-um ─────────────────────────────────────────────────
        # Para o bit 0: vem_um = carry (que já inclui INC)
        # Para bits > 0: vem_um = carry propagado do bit anterior
        vem_um = carry

        # ── Passo 4 + 5: Operação e Somador ─────────────────────────────────
        if op == "AND":
            logic_out = a_inv & b_en
            s_bit, c_out = full_adder_1bit(logic_out, 0, 0)
        elif op == "OR":
            logic_out = a_inv | b_en
            s_bit, c_out = full_adder_1bit(logic_out, 0, 0)
        elif op == "NOT_B":
            logic_out = b_en ^ 1
            s_bit, c_out = full_adder_1bit(logic_out, 0, 0)
        else:  # ADD
            logic_out = None
            s_bit, c_out = full_adder_1bit(a_inv, b_en, vem_um)

        # Acumula o bit de resultado
        s_val |= (s_bit << i)
        carry  = c_out

    return s_val & MASK, carry


# ─────────────────────────────────────────────────────────────────────────────
# Deslocador (shifter) — atua APÓS a saída da ULA
# ─────────────────────────────────────────────────────────────────────────────

def shifter(s: int, sll8: int, sra1: int) -> tuple[int, str]:
    """
    Aplica o deslocamento à saída S da ULA.

    SLL8=1 : deslocamento LÓGICO à esquerda de 8 bits.
              Como trabalhamos com 8 bits, SLL8 desloca S de um byte inteiro
              para a posição de byte superior — o resultado em 8 bits fica 0x00,
              mas em 16 bits seria (S << 8). Seguindo a spec (desloca S em 8
              bits), implementamos como: Sd = (S << 8) & 0xFFFF, ou seja,
              num contexto de 16 bits. Internamente guardamos 16 bits para
              exibição e calculamos flags sobre os 16 bits.

    SRA1=1 : deslocamento ARITMÉTICO à direita de 1 bit.
              O bit de sinal (bit 7 de S nos 8 bits) é preservado.
              Sd = (S >> 1) | (S & 0x80)   [mantém o MSB]

    SLL8 e SRA1 nunca são 1 ao mesmo tempo (restrição da spec).

    Retorna (Sd, descricao_da_operacao)
    """
    if sll8 and sra1:
        raise ValueError("SLL8 e SRA1 não podem ser 1 ao mesmo tempo.")

    if sll8:
        # Desloca 8 posições à esquerda: os bits de S vão para o byte alto.
        # Representamos em 16 bits para fidelidade ao circuito real.
        sd  = (s << 8) & 0xFFFF
        desc = f"SLL8: {s:#04x} << 8 = {sd:#06x}"
    elif sra1:
        # Deslocamento aritmético à direita: preserva o sinal (bit 7 de S).
        sign_bit = (s & MSB)           # isola o bit de sinal
        sd  = ((s >> 1) | sign_bit) & MASK
        desc = f"SRA1: {s:#04x} >> 1 (aritmético) = {sd:#04x}"
    else:
        sd   = s & MASK
        desc = "Sem deslocamento"

    return sd, desc


# ─────────────────────────────────────────────────────────────────────────────
# Flags N e Z
# ─────────────────────────────────────────────────────────────────────────────

def calc_flags(sd: int, sll8: int) -> tuple[int, int]:
    """
    Calcula as flags N (negativo) e Z (zero) sobre a saída deslocada Sd.

    Para SLL8=1, Sd tem 16 bits; para os demais casos, 8 bits.
    N = 1 se Sd < 0 (interpretado com sinal), ou seja, MSB = 1.
    Z = 1 se Sd == 0.
    """
    if sll8:
        # Sd em 16 bits: bit de sinal é o bit 15
        n_flag = (sd >> 15) & 1
    else:
        # Sd em 8 bits: bit de sinal é o bit 7
        n_flag = (sd >> 7) & 1

    z_flag = 1 if sd == 0 else 0
    return n_flag, z_flag


# ─────────────────────────────────────────────────────────────────────────────
# ULA completa (Etapa 2) — ponto de entrada por instrução
# ─────────────────────────────────────────────────────────────────────────────

def ula_etapa2(ir_str: str, a: int, b: int) -> dict:
    """
    Executa uma instrução completa da ULA de 8 bits (Etapa 2).

    Parâmetros
    ----------
    ir_str : string de 8 bits  "SLL8 SRA1 F0 F1 ENA ENB INVA INC"
    a, b   : operandos inteiros de 8 bits (0..255)

    Retorna dict com todos os sinais e resultados.
    """
    fields = parse_instruction_8bit(ir_str)

    sll8 = fields["SLL8"]
    sra1 = fields["SRA1"]
    f0   = fields["F0"]
    f1   = fields["F1"]
    ena  = fields["ENA"]
    enb  = fields["ENB"]
    inva = fields["INVA"]
    inc  = fields["INC"]

    # 1. Núcleo da ULA (8 bits encadeados)
    s_raw, vai_um = ula_8bit_core(f0, f1, ena, enb, inva, inc, a, b)

    # 2. Deslocador (atua sobre S, APÓS a ULA)
    sd, shift_desc = shifter(s_raw, sll8, sra1)

    # 3. Flags
    n_flag, z_flag = calc_flags(sd, sll8)

    return {
        # Campos de controle
        "sll8"       : sll8,
        "sra1"       : sra1,
        "f0"         : f0,
        "f1"         : f1,
        "ena"        : ena,
        "enb"        : enb,
        "inva"       : inva,
        "inc"        : inc,
        # Operandos
        "a"          : a,
        "b"          : b,
        # Resultados intermediários
        "op"         : decode_operation(f0, f1),
        "S_raw"      : s_raw,       # saída da ULA antes do deslocamento
        "vai_um"     : vai_um,      # carry-out do MSB
        "shift_desc" : shift_desc,  # descrição do deslocamento aplicado
        # Saídas finais
        "Sd"         : sd,          # saída deslocada
        "N"          : n_flag,      # flag negativo
        "Z"          : z_flag,      # flag zero
    }


# ─────────────────────────────────────────────────────────────────────────────
# Parser de instrução de 8 bits
# ─────────────────────────────────────────────────────────────────────────────

def parse_instruction_8bit(ir_str: str) -> dict:
    """
    Interpreta string de 8 bits como instrução da ULA (Etapa 2).

    Formato: SLL8 SRA1 F0 F1 ENA ENB INVA INC
              X0    X1  X2 X3  X4  X5   X6  X7
    """
    ir_str = ir_str.strip()
    if len(ir_str) != 8 or not all(c in "01" for c in ir_str):
        raise ValueError(
            f"Instrução inválida: '{ir_str}'. "
            f"Esperado: 8 caracteres '0' ou '1'."
        )
    b = [int(c) for c in ir_str]
    fields = {
        "SLL8": b[0],
        "SRA1": b[1],
        "F0"  : b[2],
        "F1"  : b[3],
        "ENA" : b[4],
        "ENB" : b[5],
        "INVA": b[6],
        "INC" : b[7],
    }
    if fields["SLL8"] and fields["SRA1"]:
        raise ValueError(
            f"Instrução inválida: SLL8=1 e SRA1=1 ao mesmo tempo em '{ir_str}'."
        )
    return fields


# ─────────────────────────────────────────────────────────────────────────────
# Leitura do arquivo de programa
# ─────────────────────────────────────────────────────────────────────────────

def load_program(path: str) -> list[str]:
    """
    Lê o arquivo .txt e retorna lista de strings de instrução (8 bits cada).
    Ignora linhas vazias e comentários (# ...).
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Arquivo não encontrado: '{path}'")
    instructions = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.split("#")[0].strip()
            if line:
                instructions.append(line)
    return instructions


# ─────────────────────────────────────────────────────────────────────────────
# Execução do programa e geração de log
# ─────────────────────────────────────────────────────────────────────────────

def run_program(
    instructions: list[str],
    a: int,
    b: int,
    log_path: str | None = None,
    verbose: bool = True,
):
    """
    Executa a sequência de instruções da ULA de 8 bits.

    Parâmetros
    ----------
    instructions  : lista de strings de 8 bits
    a, b          : operandos (inteiros 0..255), fixos para toda a execução
    log_path      : caminho do arquivo de log (None = não grava)
    verbose       : imprime trace detalhado de cada instrução
    """
    # Cabeçalho do log
    log_header = (
        f"{'PC':>3} | {'IR':^8} | {'A':^10} | {'B':^10} | "
        f"{'Sd':^10} | {'Vai-um':^6} | {'N':^1} | {'Z':^1}"
    )
    log_sep    = "-" * len(log_header)
    log_lines  = [log_header, log_sep]

    print(H("\n══════════════════════════════════════════════════════════════════"))
    print(H("  ULA Mic-1 Etapa 2 — Execução do Programa"))
    print(H("══════════════════════════════════════════════════════════════════"))
    print(f"  Operandos: A = {B(f'{a:08b}')} ({a:3d})   B = {B(f'{b:08b}')} ({b:3d})")
    print(f"  Total de instruções: {len(instructions)}")

    results = []
    for pc, ir_str in enumerate(instructions):
        try:
            r = ula_etapa2(ir_str, a, b)
        except ValueError as e:
            print(RD(f"\n  [PC={pc:03d}] ERRO: {e}"))
            continue

        if verbose:
            trace_instrucao(pc, ir_str, r)

        # Linha de log
        sd_str = f"{r['Sd']:#06x}" if r['sll8'] else f"{r['Sd']:#04x}"
        log_line = (
            f"{pc:3d} | {ir_str:^8} | {r['a']:^10} | {r['b']:^10} | "
            f"{r['Sd']:^10} | {r['vai_um']:^6} | {r['N']:^1} | {r['Z']:^1}"
        )
        log_lines.append(log_line)
        results.append((pc, ir_str, r))

    # ── Sumário ──────────────────────────────────────────────────────────────
    print(H("\n══════════════════════════════════════════════════════════════════"))
    print(H("  Resumo das Saídas"))
    print(H("══════════════════════════════════════════════════════════════════"))
    print(f"  {BOLD}{log_header}{RST}")
    print(D("  " + log_sep))
    for pc, ir_str, r in results:
        n_s = HL(str(r['N'])) if r['N'] else str(r['N'])
        z_s = HL(str(r['Z'])) if r['Z'] else str(r['Z'])
        v_s = HL(str(r['vai_um'])) if r['vai_um'] else str(r['vai_um'])
        sd_s = HL(str(r['Sd']))
        print(f"  {pc:3d} | {ir_str:^8} | {r['a']:^10} | {r['b']:^10} | "
              f"{sd_s:}  | {v_s:}  | {n_s} | {z_s}")

    # Grava log
    if log_path:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(log_lines) + "\n")
        print(G(f"\n  Log gravado em: {log_path}"))

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Trace detalhado de uma instrução
# ─────────────────────────────────────────────────────────────────────────────

def trace_instrucao(pc: int, ir_str: str, r: dict):
    """
    Imprime o trace passo a passo de uma instrução de 8 bits.
    """
    sep = D("─" * 76)
    f   = r  # alias

    # Cabeçalho
    print(f"\n{sep}")
    print(
        f"{H(f'[PC={pc:03d}]')}  IR = {BOLD}{ir_str}{RST}  │  "
        f"SLL8={Y(str(f['sll8']))} SRA1={Y(str(f['sra1']))} "
        f"F0={Y(str(f['f0']))} F1={Y(str(f['f1']))} "
        f"ENA={Y(str(f['ena']))} ENB={Y(str(f['enb']))} "
        f"INVA={Y(str(f['inva']))} INC={Y(str(f['inc']))}"
    )

    # Operandos
    a_bin = f"{f['a']:08b}"
    b_bin = f"{f['b']:08b}"
    print(f"  {D('Operandos:')}  "
          f"A = {B(a_bin)} ({f['a']:3d})   "
          f"B = {B(b_bin)} ({f['b']:3d})")
    print()

    # ── Etapa 1: ENA / ENB ──────────────────────────────────────────────────
    a_en = f['a'] if f['ena'] else 0
    b_en = f['b'] if f['enb'] else 0
    print(f"  {G('① ENA/ENB:')}  "
          f"A_en = {a_en:08b} ({a_en:3d})   "
          f"B_en = {b_en:08b} ({b_en:3d})")

    # ── Etapa 2: INVA ───────────────────────────────────────────────────────
    a_inv = (a_en ^ MASK) & MASK if f['inva'] else a_en
    inv_str = f"{a_en:08b} XOR {MASK:08b}" if f['inva'] else "sem inversão"
    print(f"  {G('② INVA:')}     "
          f"A_inv = {a_inv:08b} ({a_inv:3d})  [{inv_str}]")

    # ── Etapa 3: Operação selecionada ────────────────────────────────────────
    op_label = {
        "AND"  : f"F1F0=00 → AND   → {a_inv:08b} AND {b_en:08b}",
        "OR"   : f"F1F0=01 → OR    → {a_inv:08b} OR  {b_en:08b}",
        "NOT_B": f"F1F0=10 → NOT_B → NOT {b_en:08b}",
        "ADD"  : f"F1F0=11 → ADD   → {a_inv:08b} + {b_en:08b} (carry-in={f['inc']})",
    }
    print(f"  {G('③ Operação:')}  [{op_label[f['op']]}]")

    # ── Etapa 4: Resultado da ULA (antes do deslocamento) ───────────────────
    s_raw_bin = f"{f['S_raw']:08b}"
    print(f"  {G('④ Saída ULA:')} S_raw = {HL(s_raw_bin)} ({f['S_raw']:3d})   "
          f"Vai-um = {HL(str(f['vai_um']))}")

    # ── Etapa 5: Deslocador ──────────────────────────────────────────────────
    shift_label  = "SLL8" if f['sll8'] else ("SRA1" if f['sra1'] else "Passagem direta")
    if f['sll8']:
        sd_bin = f"{f['Sd']:016b}"
        print(f"  {G('⑤ Deslocador:')} [{shift_label}]  "
              f"Sd = {HL(sd_bin)} ({f['Sd']})  [S deslocado 8 bits à esquerda]")
    else:
        sd_bin = f"{f['Sd']:08b}"
        if f['sra1']:
            print(f"  {G('⑤ Deslocador:')} [{shift_label}]  "
                  f"Sd = {HL(sd_bin)} ({f['Sd']:3d})  [S deslocado 1 bit à direita (aritmético)]")
        else:
            print(f"  {G('⑤ Deslocador:')} [{shift_label}]  "
                  f"Sd = {HL(sd_bin)} ({f['Sd']:3d})  [=S_raw]")

    # ── Etapa 6: Flags ───────────────────────────────────────────────────────
    n_str = HL("1 (negativo)") if f['N'] else "0"
    z_str = HL("1 (zero)")     if f['Z'] else "0"
    print(f"  {G('⑥ Flags:')}     N = {n_str}   Z = {z_str}")

    # Resultado final
    print()
    if f['sll8']:
        sd_fmt = f"{f['Sd']:#06x} (16 bits)"
    else:
        sd_fmt = f"{f['Sd']:#04x}"
    print(f"  {BOLD}Resultado:{RST}  "
          f"Sd = {HL(str(f['Sd']))} ({sd_fmt})   "
          f"Vai-um = {HL(str(f['vai_um']))}   "
          f"N = {HL(str(f['N']))}   "
          f"Z = {HL(str(f['Z']))}")


# ─────────────────────────────────────────────────────────────────────────────
# Gerador de arquivo de exemplo
# ─────────────────────────────────────────────────────────────────────────────

EXEMPLO_PROGRAMA_E2 = """\
# programa_etapa2_tarefa1.txt
# Formato: SLL8 SRA1 F0 F1 ENA ENB INVA INC  (8 bits, sem espaços)
#
# SLL8 SRA1 F0 F1 ENA ENB INVA INC   Operação
10111100   # ADD   A+B + SLL8
01111100   # ADD   A+B + SRA1
00111100   # ADD   A+B (sem deslocamento)
"""

def gerar_exemplo_e2():
    path = "programa_etapa2_tarefa1.txt"
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(EXEMPLO_PROGRAMA_E2)
        print(G(f"  Arquivo de exemplo criado: {path}"))
    return path


# ─────────────────────────────────────────────────────────────────────────────
# Ponto de entrada principal (refatorado)
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """
    Ponto de entrada principal do programa.
    Suporta argumentos de linha de comando:
        python ula_mic1_etapa2.py
        python ula_mic1_etapa2.py programa.txt saida.txt A B
    """
    # Valores padrão
    prog_path = 'programa_etapa2_tarefa1.txt'
    saida_path = 'saida_etapa2_tarefa1.txt'
    
    # Valores padrão para A e B (compatíveis com os testes)
    a = 0b10110101  # 181 (0xB5)
    b = 0b01001010  # 74  (0x4A)

    # Processa argumentos da linha de comando
    if len(sys.argv) > 1:
        prog_path = sys.argv[1]
    if len(sys.argv) > 2:
        saida_path = sys.argv[2]
    if len(sys.argv) > 3:
        try:
            a = int(sys.argv[3], 0) & 0xFF  # aceita decimal ou hex (0x...)
        except ValueError:
            print(f"Erro: valor inválido para A: '{sys.argv[3]}'")
    if len(sys.argv) > 4:
        try:
            b = int(sys.argv[4], 0) & 0xFF
        except ValueError:
            print(f"Erro: valor inválido para B: '{sys.argv[4]}'")

    # Verifica se o arquivo de programa existe; se não, gera o exemplo
    if not os.path.exists(prog_path):
        print(f"Aviso: Arquivo '{prog_path}' não encontrado. Gerando exemplo...")
        prog_path = gerar_exemplo_e2()

    try:
        # Carrega o programa
        instrucoes = load_program(prog_path)
        if not instrucoes:
            print(f"Erro: Nenhuma instrução válida em '{prog_path}'")
            return

        print(f"\nCarregando programa: {prog_path}")
        print(f"Instruções: {len(instrucoes)}")
        print(f"Entradas: A={a} (0x{a:02X}), B={b} (0x{b:02X})")

        # Executa o programa
        resultados = run_program(
            instructions=instrucoes,
            a=a,
            b=b,
            log_path=saida_path,
            verbose=True
        )

        print(f"\nExecução concluída. {len(resultados)} instruções processadas.")

    except FileNotFoundError as e:
        print(f"Erro: {e}")
    except ValueError as e:
        print(f"Erro: {e}")
    except Exception as e:
        print(f"Erro inesperado: {e}")

if __name__ == "__main__":
    main()