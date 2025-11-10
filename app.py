import streamlit as st
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any, Optional
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
    try:
        valor_original = int(str_faltantes)
    except ValueError:
        return "-" 
    
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
# --- LÓGICA DE CONFLUÊNCIA NUMÉRICA (C) ---
# --------------------------------------------------------------------------------------

def gerar_alertas_confluencia(rodada_completa: int, vela_str: str, horario_base_dt: datetime) -> List[Dict[str, Any]]:
    """Gera alertas de Confluência (CN)."""
    confluencias = []
    
    # ... (O corpo da função permanece o mesmo para velas > 10.00x)
    
    # --- 1. Análise da Vela (XX.XXx) ---
    vela_match = re.search(r'(\d{2})\.(\d{2})x', vela_str)
    if vela_match and vela_match.group(1) == vela_match.group(2):
        try:
            novo_minuto = int(vela_match.group(1))
            confluencias.append({'Origem_C': 'CN(Vela)', 'Novo_Minuto': novo_minuto})
        except ValueError:
            pass 
    
    # --- 2. Análise do Horário (HH:MM:SS) ---
    minuto_int = horario_base_dt.minute
    segundo_int = horario_base_dt.second
    hora_int = horario_base_dt.hour
    
    if minuto_int == segundo_int:
        confluencias.append({'Origem_C': 'CN(H:Residuo)', 'Novo_Minuto': hora_int})
        
    # --- 3. Análise dos 2 Últimos da Rodada (XX) ---
    ultimos_dois_rodada = rodada_completa % 100
    if ultimos_dois_rodada >= 0: 
        d1 = ultimos_dois_rodada // 10
        d2 = ultimos_dois_rodada % 10
        if d1 == d2:
             novo_minuto = d1 * 11 % 60 
             confluencias.append({'Origem_C': 'CN(Rodada)', 'Novo_Minuto': novo_minuto})
             
    # --- Geração dos Horários-Alvo (Com Regra de Avanço) ---
    alertas_confluencia = []
    horario_processamento_dt = datetime.now()

    for item in confluencias:
        novo_minuto = item['Novo_Minuto'] % 60 
        
        horario_alvo_dt = horario_base_dt.replace(minute=novo_minuto, second=horario_base_dt.second)
        
        if horario_alvo_dt < horario_processamento_dt:
            horario_alvo_dt += timedelta(hours=1)
        
        alertas_confluencia.append({
            'Timestamp_dt': horario_alvo_dt,
            'Horário Focado': horario_alvo_dt.strftime("%H:%M:%S"),
            'Origem_C': item['Origem_C'],
        })

    return alertas_confluencia

# --------------------------------------------------------------------------------------
# --- BLOCO DE ANÁLISE ESTÁTICA (T1-T5) ---
# --------------------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def obter_analise_finais_estatica() -> Tuple[pd.DataFrame, Dict[int, int], int]:
    """Retorna o Top 5 de minutos (00-59) baseado na análise estática de frequência."""
    
    rank_finais: Dict[int, int] = {
        3: 1,  # T1
        0: 2,  # T2
        2: 3,  # T3
        6: 4,  # T4
        7: 5,  # T5
    }
    
    top_1_minuto_completo = 17 
    
    dados_exibicao = [
        {'Sinal': "🎯", 'Minuto Exemplo': f"{top_1_minuto_completo:02d}", 'Final': f"{7} (Minuto Isolado)"},
        {'Sinal': "🔥", 'Minuto Exemplo': "03", 'Final': 'T1(3)'},
        {'Sinal': "🔥", 'Minuto Exemplo': "00", 'Final': 'T2(0)'},
        {'Sinal': "🔥", 'Minuto Exemplo': "02", 'Final': 'T3(2)'}, 
        {'Sinal': "🔥", 'Minuto Exemplo': "06", 'Final': 'T4(6)'},
        {'Sinal': "🔥", 'Minuto Exemplo': "07", 'Final': 'T5(7)'},
    ]
    df_top_5_display = pd.DataFrame(dados_exibicao)
        
    return df_top_5_display, rank_finais, top_1_minuto_completo

