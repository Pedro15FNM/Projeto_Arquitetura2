"""
=============================================================================
  MIC-1 — ETAPA 3: MICROINSTRUÇÕES DE 23 BITS COM ACESSO À MEMÓRIA
=============================================================================

  Palavra de microinstrução: 23 bits
  ┌──────────┬───────────────┬──────────┬──────────────┐
  │  ULA     │ Barramento C  │ Memória  │ Barramento B │
  │  8 bits  │    9 bits     │  2 bits  │    4 bits    │
  └──────────┴───────────────┴──────────┴──────────────┘

  ── ULA (bits 22..15) ────────────────────────────────────────────────────
    Bit 22: SLL8   Bit 21: SRA1   Bit 20: F0   Bit 19: F1
    Bit 18: ENA    Bit 17: ENB    Bit 16: INVA  Bit 15: INC

  ── Barramento C (bits 14..6) ─────────────────────────────────────────────
    Bit 14: H    Bit 13: OPS   Bit 12: TOS   Bit 11: CPP
    Bit 10: LV   Bit  9: SP    Bit  8: PC    Bit  7: MDR   Bit 6: MAR

  ── Memória (bits 5..4) ───────────────────────────────────────────────────
    Bit 5: WRITE   Bit 4: READ
    WRITE: MDR → dados[MAR]    READ: dados[MAR] → MDR
    (ocorre APÓS a escrita no barramento C)

  ── Barramento B (bits 3..0) ──────────────────────────────────────────────
    0000=MDR  0001=PC   0010=MBR  0011=MBRU
    0100=SP   0101=LV   0110=CPP  0111=TOS
    1000=OPS  1001=H

  Entrada A da ULA: sempre o registrador H.

  Ordem de execução:
    1. Lê barramento B (registrador selecionado por bits 3..0)
    2. ULA: A=H, B=barr_B → calcula Sd
    3. Escreve Sd nos registradores habilitados pelo barramento C
    4. WRITE ou READ de memória (APÓS barramento C)

  Log por instrução:
    Registradores antes/depois, barramento B ativo, barramento C ativo,
    e linhas da memória de dados após cada microinstrução.

  Uso:
    python mic1_etapa3.py                        # demos internas
    python mic1_etapa3.py prog.trt dados.txt     # arquivos customizados
    python mic1_etapa3.py prog.trt dados.txt saida.txt --quiet
=============================================================================
"""
from __future__ import annotations
import sys, os

# ─── Cores ANSI ──────────────────────────────────────────────────────────────
RST="\033[0m"; BOLD="\033[1m"; CYN="\033[96m"; GRN="\033[92m"
YLW="\033[93m"; RED="\033[91m"; BLU="\033[94m"; GRY="\033[90m"
MAG="\033[95m"; ORG="\033[33m"
def H(s):  return f"{BOLD}{CYN}{s}{RST}"
def G(s):  return f"{GRN}{s}{RST}"
def Y(s):  return f"{YLW}{s}{RST}"
def B(s):  return f"{BLU}{s}{RST}"
def D(s):  return f"{GRY}{s}{RST}"
def HL(s): return f"{BOLD}{MAG}{s}{RST}"
def RD(s): return f"{RED}{s}{RST}"
def OR(s): return f"{ORG}{s}{RST}"

# ─── Constantes ──────────────────────────────────────────────────────────────
WORD_MASK  = 0xFFFFFFFF
WORD_SIGN  = 0x80000000
MEM_SIZE   = 8

BARR_B_MAP = {
    0b0000:"MDR", 0b0001:"PC",  0b0010:"MBR",  0b0011:"MBRU",
    0b0100:"SP",  0b0101:"LV",  0b0110:"CPP",  0b0111:"TOS",
    0b1000:"OPS", 0b1001:"H",
}

# ─── ULA de 32 bits ──────────────────────────────────────────────────────────

def _fa(a, b, c):
    return a ^ b ^ c, (a & b) | (c & (a ^ b))

