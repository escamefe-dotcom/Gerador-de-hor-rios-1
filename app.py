import streamlit as st
from datetime import datetime, timedelta
from typing import List, Tuple
import pandas as pd
import re

# --- FUNÇÕES DE ANÁLISE ---

def calcular_faltantes_seletivos(digitos_presentes: List[int]) -> Tuple[List[int], int]:
    """Identifica os números faltantes que completam uma sequência (máximo 3 faltantes)."""
    digitos_presentes = sorted(list(set(digitos_presentes)))
    todos_faltantes_seletivos = set()
    
    for i in range(len(digitos_presentes) - 1):
        d1 = digitos_presentes[i]
        d2 = digitos_presentes[i+1]
        diferenca = d2 - d1
        
        if 2 <= diferenca <= 4:
            for d in range(d1 + 1, d2):
                todos_faltantes_seletivos.add(d)
    
    if digitos_presentes and digitos_presentes[0] > 0 and digitos_presentes[0] <= 4:
        for d in range(1, digitos_presentes[0]):
            todos_faltantes_seletivos.add(d)

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
        parte_numerica = vela_str.replace('x', '')
        if '.' in parte_numerica:
            vela_inteira = int(float(parte_numerica))
        else:
            vela_inteira = int(parte_numerica)
            
        horario_base_dt = datetime.strptime(horario_str, "%H:%M:%S")
        minuto_original = horario_base_dt.minute
    except ValueError:
        return None, None, None, None
    
    digitos_vela_str = ''.join(c for c in vela_str if c.isdigit())
    digitos_vela = [int(d) for d in digitos_vela_str]
    
    digitos_horario_str = ''.join(c for c in horario_str if c.isdigit())
    digitos_horario = [int(d) for d in digitos_horario_str]
    
    # --- 2. Análise Seletiva de Faltantes ---
    
    faltantes_V, soma_VT = calcular_faltantes_seletivos(digitos_vela)
    faltantes_H, soma_HT = calcular_faltantes_seletivos(digitos_horario)
    
    # --- 3. Cálculo e Formatação do Resultado R ---
    
    r_bruto = (ultimos_dois_rodada * 0.6) + vela_inteira + minuto_original
    r_formatado = formatar_resultado_r(r_bruto)
    
    # --- 4. Geração de Horários Brutos ---
    
    horarios_brutos = []
    
    def
