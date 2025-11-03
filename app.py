import streamlit as st
from datetime import datetime, timedelta
from typing import List, Tuple
import pandas as pd
import re

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
    """Calcula os alertas brutos e os consolida (minutos próximos) ANTES de retornar."""
    
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
        print(f"Erro de Validação na Análise: {e}")
        return None, None, None, None
    
    digitos_vela_str = ''.join(c for c in vela_str if c.isdigit())
    digitos_vela = [int(d) for d in digitos_vela_str]
    digitos_horario_str = ''.join(c for c in horario_str if c.isdigit())
    digitos_horario = [int(d) for d in digitos_horario_str]
    
    if not digitos_vela or not digitos_horario:
        return None, None, None, None
    
    faltantes_V, soma_VT = calcular_faltantes_seletivos(digitos_vela)
    faltantes_H, soma_HT = calcular_faltantes_seletivos(digitos_horario)
    
    r_bruto = (ultimos_dois_rodada * 0.6) + vela_inteira + minuto_original
    r_formatado = formatar_resultado_r(r_bruto)
    
    horarios_brutos_list = []
    
    def adicionar_horario(soma: int, origem: str):
        novo_horario_dt = horario_base_dt + timedelta(minutes=soma)
        horarios_brutos_list.append({
            'Timestamp_dt': novo_horario_dt, 
            'Origem_Bruta': origem,
            'Rodada': str(rodada),
            'R': r_formatado,
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
        
    horarios_brutos_list.sort(key=lambda x: x['Timestamp_dt'])
    
    # --- NOVO: Consolidação de Minutos Próximos (Lógica da V1 reintroduzida) ---
    horarios_consolidados = []
    i = 0
    while i < len(horarios_brutos_list):
        grupo = [horarios_brutos_list[i]]
        j = i + 1
        
        while j < len(horarios_brutos_list):
            # Diferença de até 61 segundos (mesmo minuto)
            diff = (horarios_brutos_list[j]['Timestamp_dt'] - horarios_brutos_list[j-1]['Timestamp_dt']).total_seconds()
            if diff <= 61: 
                grupo.append(horarios_brutos_list[j])
                j += 1
            else:
                break
        
        # Regra de Consolidação: Pega o maior/último do grupo se for par, ou o do meio se for ímpar.
        if len(grupo) % 2 == 1:
            meio_index = len(grupo) // 2
            horario_final_dt = grupo[meio_index]['Timestamp_dt']
        else:
            horario_final_dt = grupo[-1]['Timestamp_dt']

        # Consolida origens
        origens_consolidadas = sorted(list(set(item['Origem_Bruta'] for item in grupo)))

        horarios_consolidados.append({
            'Rodada': str(rodada),
            'Horário Focado': horario_final_dt.strftime("%H:%M:%S"),
            'Origem': ' / '.join(origens_consolidadas),
            'R': r_formatado,
            'Timestamp_dt': horario_final_dt 
        })
        
        i = j
    
    # Retorna o DataFrame JÁ CONSOLIDADO POR MINUTOS PRÓXIMOS
    return pd.DataFrame(horarios_consolidados), faltantes_V, faltantes_H, r_formatado, horario_base_dt

# --- 2. GERENCIAMENTO DE ESTADO E CONSOLIDAÇÃO DE HISTÓRICO ---

if 'historico_alertas' not in st.session_state:
    st.session_state.historico_alertas = pd.DataFrame(columns=['Rodada', 'Horário Focado', 'Origem', 'R', 'Timestamp_dt'])

def consolidar_historico(novo_df, horario_base_dt):
    
    historico_atualizado = st.session_state.historico_alertas.copy()
    
    # 1. Limpeza: Remove alertas que já se passaram
    historico_atualizado = historico_atualizado[
        historico_atualizado['Timestamp_dt'] >= horario_base_dt
    ]

    # 2. União: Adiciona os novos alertas (que já estão consolidados por minuto)
    historico_completo = pd.concat([historico_atualizado, novo_df], ignore_index=True)
    
    # 3. Consolidação de Rodadas: Unifica rodadas que têm o MESMO Horário Focado
    
    consolidado_dict = {}
    
    for _, row in historico_completo.iterrows():
        horario_focado = row['Horário Focado']
        
        if horario_focado not in consolidado_dict:
            consolidado_dict[horario_focado] = {
                'Rodadas': {row['Rodada']},
                'Origens': {row['Origem']},
                'R': row['R'],
                'Timestamp_dt': row['Timestamp_dt']
            }
        else:
            # Junta as rodadas e as origens
            consolidado_dict[horario_focado]['Rodadas'].add(row['Rodada'])
            consolidado_dict[horario_focado]['Origens'].add(row['Origem'])

    # 4. Converte o dicionário de volta para um DataFrame
    dados_finais = []
    for horario, data in consolidado_dict.items():
        dados_finais.append({
            'Horário Focado': horario,
            'Rodada': ', '.join(sorted(list(data['Rodadas']), key=int)), 
            'Origem': ' / '.join(data['Origens']),
            'R': data['R'],
            'Timestamp_dt': data['Timestamp_dt']
        })

    historico_final = pd.DataFrame(dados_finais)
    
    # 5. Ordena pelo Timestamp
    historico_final = historico_final.sort_values(by='Timestamp_dt').reset_index(drop=True)
    
    st.session_state.historico_alertas = historico_final

# --- 3. INTERFACE STREAMLIT ---

st.title("⚡ Ferramenta de Análise Contínua")
st.markdown("Cole os dados brutos (Rodada, Vela e Horário) nas três linhas abaixo para **adicionar** novos alertas ao histórico.")

# Novo campo único de ÁREA DE TEXTO
dados_brutos = st.text_area(
    "Cole os Dados Aqui:",
    height=150,
    placeholder="Exemplo:\n3267508\n14.99x\n09:56:31"
)

# Botão para iniciar a análise
if st.button("Adicionar Rodada e Atualizar Alertas", type="primary"):
    
    linhas = dados_brutos.strip().split('\n')
    
    if len(linhas) < 3:
        st.error("Por favor, cole os três dados em linhas separadas: Rodada, Vela e Horário.")
    else:
        rodada_input = linhas[0].strip()
        vela_input = linhas[1].strip()
        horario_input = linhas[2].strip()

        try:
            rodada = int(rodada_input)
            
            with st.spinner(f'Analisando Rodada {rodada} e consolidando histórico...'): 
                
                # 1. Calcula os novos alertas (com consolidação de minutos próximos)
                novo_df_bruto, faltantes_V, faltantes_H, r_final, horario_base_dt = analisar_e_gerar_alertas(rodada, vela_input, horario_input)
                
                if novo_df_bruto is not None and not novo_df_bruto.empty:
                    
                    # 2. Consolida, limpa o histórico e salva no estado (unificando rodadas)
                    consolidar_historico(novo_df_bruto, horario_base_dt)
                    
                    # 3. Exibição de Resumo R
                    st.success(f"Rodada {rodada} adicionada com sucesso. Histórico atualizado.")
                    
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(label=f"Resultado R da Rodada {rodada}", value=r_final)
                    with col2:
                        st.metric(label="Horário Base da Rodada", value=horario_input)
                    
                else:
                    st.error("Nenhum alerta gerado ou erro na extração de dados. Verifique a Vela e o Horário.")
                    
        except ValueError:
            st.error("Erro de formato: A Rodada deve ser um número inteiro. Verifique todos os campos.")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado: {e}")

# --- 4. EXIBIÇÃO DO HISTÓRICO ATUALIZADO ---

st.markdown("---")
st.subheader("🔔 Histórico de Alertas Focados (Ativos)")

if not st.session_state.historico_alertas.empty:
    
    df_exibicao = st.session_state.historico_alertas.drop(columns=['Timestamp_dt'])
    
    st.dataframe(
        df_exibicao, 
        hide_index=True,
        column_order=['Horário Focado', 'Rodada', 'R', 'Origem']
    )
    
else:
    st.info("Nenhuma rodada adicionada ou todos os alertas se passaram. Insira os dados para começar.")
    
if st.button("Limpar TODO o Histórico", help="Apaga todos os alertas ativos."):
    st.session_state.historico_alertas = pd.DataFrame(columns=['Rodada', 'Horário Focado', 'Origem', 'R', 'Timestamp_dt'])
    st.rerun() 
