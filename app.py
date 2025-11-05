import streamlit as st
from datetime import datetime, timedelta
from typing import List, Tuple
import pandas as pd
import re

# Define o layout e tema padrão da página ANTES de qualquer coisa
st.set_page_config(
    page_title="Ferramenta de Análise", 
    layout="centered",
    initial_sidebar_state="auto", 
)

# --- FUNÇÕES DE CÁLCULO GERAL ---

def calcular_cotacao(faltantes: List[int]) -> str:
    """Calcula a Cotação (C) com base nos dois faltantes, aplicando um desconto de 20%."""
    if len(faltantes) != 2:
        return "-"
    
    str_faltantes = "".join(map(str, faltantes))
    valor_original = int(str_faltantes)
    
    valor_minimo_bruto = valor_original * 0.80
    valor_minimo = round(valor_minimo_bruto)
    
    return f"{valor_minimo} a {valor_original}x"

@st.cache_data(show_spinner=False)
def calcular_faltantes_seletivos(digitos_presentes: List[int]) -> Tuple[List[int], int]:
    """Identifica EXATAMENTE dois números faltantes (Sequência de 4, sem 0 no resultado)."""
    digitos_presentes = set(digitos_presentes)
    
    if len(digitos_presentes) < 2:
        return [], 0
    
    todos_digitos = set(range(10))
    faltantes_globais = todos_digitos - digitos_presentes
    
    melhor_sequencia_faltantes = None
    melhor_inicio = 10 
    
    for inicio_seq in range(10):
        
        sequencia_alvo = [(inicio_seq + i) % 10 for i in range(4)]
        
        digitos_presentes_na_seq = [d for d in sequencia_alvo if d in digitos_presentes]
        digitos_faltantes_na_seq = [d for d in sequencia_alvo if d in faltantes_globais]
        
        if len(digitos_presentes_na_seq) == 2 and len(digitos_faltantes_na_seq) == 2:
            
            if 0 not in digitos_faltantes_na_seq:
                
                if inicio_seq < melhor_inicio:
                    melhor_inicio = inicio_seq
                    melhor_sequencia_faltantes = sorted(digitos_faltantes_na_seq)
            
    if melhor_sequencia_faltantes:
        faltantes_finais = melhor_sequencia_faltantes
    else:
        faltantes_finais = sorted([f for f in faltantes_globais if f != 0])[:2] 
        
    soma_total = sum(faltantes_finais)

    return faltantes_finais, soma_total

@st.cache_data(show_spinner=False)
def formatar_resultado_r(r_bruto: float) -> str:
    """Formata o resultado R."""
    if r_bruto <= 99.99:
        return str(int(r_bruto))
    else:
        parte_inteira = int(r_bruto)
        soma_digitos = sum(int(d) for d in str(parte_inteira))
        parte_decimal = r_bruto - parte_inteira
        
        return str(round(soma_digitos + parte_decimal, 1))

# --------------------------------------------------------------------------------------
# --- NOVO BLOCO DE ANÁLISE ESTÁTICA (BASEADO NA FREQUÊNCIA DO TOP 5) ---
# --------------------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def obter_analise_finais_estatica() -> Tuple[pd.DataFrame, List[int], int]:
    """
    Retorna o Top 5 de minutos (00-59) baseado na análise estática de frequência
    (Finais de Minuto 7, 8, 0, 2, 3) para sinalização.
    """
    
    # DADOS OBTIDOS DA ANÁLISE DE FREQUÊNCIA DAS SUAS IMAGENS:
    finais_analisados = [7, 8, 0, 2, 3] # Top 5 Finais de Minuto mais frequentes
    
    # O Minuto 07 foi o mais frequente (Top 1) na análise inicial de 00 a 09.
    # Usamos o final 7 como base para o Top 1 de sinalização.
    top_1_final_minuto = 7 
    top_1_minuto_completo = 7 # Usamos 07 como exemplo de Top 1 completo
    
    # Lista de todos os minutos completos (00-59) que terminam nos finais do Top 5
    top_minutos_completos_int = []
    for final in finais_analisados:
        top_minutos_completos_int.extend([m for m in range(60) if m % 10 == final])
        
    # Remove o Top 1 (07) da lista de Top 5 (para evitar sinalização dupla)
    top_minutos_completos_int = [m for m in top_minutos_completos_int if m != top_1_minuto_completo]
    
    # Criando o DataFrame para exibição (apenas para fins visuais na sidebar)
    dados_exibicao = [
        {'Minuto': f"🚀 {top_1_minuto_completo:02d}", 'Tipo de Minuto': f"Final {top_1_final_minuto} (Top 1)"},
        {'Minuto': f"🔥 {8:02d}", 'Tipo de Minuto': 'Final 8'},
        {'Minuto': f"🔥 {0:02d}", 'Tipo de Minuto': 'Final 0'},
        {'Minuto': f"🔥 {2:02d}", 'Tipo de Minuto': 'Final 2'},
        {'Minuto': f"🔥 {3:02d}", 'Tipo de Minuto': 'Final 3'},
    ]
    df_top_5_display = pd.DataFrame(dados_exibicao)
        
    return df_top_5_display, top_minutos_completos_int, top_1_minuto_completo

