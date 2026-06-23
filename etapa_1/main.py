import os

def decode_instruction(ir_string):
    """Decodifica a string de 6 bits nos sinais de controle."""
    ir_string = ir_string.strip()
    if len(ir_string) != 6:
        raise ValueError(f"Instrução inválida: {ir_string}")
        
    return {
        'F0': int(ir_string[0]),
        'F1': int(ir_string[1]),
        'ENA': int(ir_string[2]),
        'ENB': int(ir_string[3]),
        'INVA': int(ir_string[4]),
        'INC': int(ir_string[5])
    }

def ula_mic1(a, b, ctrl):
    """Executa a operação da ULA de 1 bit."""
    MASK = 1
    
    F0 = ctrl['F0']
    F1 = ctrl['F1']
    ENA = ctrl['ENA']
    ENB = ctrl['ENB']
    INVA = ctrl['INVA']
    INC = ctrl['INC']

    a_ena = a & (MASK if ENA else 0)
    b_enb = b & (MASK if ENB else 0)

    a_inva = a_ena ^ (MASK if INVA else 0)
    b_inv = (~b_enb) & MASK

    en_and = (not F0) and (not F1)
    en_or = (not F0) and F1
    en_not = F0 and (not F1)
    en_sum = F0 and F1

    s = 0
    vai_um = 0

    if en_and:
        s = a_inva & b_enb
    elif en_or:
        s = a_inva | b_enb
    elif en_not:
        s = b_inv
    elif en_sum:
        resultado_soma = a_inva + b_enb + INC
        s = resultado_soma & MASK
        vai_um = (resultado_soma >> 1) & 1

    return s, vai_um

def main():
    programa_path = 'programa_etapa1.txt'
    saida_path = 'saida_etapa1.txt'
    
    a_inicial = 1
    b_inicial = 1
    
    if not os.path.exists(programa_path):
        print(f"Erro: Arquivo '{programa_path}' não encontrado.")
        return

    with open(programa_path, 'r') as f_in, open(saida_path, 'w') as f_out:
        f_out.write("PC\tIR\tA\tB\tS\tVai-um\n")
        f_out.write("-" * 50 + "\n")
        
        pc = 0
        for linha in f_in:
            linha = linha.strip()
            if not linha or linha.startswith('#'):
                continue
            
            try:
                ctrl = decode_instruction(linha)
                s, vai_um = ula_mic1(a_inicial, b_inicial, ctrl)
                f_out.write(f"{pc}\t{linha}\t{a_inicial}\t{b_inicial}\t{s}\t{vai_um}\n")
                pc += 1
            except Exception as e:
                print(f"Erro ao processar instrução '{linha}' no PC {pc}: {e}")

    print(f"Execução concluída. Resultados exportados para '{saida_path}'.")

if __name__ == "__main__":
    main()