def ula_32(sll8, sra1, f0, f1, ena, enb, inva, inc, a, b):
    op = {(0,0):"AND",(0,1):"OR",(1,0):"NOT_B",(1,1):"ADD"}[(f0,f1)]
    carry = inc
    s_val = 0
    for i in range(32):
        ab = (a>>i)&1; bb = (b>>i)&1
        ae = ab & ena; be = bb & enb
        ai = ae ^ inva
        if op=="AND":  sb,co = _fa(ai & be, 0, 0)
        elif op=="OR": sb,co = _fa(ai | be, 0, 0)
        elif op=="NOT_B": sb,co = _fa(be^1, 0, 0)
        else:          sb,co = _fa(ai, be, carry)
        s_val |= (sb << i); carry = co
    s_val &= WORD_MASK
    if sll8 and sra1:
        raise ValueError("SLL8 e SRA1 simultaneos!")
    if sll8:
        sd = (s_val << 8) & WORD_MASK
        sh = f"SLL8:{s_val:#010x}<<8={sd:#010x}"
    elif sra1:
        sd = ((s_val >> 1) | (s_val & WORD_SIGN)) & WORD_MASK
        sh = f"SRA1:{s_val:#010x}>>1={sd:#010x}"
    else:
        sd = s_val; sh = "NoShift"
    n = (sd >> 31) & 1
    z = 1 if sd == 0 else 0
    return {"op":op,"S_raw":s_val,"vai_um":carry,"Sd":sd,"shift":sh,"N":n,"Z":z}

# ─── Registradores ───────────────────────────────────────────────────────────

class Registers:
    NAMES = ["H","OPS","TOS","CPP","LV","SP","PC","MDR","MAR","MBR","MBRU"]
    def __init__(self):
        for n in self.NAMES: setattr(self, n, 0)
    def get(self, name):
        return getattr(self, name, 0)
    def set(self, name, value):
        if name in ("MBR","MBRU"):
            v = value & 0xFF
            self.MBR  = v if v < 128 else v - 256
            self.MBRU = v
        else:
            setattr(self, name, value & WORD_MASK)
    def snapshot(self):
        return {n: self.get(n) for n in self.NAMES}
    def dump(self):
        lines=[]; row=[]
        for i,n in enumerate(self.NAMES):
            v=self.get(n)
            row.append(f"{n}={v:#010x}({v:11d})")
            if len(row)==3: lines.append("  "+"  ".join(row)); row=[]
        if row: lines.append("  "+"  ".join(row))
        return "\n".join(lines)

# ─── Memória de dados ─────────────────────────────────────────────────────────

class DataMemory:
    def __init__(self, size=MEM_SIZE):
        self.size = size
        self.data = [0]*size
    def read(self, addr):
        if not 0<=addr<self.size: raise IndexError(f"Endereço inválido: {addr}")
        return self.data[addr]
    def write(self, addr, value):
        if not 0<=addr<self.size: raise IndexError(f"Endereço inválido: {addr}")
        self.data[addr] = value & WORD_MASK
    def snapshot(self): return self.data[:]
    def dump(self):
        return "\n".join(f"  dados[{i}]={v:#010x} ({v:11d})" for i,v in enumerate(self.data))

# ─── Parser da microinstrução ─────────────────────────────────────────────────

def parse_mi(ir_str):
    """
    Decodifica string de 23 bits.

    Posições (0=MSB, 22=LSB):
      0-7   : ULA  (SLL8,SRA1,F0,F1,ENA,ENB,INVA,INC)
      8-16  : Barramento C  (H,OPS,TOS,CPP,LV,SP,PC,MDR,MAR)
      17-18 : Memória (WRITE,READ)
      19-22 : Barramento B (4 bits)
    """
    ir_str = ir_str.strip()
    if len(ir_str)!=23 or not all(c in "01" for c in ir_str):
        raise ValueError(f"IR inválido: '{ir_str}' (precisa de 23 bits)")
    b = [int(c) for c in ir_str]
    ula = dict(SLL8=b[0],SRA1=b[1],F0=b[2],F1=b[3],ENA=b[4],ENB=b[5],INVA=b[6],INC=b[7])
    bc  = dict(H=b[8],OPS=b[9],TOS=b[10],CPP=b[11],LV=b[12],SP=b[13],PC=b[14],MDR=b[15],MAR=b[16])
    mem = dict(WRITE=b[17],READ=b[18])
    bb_code = (b[19]<<3)|(b[20]<<2)|(b[21]<<1)|b[22]
    bb_reg  = BARR_B_MAP.get(bb_code, f"?({bb_code:04b})")
    return {"raw":ir_str,"ula":ula,"barr_c":bc,"mem":mem,"bb_code":bb_code,"bb_reg":bb_reg}

# ─── Execução de uma microinstrução ──────────────────────────────────────────