# --- FIM NOVO BLOCO ---
# --------------------------------------------------------------------------------------

# --- GERAÇÃO DE ALERTAS (COM INTEGRAÇÃO DA COTAÇÃO) ---
# ... (analisar_e_gerar_alertas permanece inalterada) ...

@st.cache_data(show_spinner=False)
def analisar_e_gerar_alertas(rodada, vela_str, horario_str):
    
    try:
        ultimos_dois_rodada = rodada % 100
        parte_numerica = vela_str.replace('x', '').replace(',', '.')
        if not parte_numerica:
             raise ValueError("Vela vazia após limpeza.")
             
        vela_inteira = int(float(parte_numerica))
        
        if horario_str.count(':') == 1:
            horario_str += ':00'
            
        horario_base_dt = datetime.strptime(horario_str, "%H:%M:%S")
        minuto_original = horario_base_dt.minute
    except ValueError as e:
        print(f"Erro de Validação na Análise de Entrada: {e}")
        return None, None, None, None, None, None
    
    digitos_vela_str = ''.join(c for c in vela_str if c.isdigit())
    digitos_vela = [int(d) for d in digitos_vela_str]
    digitos_horario_str = ''.join(c for c in horario_str if c.isdigit())
    digitos_horario = [int(d) for d in digitos_horario_str]
    
    if not digitos_vela or not digitos_horario:
        return None, None, None, None, None, None
    
    faltantes_V, soma_VT = calcular_faltantes_seletivos(digitos_vela)
    faltantes_H, soma_HT = calcular_faltantes_seletivos(digitos_horario)
    
    cotacao_C = calcular_cotacao(faltantes_V)
    
    r_bruto = (ultimos_dois_rodada * 0.6) + vela_inteira + minuto_original
    r_formatado = formatar_resultado_r(r_bruto)
    
    horarios_brutos_list = []
    
    def adicionar_horario(soma: int, origem_completa: str):
        novo_horario_dt = horario_base_dt + timedelta(minutes=soma)
        
        if origem_completa.startswith('V x'):
            origem_simples = 'V'
        elif origem_completa.startswith('H x'):
            origem_simples = 'H'
        else:
            origem_simples = origem_completa.split(' ')[0] 
        
        horarios_brutos_list.append({
            'Timestamp_dt': novo_horario_dt, 
            'Origem_Bruta': origem_simples,
            'Rodada': str(rodada),
            'R': r_formatado,
            'C': cotacao_C 
        })
        
    for v in faltantes_V:
        adicionar_horario(v, f"V x 1 (+{v}m)")
        adicionar_horario(v * 10, f"V x 10 (+{v*10}m)")
        
    if soma_VT > 0:
        adicionar_horario(soma_VT, f"VT (Soma V +{soma_VT}m)")
        
    horarios_brutos_list.sort(key=lambda x: x['Timestamp_dt'])
    
    horarios_consolidados = []
    i = 0
    while i < len(horarios_brutos_list):
        grupo = [horarios_brutos_list[i]]
        j = i + 1
        
        while j < len(horarios_brutos_list):
            diff = (horarios_brutos_list[j]['Timestamp_dt'] - horarios_brutos_list[j-1]['Timestamp_dt']).total_seconds()
            if diff <= 61: 
                grupo.append(horarios_brutos_list[j])
                j += 1
            else:
                break
        
        if len(grupo) % 2 == 1:
            meio_index = len(grupo) // 2
            horario_final_dt = grupo[meio_index]['Timestamp_dt']
        else:
            horario_final_dt = grupo[-1]['Timestamp_dt']

        origens_consolidadas = sorted(list(set(item['Origem_Bruta'] for item in grupo)))
        r_consolidado = grupo[0]['R']
        c_consolidado = grupo[0]['C']

        horarios_consolidados.append({
            'Rodada': str(rodada),
            'Horário Focado': horario_final_dt.strftime("%H:%M:%S"),
            'Origem': ' / '.join(origens_consolidadas),
            'R': r_consolidado,
            'C': c_consolidado, 
            'Timestamp_dt': horario_final_dt 
        })
        
        i = j
    
    return pd.DataFrame(horarios_consolidados), faltantes_V, faltantes_H, r_formatado, cotacao_C, horario_base_dt


