import streamlit as st
from datetime import datetime, timedelta
from typing import List, Tuple
import pandas as pd
import re # Importa a biblioteca de expressões regulares

# Define o layout e tema padrão da página ANTES de qualquer coisa
st.set_page_config(
    page_title="Ferramenta de Análise", 
    layout="centered",
    initial_sidebar_state="collapsed",
)

# --- 1. FUNÇÕES DE CÁLCULO (CACHED) ---

@st.cache_data(show_spinner=False)
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

@st.cache_data(show_spinner=False)
def formatar_resultado_r(r_bruto: float) -> str:
    """Aplica a regra de formatação para o Resultado R (Regra Condicional)."""
    if r_bruto <= 99.99:
        return str(int(r_bruto))
    else:
        parte_inteira = int(r_bruto)
        soma_digitos = sum(int(d) for d in str(parte_inteira))
        parte_decimal = r_bruto - parte_inteira
        
        return str(round(soma_digitos + parte_decimal, 1))

@st.cache_data(show_spinner=False)
def analisar_e_gerar_alertas(rodada, vela_str, horario_str):
    """Calcula os alertas e retorna os dados brutos, incluindo o Timestamp."""
    
    try:
        ultimos_dois_rodada = rodada % 100
        
        # CORREÇÃO CRÍTICA: Processamento da Vela
        # Remove "x" e garante que o float seja parseado corretamente
        parte_numerica = vela_str.replace('x', '').replace(',', '.')
        if not parte_numerica:
             raise ValueError("Vela vazia após limpeza.")
             
        # Garante que pegamos a parte inteira para o cálculo de R
        vela_inteira = int(float(parte_numerica))
        
        # Garante que o horário está no formato correto, adicionando :00 se faltar
        if horario_str.count(':') == 1:
            horario_str += ':00'
            
        horario_base_dt = datetime.strptime(horario_str, "%H:%M:%S")
        minuto_original = horario_base_dt.minute
    except ValueError as e:
        # Se houver erro de formato, retorna None.
        print(f"Erro de Validação na Análise: {e}")
        return None, None, None, None
    
    # Extrai APENAS dígitos para cálculo de faltantes (mais seguro)
    digitos_vela_str = ''.join(c for c in vela_str if c.isdigit())
    digitos_vela = [int(d) for d in digitos_vela_str]
    
    digitos_horario_str = ''.join(c for c in horario_str if c.isdigit())
    digitos_horario = [int(d) for d in digitos_horario_str]
    
    # Evita processar se não houver dígitos suficientes (segurança)
    if not digitos_vela or not digitos_horario:
        return None, None, None, None
    
    faltantes_V, soma_VT = calcular_faltantes_seletivos(digitos_vela)
    faltantes_H, soma_HT = calcular_faltantes_seletivos(digitos_horario)
    
    r_bruto = (ultimos_dois_rodada * 0.6) + vela_inteira + minuto_original
    r_formatado = formatar_resultado_r(r_bruto)
    
    horarios_brutos = []
    
    def adicionar_horario(soma: int, origem: str):
        novo_horario_dt = horario_base_dt + timedelta(minutes=soma)
        horarios_brutos.append({
            'Rodada': str(rodada),
            'Horário Focado': novo_horario_dt.strftime("%H:%M:%S"),
            'Origem': origem,
            'R': r_formatado,
            'Timestamp_dt': novo_horario_dt 
        })
        
    for v in faltantes_V:
        adicionar_horario(v, f"V x 1 (+{v}m)")
        adicionar_horario(v * 10, f"V x 10 (+{v*10}m)")
    for h in faltantes_H:
        adicionar_horario(h, f"H x 1 (+{h}m)")
        adicionar_horario(h * 10, f"H x 10 (+{h*10}m)")
        
    if soma_VT > 0:
        adicionar_horario(soma_VT, f"VT (Soma V +{soma_VT}m)")
    if soma_HT > 0:
        adicionar_horario(soma_HT, f"HT (Soma H +{soma_HT}m)")
        
    if soma_VT > 0 or soma_HT > 0:
        soma_total_media = round((soma_VT + soma_HT) / 2)
        adicionar_horario(soma_total_media, f"HM (+{soma_total_media}m)")
        
    return pd.DataFrame(horarios_brutos), faltantes_V, faltantes_H, r_formatado, horario_base_dt

# --- 2. GERENCIAMENTO DE ESTADO E CONSOLIDAÇÃO DE HISTÓRICO ---

if 'historico_alertas' not in st.session_state:
    st.session_state.historico_alertas = pd.DataFrame(columns=['Rodada', 'Horário Focado', 'Origem', 'R', 'Timestamp_dt'])

def consolidar_historico(novo_df, horario_base_dt):
    
    historico_atualizado = st.session_state.historico_alertas.copy()
    
    # 1. Limpeza: Remove alertas que já se passaram (Timestamp_dt < horario_base_dt)
    historico_atualizado = historico_atualizado[
        historico_atualizado['Timestamp_dt'] >= horario_base_dt
    ]

    # 2. União: Adiciona os novos alertas
    historico_completo = pd.concat([historico_atualizado, novo_df], ignore_index=True)
    
    # 3. Consolidação de Horário Duplicado: Unifica as rodadas e origens
    
    consolidado_dict = {}
    
    for _, row in historico_completo.iterrows():
        horario = row['Horário Focado']
        
        if horario not in consolidado_dict:
            consolidado_dict[horario] = {
                'Rodadas': {row['Rodada']},
                'Origens': {row['Origem']},
                'R': row['R'],
                'Timestamp_dt': row['Timestamp_dt']
            }
        else:
            consolidado_dict[horario]['Rodadas'].add(row['Rodada'])
            consolidado_dict[horario]['Origens'].add(row['Origem'])

    # 4. Converte o dicionário de volta para um DataFrame
    
    dados_finais = []
    for horario, data in consolidado_dict.items():
        dados_finais.append({
            'Horário Focado': horario,
            'Rodada': ', '.join(sorted(list(data['Rodadas']), key=int)), 
            'Origem': ', '.join(data['Origens']),
            'R': data['R'],
            'Timestamp_dt': data['Timestamp_dt']
        })

    historico_final = pd.DataFrame(dados_finais)
    
    # 5. Ordena pelo Timestamp e salva o estado
    historico_final = historico_final.sort_values(by='Timestamp_dt').reset_index(drop=True)
    
    st.session_state.historico_alertas = historico_final

# --- 3. INTERFACE STREAMLIT ---

st