# --------------------------------------------------------------------------------------
# --- FUNÇÃO PRINCIPAL DE ANÁLISE (COM FILTRO) ---
# --------------------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def analisar_e_gerar_alertas(rodada, vela_str, horario_str):
    
    # 0. PRÉ-PROCESSAMENTO
    try:
        # Normaliza vírgula para ponto e remove 'x'
        parte_numerica = vela_str.replace('x', '').replace(',', '.')
        if not parte_numerica:
             raise ValueError("Vela vazia após limpeza.")
             
        vela_float_total = float(parte_numerica)
        
        # Ajusta horário para ter segundos se necessário
        if horario_str.count(':') == 1:
            horario_str += ':00'
            
        horario_base_dt = datetime.strptime(horario_str, "%H:%M:%S")
    except Exception as e:
        print(f"Erro de Validação/Parsing: {e}")
        # Retorna valores vazios e um identificador especial para a Soma RA
        return None, None, None, None, None, None, None 

    # --- NOVO FILTRO DE LÓGICA ---
    
    # 1. Lógica EXCLUSIVA para VELAS < 10.00x (apenas RA)
    if vela_float_total < 10.00:
        
        try:
            digitos_depois_virgula = re.search(r'\.(\d+)', parte_numerica)
            
            soma_digitos_fracao = 0
            if digitos_depois_virgula:
                soma_digitos_fracao = sum(int(d) for d in digitos_depois_virgula.group(1))
            
            # Se a soma for 0, não há RA.
            if soma_digitos_fracao == 0:
                return None, None, None, None, None, None, None

            horarios_brutos_list = []
            rodadas_offset = soma_digitos_fracao
            minuto_offsets = [rodadas_offset - 1, rodadas_offset, rodadas_offset + 1]
            
            for i, offset in enumerate(minuto_offsets):
                if offset > 0:
                    novo_horario_dt = horario_base_dt + timedelta(minutes=offset)
                    
                    sub_origem_ra = ""
                    if i == 0: sub_origem_ra = "Antes"
                    elif i == 1: sub_origem_ra = "Exata"
                    elif i == 2: sub_origem_ra = "Depois"
                    
                    horarios_brutos_list.append({
                        'Timestamp_dt': novo_horario_dt, 
                        'Origem_Bruta': 'RA', 
                        'Rodada': str(rodada),
                        'RA_Soma': str(soma_digitos_fracao), # Novo Campo de Saída
                        'R': '-', # Não calculado
                        'C': '-', # Não calculado
                        'Sub_Origem_C': f"RA({sub_origem_ra})" 
                    })
            
            # Consolidação dos alertas (apenas RA)
            horarios_consolidados = consolidar_alertas_internamente(horarios_brutos_list)

            # Retorna com a soma RA preenchida
            return pd.DataFrame(horarios_consolidados), None, None, '-', '-', horario_base_dt, str(soma_digitos_fracao)
            
        except Exception as e:
            print(f"Erro no cálculo RA (Rodadas Adicionadas) para vela < 10: {e}")
            return None, None, None, None, None, None, None

    # 2. Lógica COMPLETA para VELAS >= 10.00x (R, C, V, VT, Confluência)
    else:
        
        ultimos_dois_rodada = rodada % 100
        vela_inteira = int(vela_float_total)
        minuto_original = horario_base_dt.minute
        
        # --- CÁLCULOS PADRÃO (R, C, V, VT) ---
        digitos_vela_str = ''.join(c for c in parte_numerica if c.isdigit())
        digitos_vela = [int(d) for d in digitos_vela_str]
        if not digitos_vela: return None, None, None, None, None, None, None

        faltantes_V, soma_VT = calcular_faltantes_seletivos(digitos_vela)
        cotacao_C = calcular_cotacao(faltantes_V)
        r_bruto = (ultimos_dois_rodada * 0.6) + vela_inteira + minuto_original
        r_formatado = formatar_resultado_r(r_bruto)
        
        horarios_brutos_list = []
        horarios_faltantes_alvo = []
        
        # GERAÇÃO DE ALERTAS V e VT
        def adicionar_horario_faltante(soma: int, origem_completa: str):
            novo_horario_dt = horario_base_dt + timedelta(minutes=soma)
            origem_simples = origem_completa.split(' ')[0] 
            
            horarios_brutos_list.append({
                'Timestamp_dt': novo_horario_dt, 
                'Origem_Bruta': origem_simples, 
                'Rodada': str(rodada),
                'RA_Soma': '-', # Não aplicável
                'R': r_formatado,
                'C': cotacao_C,
                'Sub_Origem_C': '' 
            })
            horarios_faltantes_alvo.append(novo_horario_dt.strftime("%H:%M"))

        for v in faltantes_V:
            adicionar_horario_faltante(v, f"V x 1 (+{v}m)")
        if soma_VT > 0:
            adicionar_horario_faltante(soma_VT, f"VT (Soma V +{soma_VT}m)")

        # GERAÇÃO E FILTRO DE ALERTAS C
        alertas_confluencia = gerar_alertas_confluencia(rodada, vela_str, horario_base_dt)
        horarios_faltantes_alvo_set = set(horarios_faltantes_alvo) 

        for alerta_c in alertas_confluencia:
            horario_alvo_c_minuto = alerta_c['Timestamp_dt'].strftime("%H:%M")
            if horario_alvo_c_minuto in horarios_faltantes_alvo_set:
                horarios_brutos_list.append({
                    'Timestamp_dt': alerta_c['Timestamp_dt'],
                    'Origem_Bruta': 'C', 
                    'Rodada': str(rodada),
                    'RA_Soma': '-', # Não aplicável
                    'R': r_formatado, 
                    'C': cotacao_C,
                    'Sub_Origem_C': alerta_c['Origem_C'] 
                })
            
        horarios_brutos_list.sort(key=lambda x: x['Timestamp_dt'])
        
        # CONSOLIDAÇÃO INTERNA DE ALERTAS
        horarios_consolidados = consolidar_alertas_internamente(horarios_brutos_list)
        
        # Retorna com a Soma RA vazia
        return pd.DataFrame(horarios_consolidados), faltantes_V, None, r_formatado, cotacao_C, horario_base_dt, '-'

