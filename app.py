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

# --- FUNÇÃO 1 DE ANÁLISE ESTATÍSTICA: FINAIS MINUTÁRIOS (0-9) ---

@st.cache_data(show_spinner=False)
def analisar_top_minutos_finais_pagantes(df_bruto: pd.DataFrame) -> List[int]:
    """
    Filtra o DataFrame bruto para encontrar os 5 dígitos finais de minuto mais pagantes (Vela > 10.00x).
    """
    if df_bruto.empty:
        return []

    df_bruto['Vela_Numerica'] = df_bruto['Vela'].str.replace('x', '').str.replace(',', '.').astype(float)
    
    df_pagantes = df_bruto[df_bruto['Vela_Numerica'] > 10.00].copy()
    
    if df_pagantes.empty:
        return []
        
    df_pagantes['Minuto_Final'] = df_pagantes['Minuto'] % 10
    
    contagem_minutos_finais = df_pagantes['Minuto_Final'].value_counts()
    
    top_minutos_finais = contagem_minutos_finais.head(5).index.tolist()
    
    return top_minutos_finais

# --- FUNÇÃO 2 DE ANÁLISE ESTATÍSTICA: MINUTOS COMPLETOS (00-59) ---

@st.cache_data(show_spinner=False)
def analisar_top_minutos_completos(df_bruto: pd.DataFrame) -> pd.DataFrame:
    """
    Filtra o DataFrame bruto para encontrar a frequência dos minutos completos mais pagantes (Vela > 10.00x).
    Retorna um DataFrame com Minuto e Contagem.
    """
    if df_bruto.empty:
        return pd.DataFrame(columns=['Minuto', 'Contagem'])

    df_bruto['Vela_Numerica'] = df_bruto['Vela'].str.replace('x', '').str.replace(',', '.').astype(float)
    
    df_pagantes = df_bruto[df_bruto['Vela_Numerica'] > 10.00].copy()
    
    if df_pagantes.empty:
        return pd.DataFrame(columns=['Minuto', 'Contagem'])
        
    contagem_minutos = df_pagantes['Minuto'].value_counts().reset_index()
    contagem_minutos.columns = ['Minuto', 'Contagem']
    
    contagem_minutos['Minuto'] = contagem_minutos['Minuto'].apply(lambda x: f"{x:02d}")
    
    df_top_5 = contagem_minutos.head(5)
    
    return df_top_5


# --- GERAÇÃO DE ALERTAS (COM INTEGRAÇÃO DA COTAÇÃO) ---

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
        print(f"Erro de Validação na Análise: {e}")
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

# NOVO DF: Armazena o histórico BRUTO para análise estatística
if 'historico_bruto' not in st.session_state:
    st.session_state.historico_bruto = pd.DataFrame(columns=['Rodada', 'Vela', 'Horario', 'Minuto'])

# DF EXISTENTE: Armazena alertas focados
if 'historico_alertas' not in st.session_state:
    st.session_state.historico_alertas = pd.DataFrame(columns=['Rodada', 'Horário Focado', 'Origem', 'R', 'C', 'Sinalizacao', 'Timestamp_dt'])


def consolidar_historico(novo_df, horario_base_dt, top_minutos_finais_pagantes):
    
    historico_atualizado = st.session_state.historico_alertas.copy()
    
    historico_atualizado = historico_atualizado[
        historico_atualizado['Timestamp_dt'] >= horario_base_dt
    ]

    historico_completo = pd.concat([historico_atualizado, novo_df], ignore_index=True)
    
    consolidado_dict = {}
    
    for _, row in historico_completo.iterrows():
        horario_focado = row['Horário Focado']
        
        # 1. Determina a sinalização (FOGO 🔥)
        minuto_focado = datetime.strptime(horario_focado, "%H:%M:%S").minute
        final_minutario_focado = minuto_focado % 10
        
        # AQUI: Substituição de ⭐ por 🔥
        sinalizacao = "🔥" if final_minutario_focado in top_minutos_finais_pagantes else ""
        
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
            # AQUI: Substituição de ⭐ por 🔥
            if sinalizacao == "🔥":
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

# --- 3. INTERFACE STREAMLIT ---

st.title("⚡ Ferramenta de Análise Contínua")
st.markdown("Cole os dados brutos (Rodada, Vela e Horário) nas três linhas abaixo para **adicionar** novos alertas ao histórico.")