def executar(mi, regs, mem_dados):
    """
    Executa uma microinstrução em 4 passos:
      1. Lê barramento B
      2. Calcula ULA (A=H sempre, B=barr_B)
      3. Escreve Sd nos registradores do barramento C
      4. Operação de memória (APÓS barramento C)
    """
    snap_antes    = regs.snapshot()
    snap_mem_antes = mem_dados.snapshot()

    # 1. Barramento B
    bb_reg = mi["bb_reg"]
    bb_val = regs.get(bb_reg) & WORD_MASK

    # 2. ULA: A = H (sempre)
    u = mi["ula"]
    ur = ula_32(u["SLL8"],u["SRA1"],u["F0"],u["F1"],
                u["ENA"],u["ENB"],u["INVA"],u["INC"],
                regs.H & WORD_MASK, bb_val)
    sd = ur["Sd"]

    # 3. Barramento C → escreve Sd
    escritos = []
    for reg, en in mi["barr_c"].items():
        if en:
            regs.set(reg, sd)
            escritos.append(reg)

    # 4. Memória (APÓS barramento C)
    m = mi["mem"]; mem_op = None
    if m["WRITE"] and m["READ"]:
        raise ValueError("WRITE e READ simultâneos!")
    elif m["WRITE"]:
        addr = regs.MAR & (MEM_SIZE-1)
        mem_dados.write(addr, regs.MDR)
        mem_op = "WRITE"
    elif m["READ"]:
        addr = regs.MAR & (MEM_SIZE-1)
        val  = mem_dados.read(addr)
        regs.set("MDR", val)
        mem_op = "READ"

    return {
        "snap_antes":snap_antes, "snap_depois":regs.snapshot(),
        "snap_mem_antes":snap_mem_antes, "snap_mem_depois":mem_dados.snapshot(),
        "bb_reg":bb_reg, "bb_val":bb_val,
        "escritos":escritos, "ur":ur, "sd":sd, "mem_op":mem_op,
    }

# ─── Trace / Log ─────────────────────────────────────────────────────────────

def trace(pc, mi, ex, verbose=True):
    u=mi["ula"]; ur=ex["ur"]; sa=ex["snap_antes"]; sd_=ex["snap_depois"]
    sep = D("─"*82)

    if verbose:
        print(f"\n{sep}")
        print(f"{H(f'[PC={pc:03d}]')}  IR={BOLD}{mi['raw']}{RST}")
        print(f"  {D('ULA:')} "
              f"SLL8={Y(str(u['SLL8']))} SRA1={Y(str(u['SRA1']))} "
              f"F0={Y(str(u['F0']))} F1={Y(str(u['F1']))} "
              f"ENA={Y(str(u['ENA']))} ENB={Y(str(u['ENB']))} "
              f"INVA={Y(str(u['INVA']))} INC={Y(str(u['INC']))}")
        print(f"  {D('BarrB:')} {B(ex['bb_reg'])}  "
              f"{D('BarrC:')} {G(','.join(ex['escritos']) or '(nenhum)')}  "
              f"{D('Mem:')} WRITE={Y(str(mi['mem']['WRITE']))} READ={Y(str(mi['mem']['READ']))}")

        # Registradores ANTES
        print(f"\n  {G('◀ Registradores ANTES:')}")
        _print_snap(sa)

        # Passos
        print(f"\n  {G('① BarrB:')}  "
              f"{B(ex['bb_reg'])} = {ex['bb_val']:#010x} ({ex['bb_val']})")
        a_ula = sa["H"] & WORD_MASK
        print(f"  {G('② ULA:')}   A(H)={a_ula:#010x}  B={ex['bb_val']:#010x}  "
              f"op={ur['op']}  S_raw={ur['S_raw']:#010x}  {ur['shift']}")
        print(f"           Sd={HL(f\"{ur['Sd']:#010x}\")}({ur['Sd']})  "
              f"Vai-um={HL(str(ur['vai_um']))}  N={HL(str(ur['N']))}  Z={HL(str(ur['Z']))}")
        if ex["escritos"]:
            print(f"  {G('③ BarrC:')}  Sd={HL(f'{ex[\"sd\"]:#010x}')} → {', '.join(ex['escritos'])}")
        else:
            print(f"  {G('③ BarrC:')}  (nenhum registrador escrito)")

        if ex["mem_op"]=="WRITE":
            addr=sd_["MAR"]&(MEM_SIZE-1)
            print(f"  {G('④ WRITE:')}  dados[MAR={addr}] ← MDR={OR(f'{sd_[\"MDR\"]:#010x}')} ({sd_['MDR']})")
        elif ex["mem_op"]=="READ":
            addr=sd_["MAR"]&(MEM_SIZE-1)
            print(f"  {G('④ READ:')}   MDR ← dados[MAR={addr}] = {OR(f'{sd_[\"MDR\"]:#010x}')} ({sd_['MDR']})")
        else:
            print(f"  {G('④ Mem:')}    (sem operação)")

        # Registradores DEPOIS
        print(f"\n  {G('▶ Registradores DEPOIS:')}")
        _print_snap(sd_)

        # Diff de registradores
        diffs = [f"{n}: {sa[n]:#010x}→{HL(f'{sd_[n]:#010x}')}"
                 for n in Registers.NAMES if sa.get(n)!=sd_.get(n)]
        if diffs:
            print(f"  {G('  Δ Alterados:')} " + ", ".join(diffs))

        # Diff de memória
        mdiffs = [f"dados[{i}]:{b:#010x}→{HL(f'{a:#010x}')}({a})"
                  for i,(b,a) in enumerate(zip(ex["snap_mem_antes"],ex["snap_mem_depois"])) if b!=a]
        print(f"\n  {G('Memória dados:')} " + (OR("ALTERADA → ")+", ".join(mdiffs) if mdiffs else D("(inalterada)")))

    # Linha de log (sempre gerada)
    m=ex["snap_mem_depois"]
    log = (
        f"PC={pc:03d}|IR={mi['raw']}|"
        f"BarrB={ex['bb_reg']}({ex['bb_val']})|"
        f"BarrC=[{','.join(ex['escritos']) or '-'}]|"
        f"op={ur['op']}|Sd={ur['Sd']}|VU={ur['vai_um']}|N={ur['N']}|Z={ur['Z']}|"
        f"MEM={ex['mem_op'] or '-'}|"
        f"H={sd_['H']}|OPS={sd_['OPS']}|TOS={sd_['TOS']}|CPP={sd_['CPP']}|"
        f"LV={sd_['LV']}|SP={sd_['SP']}|PC={sd_['PC']}|MDR={sd_['MDR']}|"
        f"MAR={sd_['MAR']}|MBR={sd_['MBR']}|"
        f"DADOS=[{','.join(str(v) for v in m)}]"
    )
    return log