# --------------------------------------------------------------------------------------
# --- FUNÇÃO AUXILIAR DE CONSOLIDAÇÃO INTERNA ---
# --------------------------------------------------------------------------------------

def consolidar_alertas_internamente(horarios_brutos_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa alertas próximos em um único horário focado."""
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
        
        # O horário focado é o do meio ou o último do grupo
        horario_final_dt = grupo[len(grupo) // 2]['Timestamp_dt'] if len(grupo) % 2 == 1 else grupo[-1]['Timestamp_dt']

        # Consolida campos
        origens_consolidadas = sorted(list(set(item['Origem_Bruta'] for item in grupo)))
        sub_origens_gerais = [item['Sub_Origem_C'] for item in grupo if item['Sub_Origem_C']]
        
        # RA_Soma ou Rodada são o campo de ID agora. Prioriza RA_Soma se existir.
        id_display = next((item['RA_Soma'] for item in grupo if item['RA_Soma'] != '-'), grupo[0]['Rodada'])
        
        horarios_consolidados.append({
            'Rodada': grupo[0]['Rodada'], # Mantém a rodada para referência interna
            'RA_Soma': next((item['RA_Soma'] for item in grupo if item['RA_Soma'] != '-'), '-'), # Mantém a soma RA
            'Horário Focado': horario_final_dt.strftime("%H:%M:%S"),
            'Origem': ' / '.join(origens_consolidadas), 
            'R': grupo[0]['R'],
            'C': grupo[0]['C'], 
            'Timestamp_dt': horario_final_dt,
            'Sub_Origem_C': ' / '.join(sorted(list(set(sub_origens_gerais)))) 
        })
        
        i = j
        
    return horarios_consolidados

# --------------------------------------------------------------------------------------
# --- GERENCIAMENTO DE ESTADO E CONSOLIDAÇÃO FINAL DE HISTÓRICO ---
# --------------------------------------------------------------------------------------

if 'historico_bruto' not in st.session_state:
    st.session_state.historico_bruto = pd.DataFrame(columns=['Rodada', 'Vela', 'Horario', 'Minuto'])

if 'historico_alertas' not in st.session_state:
    # Novo formato para o histórico, incluindo RA_Soma
    st.session_state.historico_alertas = pd.DataFrame(columns=['Rodada', 'RA_Soma', 'Horário Focado', 'Origem', 'R', 'C', 'Sinalizacao', 'Sub_Origem_C', 'Timestamp_dt'])


def consolidar_historico(novo_df, horario_base_dt, rank_finais: Dict[int, int], top_1_minuto_00_59: int):
    
    historico_atualizado = st.session_state.historico_alertas.copy()
    
    # Limpa alertas passados
    historico_atualizado = historico_atualizado[
        historico_atualizado['Timestamp_dt'] >= horario_base_dt
    ].drop(columns=['Sinalização'], errors='ignore') 
    
    historico_completo = pd.concat([historico_atualizado, novo_df], ignore_index=True)
    
    consolidado_dict = {}
    
    for _, row in historico_completo.iterrows():
        horario_focado = row['Horário Focado']
        chave_consolidada = horario_focado
        
        # 3.1. Cálculo e Prioridade da Sinalização Estática (T1 a T5)
        minuto_focado = datetime.strptime(horario_focado, "%H:%M:%S").minute
        final_minuto = minuto_focado % 10
        sinalizacao = ""
        if minuto_focado == top_1_minuto_00_59:
            sinalizacao = "(T1)"
        elif final_minuto in rank_finais:
            rank = rank_finais[final_minuto]
            sinalizacao = f"(T{rank})"

        if chave_consolidada not in consolidado_dict:
            consolidado_dict[chave_consolidada] = {
                'Rodadas': {row['Rodada']},
                'RA_Soma': {row['RA_Soma']}, # Novo Campo
                'Origens': set(row['Origem'].split(' / ')), 
                'R': row['R'],
                'C': row['C'],
                'Sinalizacao': sinalizacao, 
                'Sub_Origem_C': set(s.strip() for s in row.get('Sub_Origem_C', '').split(' / ') if s.strip()), 
                'Timestamp_dt': row['Timestamp_dt']
            }
        else:
            consolidado_dict[chave_consolidada]['Rodadas'].add(row['Rodada'])
            consolidado_dict[chave_consolidada]['RA_Soma'].add(row['RA_Soma'])
            consolidado_dict[chave_consolidada]['Origens'].update(set(row['Origem'].split(' / ')))
            
            novas_sub_origens = set(s.strip() for s in row.get('Sub_Origem_C', '').split(' / ') if s.strip())
            consolidado_dict[chave_consolidada]['Sub_Origem_C'].update(novas_sub_origens)
            
            # Atualiza Sinalização (prioridade)
            def obter_prioridade(sinal):
                if sinal == "(T1)": return 0
                match = re.search(r'\(T(\d)\)', sinal)
                if match: return int(match.group(1))
                return 99

            prioridade_nova = obter_prioridade(sinalizacao)
            prioridade_atual = obter_prioridade(consolidado_dict[chave_consolidada]['Sinalizacao'])
            
            if prioridade_nova < prioridade_atual:
                consolidado_dict[chave_consolidada]['Sinalizacao'] = sinalizacao
            

    # 4. Cria o DataFrame Final para Exibição
    dados_finais = []
    for horario, data in consolidado_dict.items():
        sub_origens_limpas = [s for s in data['Sub_Origem_C'] if s]
        
        origem_final_str = ' / '.join(sorted(list(data['Origens'])))
        
        # Prioriza a RA_Soma (se for o caso) na coluna ID, caso contrário usa a Rodada
        ra_soma_exibicao = next((s for s in data['RA_Soma'] if s != '-'), '-')
        rodada_exibicao = ', '.join(sorted(list(data['Rodadas']), key=int))

        dados_finais.append({
            'Horário Focado': horario,
            'Rodada': rodada_exibicao,
            'RA_Soma': ra_soma_exibicao,
            'Origem': origem_final_str, 
            'R': data['R'],
            'C': data['C'],
            'Sinalização': data['Sinalizacao'],
            'Sub_Origem_C': ' / '.join(sorted(list(set(sub_origens_limpas)))),
            'Timestamp_dt': data['Timestamp_dt']
        })

    historico_final = pd.DataFrame(dados_finais)
    historico_final = historico_final.sort_values(by='Timestamp_dt').reset_index(drop=True)
    st.session_state.historico_alertas = historico_final

# --------------------------------------------------------------------------------------
# --- INTERFACE STREAMLIT: LAYOUT PRINCIPAL ---
# --------------------------------------------------------------------------------------

st.title("⚡ Ferramenta de Análise Contínua")

st.markdown("Cole os dados brutos (Rodada, Vela e Horário) nas três linhas abaixo.")
dados_brutos = st.text_area(
    "Cole os Dados Aqui:",
    height=150,
    placeholder="Exemplo:\n3293215\n1.38x\n11:10:23 (Vela < 10.00x acionará APENAS o cálculo de RA)"
)

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
                
                # 1. Pré-processamento e extração do valor da vela para a Sidebar
                parte_numerica = vela_input.replace('x', '').replace(',', '.')
                vela_float_total = float(parte_numerica) if parte_numerica else 0.0

                # 2. Obtém a Análise Estática do Top 5
                df_top_minutos_completos, rank_finais, top_1_minuto_completo = obter_analise_finais_estatica()
                
                # 3. Gera os Alertas (Com filtro de lógica)
                novo_df_bruto, faltantes_V, _, r_final, cotacao_final, horario_base_dt, ra_soma_final = analisar_e_gerar_alertas(rodada, vela_input, horario_input)
                
                # Atualiza R e C caso a vela fosse < 10.00
                if r_final == '-': r_final = 'N/A'
                if cotacao_final == '-': cotacao_final = 'N/A'
                
                if novo_df_bruto is not None and not novo_df_bruto.empty:
                    
                    # 4. Consolida Alertas e aplica Sinalização
                    consolidar_historico(novo_df_bruto, horario_base_dt, rank_finais, top_1_minuto_completo)
                    
                    st.success(f"Rodada {rodada} adicionada. Alertas atualizados. RA Soma: {ra_soma_final}")

                    # --- EXIBIÇÃO DE ESTATÍSTICAS E METRICAS NA BARRA LATERAL (Sidebar) ---
                    with st.sidebar:
                        st.subheader("💡 Última Análise")
                        col1_s, col2_s = st.columns(2)
                        with col1_s:
                            st.metric(label=f"Vela < 10.00x?", value="✅ SIM" if vela_float_total < 10.00 else "❌ NÃO")
                        with col2_s:
                            st.metric(label="RA Soma", value=ra_soma_final)

                        st.markdown(f"**Resultado R:** {r_final}")
                        st.markdown(f"**Cotação C:** {cotacao_final}")
                        st.markdown("---")
                        
                        st.subheader("📊 Top Minutos (Estático)")
                        st.dataframe(df_top_minutos_completos, hide_index=True)
                        st.info(f"Finais Rankeados: T1(3), T2(0), T3(2), T4(6), T5(7).")
                        
                        st.markdown("---")
                        if st.button("Limpar Histórico Completo", help="Apaga todos os alertas ativos e o histórico bruto."):
                            st.session_state.historico_alertas = pd.DataFrame(columns=['Rodada', 'RA_Soma', 'Horário Focado', 'Origem', 'R', 'C', 'Sinalizacao', 'Sub_Origem_C', 'Timestamp_dt'])
                            st.session_state.historico_bruto = pd.DataFrame(columns=['Rodada', 'Vela', 'Horario', 'Minuto'])
                            st.rerun()

                else:
                    st.warning(f"Rodada {rodada} adicionada, mas NENHUM alerta foi gerado. (Vela < 10.00x com RA Soma=0, ou sem faltantes para vela > 10.00x)")
                    
        except ValueError:
            st.error("Erro de formato: A Rodada deve ser um número inteiro. Verifique a Vela e o Horário.")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado: {e}")

# --------------------------------------------------------------------------------------
# --- EXIBIÇÃO PRINCIPAL: HISTÓRICO DE ALERTAS ---
# --------------------------------------------------------------------------------------

st.markdown("---")
st.subheader("🔔 Histórico de Alertas Focados (Ativos)")

if not st.session_state.historico_alertas.empty:
    
    df_exibicao = st.session_state.historico_alertas.copy()
    
    df_exibicao['Horário'] = df_exibicao['Sinalização'] + ' ' + df_exibicao['Horário Focado']
    df_exibicao['RA Soma'] = df_exibicao['RA_Soma'].apply(lambda x: x if x != '-' else df_exibicao['Rodada'].iloc[df_exibicao[df_exibicao['RA_Soma']=='-'].index.get_loc(df_exibicao.index[df_exibicao['RA_Soma']=='-'].get_loc(df_exibicao.index.get_loc(df_exibicao.index)[0]))])
    df_exibicao['RA Soma/Rodada'] = df_exibicao.apply(
        lambda row: row['RA_Soma'] if row['RA_Soma'] != '-' else row['Rodada'], axis=1
    )
    df_exibicao['Confluência'] = df_exibicao['Sub_Origem_C'].apply(lambda x: x if x else '-')
    
    df_exibicao = df_exibicao.drop(
        columns=['Timestamp_dt', 'Sinalização', 'Horário Focado', 'Sub_Origem_C', 'Rodada', 'RA_Soma'] 
    ) 
    
    st.dataframe(
        df_exibicao, 
        hide_index=True,
        column_order=['Horário', 'RA Soma/Rodada', 'R', 'C', 'Origem', 'Confluência'], 
        column_config={
            "Horário": st.column_config.TextColumn(
                "Horário Focado (Sinalizado)", 
                help="Sinalização de prioridade (T1 a T5)." 
            ),
             "RA Soma/Rodada": st.column_config.TextColumn(
                "RA Soma / Rodada ID",
                help="Se for RA, mostra a soma dos decimais. Caso contrário, mostra o ID da Rodada que gerou o sinal (para velas >= 10.00x)."
            ),
            "Origem": st.column_config.TextColumn(
                "Origem (RA, V, VT, C)",
                help="RA=Rodadas Adicionadas; V=Faltantes Vela; VT=Soma Faltantes; C=Confluência Numérica."
            ),
            "R": st.column_config.TextColumn("R (Resultado)"),
            "C": st.column_config.TextColumn("C (Cotação)"),
            "Confluência": st.column_config.TextColumn(
                "Det. RA/C",
                help="Detalhes do RA (Antes/Exata/Depois) ou Confluência (Vela/H:Residuo/Rodada)."
            )
        }
    )
    
else:
    st.info("Nenhuma rodada adicionada ou todos os alertas se passaram. Insira os dados para começar.")