dados_brutos = st.text_area(
    "Cole os Dados Aqui:",
    height=150,
    placeholder="Exemplo:\n3269006\n45.59x\n20:07:50"
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
                
                # 1. Adiciona o dado bruto ao histórico
                horario_str_parse = horario_input
                if horario_str_parse.count(':') == 1:
                    horario_str_parse += ':00'
                    
                minuto_bruto = datetime.strptime(horario_str_parse, "%H:%M:%S").minute
                    
                novo_dado_bruto = pd.DataFrame([{
                    'Rodada': str(rodada),
                    'Vela': vela_input,
                    'Horario': horario_input,
                    'Minuto': minuto_bruto 
                }])
                st.session_state.historico_bruto = pd.concat([st.session_state.historico_bruto, novo_dado_bruto], ignore_index=True)
                
                # 2. Analisa os TOP 5 Finais Minutários e Minutos Completos
                top_minutos_finais = analisar_top_minutos_finais_pagantes(st.session_state.historico_bruto)
                df_top_minutos_completos = analisar_top_minutos_completos(st.session_state.historico_bruto)
                
                # 3. Gera os Alertas (R e C)
                novo_df_bruto, faltantes_V, faltantes_H, r_final, cotacao_final, horario_base_dt = analisar_e_gerar_alertas(rodada, vela_input, horario_input)
                
                if novo_df_bruto is not None and not novo_df_bruto.empty:
                    
                    # 4. Consolida Alertas e aplica Sinalização
                    consolidar_historico(novo_df_bruto, horario_base_dt, top_minutos_finais)
                    
                    st.success(f"Rodada {rodada} adicionada. Faltantes (V): {', '.join(map(str, faltantes_V))}. Histórico e estatísticas atualizadas.")
                    
                    st.markdown("---")
                    col1, col2, col3 = st.columns(3) 
                    with col1:
                        st.metric(label=f"Resultado R", value=r_final)
                    with col2:
                        st.metric(label="Cotação (C)", value=cotacao_final)
                    with col3:
                        st.metric(label="Horário Base", value=horario_input)
                        
                    # 5. Exibe a tabela de estatísticas
                    st.markdown("---")
                    col_estat, col_vazio = st.columns([1, 2])
                    
                    with col_estat:
                        st.subheader("📊 Top 5 Minutos Completos Pagantes")
                        st.dataframe(
                            df_top_minutos_completos,
                            hide_index=True,
                            column_config={
                                "Minuto": st.column_config.TextColumn("Minuto (00-59)"),
                                "Contagem": st.column_config.NumberColumn("Frequência")
                            }
                        )
                        
                    # AQUI: Substituição de ⭐ por 🔥
                    st.info(f"Top 5 Finais Minutários (dígitos 0-9) para 🔥: {', '.join(map(str, top_minutos_finais))}")

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
    
    df_exibicao = st.session_state.historico_alertas.copy()
    df_exibicao['Horário'] = df_exibicao['Sinalização'] + ' ' + df_exibicao['Horário Focado']
    
    df_exibicao = df_exibicao.drop(columns=['Timestamp_dt', 'Rodada', 'Sinalização', 'Horário Focado']) 
    
    st.dataframe(
        df_exibicao, 
        hide_index=True,
        column_order=['Horário', 'R', 'C', 'Origem'],
        column_config={
            # AQUI: Substituição de ⭐ por 🔥
            "Horário": st.column_config.TextColumn(
                "Horário Focado (Sinalizado)", help="Horário que coincide com um dos 5 Finais Minutários mais pagantes (🔥)"
            )
        }
    )
    
else:
    st.info("Nenhuma rodada adicionada ou todos os alertas se passaram. Insira os dados para começar.")
    
if st.button("Limpar TODO o Histórico", help="Apaga todos os alertas ativos e o histórico bruto para a estatística."):
    st.session_state.historico_alertas = pd.DataFrame(columns=['Rodada', 'Horário Focado', 'Origem', 'R', 'C', 'Sinalizacao', 'Timestamp_dt'])
    st.session_state.historico_bruto = pd.DataFrame(columns=['Rodada', 'Vela', 'Horario', 'Minuto'])
    st.rerun()
