import os
import sys

"""
───────────────────────────────────────────────────────────────────────────
                        Núcleo da ULA de 1 bit
───────────────────────────────────────────────────────────────────────────
"""

def full_adder(a: int, b: int, cin: int) -> tuple[int, int]:
    """
    Somador completo de 1 bit.
    Retorna (soma, carry_out).

    Tabela-verdade (implementação em lógica pura, sem usar '+'):
      S       = A XOR B XOR Cin
      Cout    = (A AND B) OR (Cin AND (A XOR B))
    """

    s    = a ^ b ^ cin
    cout = (a & b) | (cin & (a ^ b))
    return s, cout


def decode_operation(f0: int, f1: int) -> str:
    """
    Decodificador F0/F1 → nome da operação selecionada.
    (Espelho do circuito decodificador da figura.)
    """

    ops = {
        (0, 0): "AND",
        (0, 1): "OR",
        (1, 0): "NOT_B",
        (1, 1): "ADD",   # usa o somador completo
    }
    return ops[(f0, f1)]


def ula_1bit(
    f0: int, f1: int,
    ena: int, enb: int,
    inva: int, inc: int,
    a: int, b: int,
    carry_in: int = 0
) -> tuple[int, int]:
    """
    ULA de 1 bit segundo o diagrama da Mic-1.
    Retorna (S, carry_out).
    """

    # 1. Habilitações
    a_en = a & ena
    b_en = b & enb

    # 2. Inversão de A (XOR com INVA)
    a_inv = a_en ^ inva

    # 3. Vem-um efetivo (INC só atua no bit 0, mas aqui usamos carry_in)
    vem_um = carry_in | inc   # INC é 1 apenas se carry_in=0

    # 4. Decodificador F0/F1 
    op = (f0 << 1) | f1  # 0=AND, 1=OR, 2=NOT_B, 3=ADD

    if op == 0:      # AND
        logic_out = a_inv & b_en
        s, cout = full_adder(logic_out, 0, 0)
    elif op == 1:    # OR
        logic_out = a_inv | b_en
        s, cout = full_adder(logic_out, 0, 0)
    elif op == 2:    # NOT_B
        logic_out = b_en ^ 1
        s, cout = full_adder(logic_out, 0, 0)
    else:            # ADD (soma completa)
        s, cout = full_adder(a_inv, b_en, vem_um)

   
    return s, cout



"""
───────────────────────────────────────────────────────────────────────────
                        ULA DE 32 BITS
───────────────────────────────────────────────────────────────────────────
"""

def ula_32bits(A: int, B: int, ctrl_bits: int) -> tuple[int, int]:
    """
    Executa a ULA sobre palavras de 32 bits.
    ctrl_bits: inteiro com 6 bits no formato F0 F1 ENA ENB INVA INC.
    Retorna (S, carry_out).
    """

    # extrai os 6 bits de controle
    f0  = (ctrl_bits >> 5) & 1
    f1  = (ctrl_bits >> 4) & 1
    ena = (ctrl_bits >> 3) & 1
    enb = (ctrl_bits >> 2) & 1
    inva = (ctrl_bits >> 1) & 1
    inc = ctrl_bits & 1

    S = 0
    carry = 0
    mask = 1

    for i in range(32):
        a_bit = (A >> i) & 1
        b_bit = (B >> i) & 1
        inc_atual = inc if i == 0 else 0  # previne o inc de incrementar todos os bits, como estava fazendo antes da correção
        s_bit, carry = ula_1bit(f0, f1, ena, enb, inva, inc_atual, a_bit, b_bit, carry)

        if s_bit:
            S |= (mask << i)

    return S, carry



"""
───────────────────────────────────────────────────────────────────────────
                   Leitura do arquivo e log
───────────────────────────────────────────────────────────────────────────
"""

def ler_programa(caminho: str) -> list[str]:
    """Lê instruções (6 bits) ignorando linhas vazias e comentários."""

    if not os.path.exists(caminho):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
    with open(caminho, 'r', encoding='utf-8') as f:
        linhas = [linha.strip() for linha in f if linha.strip() and not linha.startswith('#')]
    return linhas


def extrair_entradas(programa: list[str]) -> tuple[int, int]:
    # extrai os valores de A e B da primeira linha

    # valor padrão caso haja erro
    if not programa:
        return 0xFFFFFFFF, 0x00000001
    
    primeira_linha = programa[0]
    partes = primeira_linha.split()

    if len(partes) >= 2:

        try:
            A = int(partes[0], 2) & 0xFFFFFFFF
            B = int(partes[1], 2) & 0xFFFFFFFF
            return A, B
        
        except ValueError:
            pass  # se houve erro, ignora e usa o valor padrão

    return 0xFFFFFFFF, 0x00000001    


def formatar_32bits(valor: int) -> str:
    # Retorna string binária com 32 bits.
    return format(valor & 0xFFFFFFFF, '032b')

def gerar_log(programa: list[str], A: int, B: int) -> list[str]:
    """
    Executa o programa (ignorando a primeira linha) e retorna as linhas de log.
    """

    log = []
    # Cabeçalho
    log.append(f"b = {formatar_32bits(B)}")
    log.append(f"a = {formatar_32bits(A)}")
    log.append("")
    log.append("Start of Program")
    log.append("=" * 60)

    # pula a primeira linha 
    instrucoes = programa[1:] if programa else []
    pc = 1   # PC começa em 1

    for ir_str in instrucoes:
        if len(ir_str) != 6 or not all(c in '01' for c in ir_str):
            raise ValueError(f"Instrução inválida: '{ir_str}'")

        ctrl = int(ir_str, 2)
        S, carry = ula_32bits(A, B, ctrl)

        log.append(f"Cycle {pc}")
        log.append("")
        log.append(f"PC = {pc}")
        log.append(f"IR = {ir_str}")
        log.append(f"b = {formatar_32bits(B)}")
        log.append(f"a = {formatar_32bits(A)}")
        log.append(f"s = {formatar_32bits(S)}")
        log.append(f"co = {carry}")
        log.append("=" * 60)

        pc += 1

    # indica fim do programa
    log.append(f"Cycle {pc}")
    log.append(f"PC = {pc}")
    log.append("")
    log.append("> Line is empty, EOP.")

    return log

def salvar_log(caminho: str, linhas: list[str]) -> None:
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write('\n'.join(linhas))



"""
───────────────────────────────────────────────────────────────────────────
                    Ponto de entrada
───────────────────────────────────────────────────────────────────────────
"""

def main():
    # Argumentos (simples)
    prog_path = 'programa_etapa1.txt'
    saida_path = 'saida_etapa1.txt'

    if len(sys.argv) > 1:
        prog_path = sys.argv[1]
    if len(sys.argv) > 2:
        saida_path = sys.argv[2]

    try:
        programa = ler_programa(prog_path)
        if not programa:
            print(f"Programa vazio em '{prog_path}'")
            return

        A, B = extrair_entradas(programa)   

        linhas_log = gerar_log(programa, A, B)
        salvar_log(saida_path, linhas_log)

        print(f"Execução concluída. Log salvo em '{saida_path}'")

    except Exception as e:
        print(f"Erro: {e}")

if __name__ == '__main__':
    main()