# --- 2. GERENCIAMENTO DE ESTADO E CONSOLIDAÇÃO DE HISTÓRICO ---

if 'historico_bruto' not in st.session_state:
    st.session_state.historico_bruto = pd.DataFrame(columns=['Rodada', 'Vela', 'Horario', 'Minuto'])

if 'historico_alertas' not in st.session_state:
    st.session_state.historico_alertas = pd.DataFrame(columns=['Rodada', 'Horário Focado', 'Origem', 'R', 'C', 'Sinalizacao', 'Timestamp_dt'])


def consolidar_historico(novo_df, horario_base_dt, top_minutos_00_59_list: List[int], top_1_minuto_00_59: int):
    """
    Consolida o histórico de alertas, aplicando a sinalização (🚀/🔥) baseada 
    nos minutos completos (00-59) estáticos (Finais 7, 8, 0, 2, 3).
    """
    historico_atualizado = st.session_state.historico_alertas.copy()
    
    historico_atualizado = historico_atualizado[
        historico_atualizado['Timestamp_dt'] >= horario_base_dt
    ]

    historico_completo = pd.concat([historico_atualizado, novo_df], ignore_index=True)
    
    consolidado_dict = {}
    
    for _, row in historico_completo.iterrows():
        horario_focado = row['Horário Focado']
        
        # 1. Determina a sinalização (FOGUETE 🚀 ou FOGO 🔥) - AGORA USANDO LISTA ESTÁTICA
        minuto_focado = datetime.strptime(horario_focado, "%H:%M:%S").minute
        
        sinalizacao = ""
        if minuto_focado == top_1_minuto_00_59:
            sinalizacao = "🚀"
        elif minuto_focado in top_minutos_00_59_list: 
            sinalizacao = "🔥"
        
        chave_consolidada = horario_focado
        
        if chave_consolidada not in consolidado_dict:
            consolidado_dict[chave_consolidada] = {
                'Rodadas': {row['Rodada']},
                'Origens': {row['Origem']},
                'R': row['R'],
                'C': row['C'],
                'Sinalizacao': sinalizacao,
                'Timestamp_dt': row['Timestamp_dt']
            }
        else:
            consolidado_dict[chave_consolidada]['Rodadas'].add(row['Rodada'])
            consolidado_dict[chave_consolidada]['Origens'].add(row['Origem'])
            
            # Prioriza Foguete sobre Fogo
            if sinalizacao == "🚀":
                consolidado_dict[chave_consolidada]['Sinalizacao'] = "🚀"
            elif sinalizacao == "🔥" and consolidado_dict[chave_consolidada]['Sinalizacao'] != "🚀":
                consolidado_dict[chave_consolidada]['Sinalizacao'] = "🔥"


    dados_finais = []
    for horario, data in consolidado_dict.items():
        dados_finais.append({
            'Horário Focado': horario,
            'Rodada': ', '.join(sorted(list(data['Rodadas']), key=int)), 
            'Origem': ' / '.join(data['Origens']),
            'R': data['R'],
            'C': data['C'],
            'Sinalização': data['Sinalizacao'],
            'Timestamp_dt': data['Timestamp_dt']
        })

    historico_final = pd.DataFrame(dados_finais)
    
    historico_final = historico_final.sort_values(by='Timestamp_dt').reset_index(drop=True)
    
    st.session_state.historico_alertas = historico_final

# --- 3. INTERFACE STREAMLIT: LAYOUT PRINCIPAL ---

st.title("⚡ Ferramenta de Análise Contínua")

# 3.1. Campo de Inserção de Dados
st.markdown("Cole os dados brutos (Rodada, Vela e Horário) nas três linhas abaixo para **adicionar** novos alertas ao histórico.")
dados_brutos = st.text_area(
    "Cole os Dados Aqui:",
    height=150,
    placeholder="Exemplo:\n3269006\n45.59x\n20:07:50"
)

# 3.2. Botão de Ação 
if st.button("Adicionar Rodada e Atualizar Alertas", type="primary"):
    
    linhas = dados_brutos