def _print_snap(snap):
    row=[]
    for i,n in enumerate(Registers.NAMES):
        v=snap.get(n,0)
        row.append(f"{n}={v:#010x}({v:11d})")
        if len(row)==3: print("    "+"  ".join(row)); row=[]
    if row: print("    "+"  ".join(row))

# ─── Carregamento de arquivos ─────────────────────────────────────────────────

def load_programa(path):
    if not os.path.exists(path): raise FileNotFoundError(f"Não encontrado: {path}")
    instrs=[]
    with open(path) as f:
        for raw in f:
            line=raw.split("#")[0].strip()
            if line: instrs.append(line)
    return instrs

def load_dados(path, mem):
    if not os.path.exists(path): raise FileNotFoundError(f"Não encontrado: {path}")
    with open(path) as f:
        for i,raw in enumerate(f):
            if i>=mem.size: break
            line=raw.split("#")[0].strip()
            if line: mem.data[i]=int(line,0)&WORD_MASK

# ─── Execução do programa ─────────────────────────────────────────────────────

def run_programa(instrucoes, mem_dados, regs_init=None, log_path=None, verbose=True):
    regs = Registers()
    if regs_init:
        for k,v in regs_init.items(): regs.set(k,v)

    print(H("\n"+"═"*82))
    print(H("  MIC-1 ETAPA 3 — Execução de Microinstruções (23 bits)"))
    print(H("═"*82))
    print(f"  {len(instrucoes)} microinstrução(ões)  |  Registradores iniciais:")
    print(regs.dump())
    print(f"\n  Memória de dados inicial:")
    print(mem_dados.dump())

    log = ["="*100, "LOG MIC-1 ETAPA 3", "="*100,
           "PC  | IR(23b)                | BarrB      | BarrC              | "
           "op    Sd           VU N Z | MEM   | Regs pós execução",
           "-"*100]

    for pc, ir_str in enumerate(instrucoes):
        try:
            mi = parse_mi(ir_str)
            ex = executar(mi, regs, mem_dados)
            log.append(trace(pc, mi, ex, verbose=verbose))
        except (ValueError, IndexError) as e:
            print(RD(f"\n  [PC={pc:03d}] ERRO: {e}"))
            log.append(f"PC={pc:03d}|ERRO={e}")

    print(H("\n"+"═"*82))
    print(H("  Estado Final"))
    print(H("═"*82))
    print(regs.dump())
    print(f"\n  Memória de dados final:")
    print(mem_dados.dump())

    if log_path:
        with open(log_path,"w") as f: f.write("\n".join(log)+"\n")
        print(G(f"\n  Log salvo em: {log_path}"))
    return log

