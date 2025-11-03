import streamlit as st
from datetime import datetime, timedelta
from typing import List, Tuple
import pandas as pd

# --- FUNÇÕES DE ANÁLISE ---

def calcular_faltantes_seletivos(digitos_presentes: List[int]) -> Tuple[List[int], int]:
    """Identifica os números faltantes que completam uma sequência (máximo 3 faltantes)."""
    digitos_presentes = sorted(list(set(digitos_presentes)))
    todos_faltantes_seletivos = set()
    
    # Busca faltantes entre dígitos consecutivos (máximo 3 faltantes)
    for i in range(len(digitos_presentes) - 1):
        d1 = digitos_presentes[i]
        d2 = digitos_presentes[i+1]
        diferenca = d2 - d1
        
        if 2 <= diferenca <= 4:
            for d in range(d1 + 1, d2):
                todos_faltantes_seletivos.add(d)
    
    # Incluir faltantes que ligam ao 0 (se faltar 3 ou menos)
    if digitos_presentes and digitos_presentes[0] > 0 and digitos_presentes[0] <= 4:
        for d in range(1, digitos_presentes[0]):
            todos_faltantes_seletivos.add(d)

    # Incluir faltantes que ligam ao 9 (se faltar 3 ou menos)
    if digitos_presentes and digitos_presentes[-1] < 9 and (9 - digitos_presentes[-1]) <= 3:
        for d in range(digitos_presentes[-1] + 1, 10):
            todos_faltantes_seletivos.add(d)

    faltantes_finais = sorted(list(todos_faltantes_seletivos))
    soma_total = sum(faltantes_finais)

    return faltantes_finais, soma_total

def formatar_resultado_r(r_bruto: float) -> float:
    """Aplica a regra de formatação para o Resultado R."""
    if r_bruto <= 100:
        return r_bruto
    else:
        parte_inteira = int(r_bruto)
        soma_digitos = sum(int(d) for d in str(parte_inteira))
        parte_decimal = r_bruto - parte_inteira
        
        return round(soma_digitos + parte_decimal, 1)

def analisar_e_gerar_alertas(rodada, vela_str, horario_str):
    
    # --- 1. Extração de Componentes e Validação ---
    try:
        ultimos_dois_rodada = rodada % 100
        # Tenta extrair a parte inteira da vela. Ex: 23.89x -> 23
        parte_numerica = vela_str.replace('x', '')
        if '.' in parte_numerica:
            vela_inteira