# ─── Arquivos de exemplo ──────────────────────────────────────────────────────

DADOS_EXEMPLO = """100    # dados[0]
200    # dados[1]
0      # dados[2]
0      # dados[3]
0      # dados[4]
0      # dados[5]
0      # dados[6]
0      # dados[7]
"""

# Instruções de 23 bits:
# Cada linha: [ULA 8b][BarrC 9b][Mem 2b][BarrB 4b]
PROGRAMA_EXEMPLO = """\
# programa.trt — microinstruções de 23 bits
# [SLL8 SRA1 F0 F1 ENA ENB INVA INC][H OPS TOS CPP LV SP PC MDR MAR][WRITE READ][BB3 BB2 BB1 BB0]
#
# MI-0 (exemplo 4 da spec): Sd = H + LV → MDR; WRITE dados[MAR] ← MDR
# ULA: ADD(H,LV)=ENA=1,ENB=1,F0=1,F1=1; BusC:MDR=1; Mem:WRITE=1; BusB:LV=0101
00111100000000010100101
#
# MI-1 (exemplo 5 da spec): Sd=SP+1 → SP,MAR; READ MDR←dados[MAR]
# ULA: ENB=1,INC=1,F0=1,F1=1,ENA=0 → Sd=SP+1; BusC:SP=1,MAR=1; Mem:READ=1; BusB:SP=0100
00110101000001001010100
#
# MI-2: H = TOS  (copia TOS para H; ULA:ENB=1,ADD,ENA=0; BusC:H; BusB:TOS=0111)
00110100100000000000111
#
# MI-3: TOS = H + LV  (ULA:ENA=1,ENB=1,ADD; BusC:TOS; BusB:LV=0101)
00111100001000000000101
#
# MI-4: SP = SP + 1; sem mem  (ULA:ENB=1,INC=1,ADD,ENA=0; BusC:SP; BusB:SP=0100)
00110101000000100000100
"""

def gerar_exemplos():
    p1="dados.txt"; p2="programa.trt"; p3="saida_etapa3.txt"
    if not os.path.exists(p1):
        open(p1,"w").write(DADOS_EXEMPLO); print(G(f"  Criado: {p1}"))
    if not os.path.exists(p2):
        open(p2,"w").write(PROGRAMA_EXEMPLO); print(G(f"  Criado: {p2}"))
    return p2, p1, p3

# ─── Demos internas ───────────────────────────────────────────────────────────

def demo_spec():
    """Reproduz os exemplos (4) e (5) da especificação."""
    print(H("\n╔════════════════════════════════════════════════════════════════╗"))
    print(H("║  DEMO — Exemplos (4) e (5) da especificação                    ║"))
    print(H("╚════════════════════════════════════════════════════════════════╝"))

    # ── Exemplo (4) ──────────────────────────────────────────────────────
    print(Y("\n═══ Exemplo (4): Sd = H + LV → MDR; dados[MAR] ← MDR (WRITE) ═══"))
    print(D("""
  IR: 00111100 000000010 10 0101
      ────────────────────────────────────────────────────────
      ULA[8b] : 00111100 → SLL8=0,SRA1=0,F0=1,F1=1,ENA=1,ENB=1,INVA=0,INC=0
                           Op=ADD: Sd = A + B = H + LV
      BarrC[9b]: 000000010 → MDR habilitado (posição 7 da esq=bit MDR)
      Mem[2b] : 10 → WRITE=1, READ=0
      BarrB[4b]: 0101 → LV
      ────────────────────────────────────────────────────────
      Fluxo: B←LV; Sd=H+LV; MDR←Sd; dados[MAR]←MDR
"""))
    r1=Registers(); r1.set("H",42); r1.set("LV",100); r1.set("MAR",3)
    m1=DataMemory()
    mi1=parse_mi("00111100000000010100101")
    ex1=executar(mi1,r1,m1)
    trace(4,mi1,ex1)
    ok1 = ex1["sd"]==142 and m1.data[3]==142
    print(G(f"\n  ✓ Sd = H+LV = 42+100 = {ex1['sd']} {'OK' if ex1['sd']==142 else RD('ERRO')}"))
    print(G(f"  ✓ MDR = {r1.MDR}  dados[3] = {m1.data[3]} {'OK' if ok1 else RD('ERRO')}"))

    # ── Exemplo (5) ──────────────────────────────────────────────────────
    print(Y("\n═══ Exemplo (5): Sd=SP+1 → SP,MAR; MDR←dados[MAR] (READ) ═══"))
    print(D("""
  IR: 00110101 000001001 01 0100
      ────────────────────────────────────────────────────────
      ULA[8b] : 00110101 → ENA=0,ENB=1,INC=1,F0=1,F1=1 → Sd=B+1=SP+1
      BarrC[9b]: 000001001 → SP (pos 5) e MAR (pos 8) habilitados
      Mem[2b] : 01 → WRITE=0, READ=1
      BarrB[4b]: 0100 → SP
      ────────────────────────────────────────────────────────
      Fluxo: B←SP; Sd=SP+1; SP←Sd; MAR←Sd; MDR←dados[MAR]
"""))
    r2=Registers(); r2.set("SP",1)
    m2=DataMemory(); m2.data[2]=999
    mi2=parse_mi("00110101000001001010100")
    ex2=executar(mi2,r2,m2)
    trace(5,mi2,ex2)
    ok2 = r2.SP==2 and r2.MAR==2 and r2.MDR==999
    print(G(f"\n  ✓ SP={r2.SP} MAR={r2.MAR} MDR={r2.MDR} {'OK' if ok2 else RD('ERRO')}"))


def demo_sequencia():
    """Sequência completa: cálculo → write → read → propagação."""
    print(H("\n╔════════════════════════════════════════════════════════════════╗"))
    print(H("║  DEMO — Sequência: H+LV → mem[0] → MDR → TOS                  ║"))
    print(H("╚════════════════════════════════════════════════════════════════╝"))
    r=Registers(); r.set("H",10); r.set("LV",20); r.set("MAR",0)
    m=DataMemory()

    instrucoes = [
        # Sd = H+LV → MDR  (sem mem)
        ("00111100000000010000101", "Sd=H+LV→MDR"),
        # WRITE: dados[MAR=0] ← MDR  (ULA pass B=MDR; BusC:nenhum; WRITE)
        ("00110100000000001000000", "WRITE dados[0]←MDR"),
        # READ: MDR ← dados[MAR=0]   (ULA pass; BusC:nenhum; READ)
        ("00110100000000000100000", "READ MDR←dados[0]"),
        # TOS = MDR  (Sd=MDR via BusB+ADD; BusC:TOS)
        ("00110100001000000000000", "TOS←MDR"),
    ]

    for pc,(ir_str,desc) in enumerate(instrucoes):
        print(Y(f"\n  ── MI-{pc}: {desc} ──"))
        mi=parse_mi(ir_str)
        ex=executar(mi,r,m)
        trace(pc,mi,ex)

    print(H("\n  Estado final:"))
    print(r.dump())
    ok = m.data[0]==30 and r.TOS==30
    print(G(f"\n  dados[0]={m.data[0]} TOS={r.TOS} (esperado 30) {'OK' if ok else RD('ERRO')}"))


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    args=sys.argv[1:]
    if "--demo" in args or not args:
        demo_spec()
        demo_sequencia()
        p_prog,p_dados,p_log = gerar_exemplos()
        print(H(f"\n\n  ── Executando {p_prog} com {p_dados} ──"))
        mem=DataMemory(); load_dados(p_dados,mem)
        instrs=load_programa(p_prog)
        run_programa(instrs,mem,
                     regs_init={"H":5,"LV":10,"SP":0,"MAR":0,"TOS":0},
                     log_path=p_log, verbose=True)
        return
    if len(args)>=2:
        p_prog=args[0]; p_dados=args[1]
        p_log =args[2] if len(args)>=3 else "saida_etapa3.txt"
        quiet = "--quiet" in args
        mem=DataMemory(); load_dados(p_dados,mem)
        instrs=load_programa(p_prog)
        run_programa(instrs,mem,log_path=p_log,verbose=not quiet)
    else:
        print(Y("Uso: python mic1_etapa3.py [prog.trt dados.txt [saida.txt]] [--quiet]"))
        print(Y("     python mic1_etapa3.py --demo"))

if __name__=="__main__":
    main()
