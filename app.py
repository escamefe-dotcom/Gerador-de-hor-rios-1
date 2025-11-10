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
        
        # Calcula a diferença em minutos (deslocamento)
        diff_minutos = (horario_alvo_dt - horario_base_dt).total_seconds() // 60
        
        # Se o horário alvo estiver no passado, avança 1 hora
        if horario_alvo_dt < horario_processamento_dt:
            horario_alvo_dt += timedelta(hours=1)
            # Recalcula a diferença após o ajuste de hora
            diff_minutos = (horario_alvo_dt - horario_base_dt).total_seconds() // 60
        
        # A Rodada Resultante só é registrada se houver deslocamento positivo de minutos
        rodada_resultante = str(rodada_completa + diff_minutos) if diff_minutos > 0 else None
        
        alertas_confluencia.append({
            'Timestamp_dt': horario_alvo_dt,
            'Horário Focado': horario_alvo_dt.strftime("%H:%M:%S"),
            'Origem_C': item['Origem_C'],
            'Rodada_Resultante': rodada_resultante
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
# --- FUNÇÃO AUXILIAR DE CONSOLIDAÇÃO INTERNA ---
# --------------------------------------------------------------------------------------

def consolidar_alertas_internamente(horarios_brutos_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Agrupa alertas próximos em um único horário focado."""
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
        
        # O horário focado é o do meio ou o último do grupo
        horario_final_dt = grupo[len(grupo) // 2]['Timestamp_dt'] if len(grupo) % 2 == 1 else grupo[-1]['Timestamp_dt']

        # Consolida campos
        origens_consolidadas = sorted(list(set(item['Origem_Bruta'] for item in grupo)))
        sub_origens_gerais = [item['Sub_Origem_C'] for item in grupo if item['Sub_Origem_C']]
        
        # Consolida Rodada Resultante: prioriza qualquer valor não nulo no grupo
        rodada_resultante = next((item['Rodada_Resultante'] for item in grupo if item.get('Rodada_Resultante') is not None), None)

        horarios_consolidados.append({
            'Rodada': grupo[0]['Rodada'], # Rodada Original
            'RA_Soma': next((item['RA_Soma'] for item in grupo if item['RA_Soma'] != '-'), '-'), 
            'Horário Focado': horario_final_dt.strftime("%H:%M:%S"),
            'Origem': ' / '.join(origens_consolidadas), 
            'R': grupo[0]['R'],
            'C': grupo[0]['C'], 
            'Timestamp_dt': horario_final_dt,
            'Sub_Origem_C': ' / '.join(sorted(list(set(sub_origens_gerais)))),
            'Rodada_Resultante': rodada_resultante, 
            'Sinalizacao': '', # Inicializa com string vazia
            'Resultado_Vela': '-', # Inicializa com '-'
        })
        
        i = j
        
    return horarios_consolidados

# --------------------------------------------------------------------------------------
# --- FUNÇÃO PRINCIPAL DE ANÁLISE (COM FILTRO) ---
# --------------------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def analisar_e_gerar_alertas(rodada, vela_str, horario_str):
    
    # 0. PRÉ-PROCESSAMENTO
    
    # Inicializa variáveis de retorno dentro do escopo da função
    r_final_func = '-'
    cotacao_final_func = '-'
    horario_base_dt_func = datetime.now()
    ra_soma_final_func = '-'
    
    try:
        rodada_int = int(rodada)
        
        # Normaliza vírgula para ponto e remove 'x'
        parte_numerica = vela_str.replace('x', '').replace(',', '.')
        if not parte_numerica:
             return None, None, None, r_final_func, cotacao_final_func, horario_base_dt_func, ra_soma_final_func
             
        vela_float_total = float(parte_numerica)
        
        # Ajusta horário para ter segundos se necessário
        if horario_str.count(':') == 1:
            horario_str += ':00'
            
        horario_base_dt_func = datetime.strptime(horario_str, "%H:%M:%S")
    except Exception as e:
        return None, None, None, r_final_func, cotacao_final_func, horario_base_dt_func, ra_soma_final_func

    # --- FILTRO DE LÓGICA ---
    
    # 1. Lógica EXCLUSIVA para VELAS < 10.00x (apenas RA)
    if vela_float_total < 10.00:
        
        try:
            digitos_depois_virgula = re.search(r'\.(\d+)', parte_numerica)
            
            soma_digitos_fracao = 0
            if digitos_depois_virgula:
                soma_digitos_fracao = sum(int(d) for d in digitos_depois_virgula.group(1))
            
            ra_soma_final_func = str(soma_digitos_fracao)
            
            # Se a soma for 0, não há RA.
            if soma_digitos_fracao == 0:
                return None, None, None, r_final_func, cotacao_final_func, horario_base_dt_func, ra_soma_final_func 

            horarios_brutos_list = []
            rodadas_offset = soma_digitos_fracao
            minuto_offsets = [rodadas_offset - 1, rodadas_offset, rodadas_offset + 1]
            
            for i, offset in enumerate(minuto_offsets):
                if offset > 0:
                    novo_horario_dt = horario_base_dt_func + timedelta(minutes=offset)
                    
                    # CÁLCULO DA RODADA RESULTANTE
                    rodada_resultante_int = rodada_int + offset
                    
                    sub_origem_ra = ""
                    if i == 0: sub_origem_ra = "Antes"
                    elif i == 1: sub_origem_ra = "Exata"
                    elif i == 2: sub_origem_ra = "Depois"
                    
                    horarios_brutos_list.append({
                        'Timestamp_dt': novo_horario_dt, 
                        'Origem_Bruta': 'RA', 
                        'Rodada': str(rodada_int),
                        'RA_Soma': str(soma_digitos_fracao), 
                        'R': '-', 
                        'C': '-', 
                        'Sub_Origem_C': f"RA({sub_origem_ra})",
                        'Rodada_Resultante': str(rodada_resultante_int), 
                    })
            
            horarios_consolidados = consolidar_alertas_internamente(horarios_brutos_list)
            df_final = pd.DataFrame(horarios_consolidados)
            # Garante que seja string para evitar conflitos na concatenação
            df_final['Rodada_Resultante'] = df_final['Rodada_Resultante'].astype(str).replace('None', None) 

            return df_final, None, None, r_final_func, cotacao_final_func, horario_base_dt_func, ra_soma_final_func
            
        except Exception as e:
            return None, None, None, r_final_func, cotacao_final_func, horario_base_dt_func, ra_soma_final_func

    # 2. Lógica COMPLETA para VELAS >= 10.00x (R, C, V, VT, Confluência)
    else:
        
        ultimos_dois_rodada = rodada_int % 100
        vela_inteira = int(vela_float_total)
        minuto_original = horario_base_dt_func.minute
        
        # --- CÁLCULOS PADRÃO (R, C, V, VT) ---
        digitos_vela_str = ''.join(c for c in parte_numerica if c.isdigit())
        digitos_vela = [int(d) for d in digitos_vela_str]
        if not digitos_vela: return None, None, None, r_final_func, cotacao_final_func, horario_base_dt_func, ra_soma_final_func

        faltantes_V, soma_VT = calcular_faltantes_seletivos(digitos_vela)
        cotacao_final_func = calcular_cotacao(faltantes_V)
        r_bruto = (ultimos_dois_rodada * 0.6) + vela_inteira + minuto_original
        r_final_func = formatar_resultado_r(r_bruto)
        
        horarios_brutos_list = []
        
        # GERAÇÃO DE ALERTAS V e VT
        def adicionar_horario_faltante(soma: int, origem_completa: str):
            novo_horario_dt = horario_base_dt_func + timedelta(minutes=soma)
            origem_simples = origem_completa.split(' ')[0] 
            
            # CÁLCULO DA RODADA RESULTANTE
            rodada_resultante_int = rodada_int + soma
            
            horarios_brutos_list.append({
                'Timestamp_dt': novo_horario_dt, 
                'Origem_Bruta': origem_simples, 
                'Rodada': str(rodada_int),
                'RA_Soma': '-', 
                'R': r_final_func,
                'C': cotacao_final_func,
                'Sub_Origem_C': '',
                'Rodada_Resultante': str(rodada_resultante_int) 
            })

        for v in faltantes_V:
            if v > 0: # Garante que só adicionamos se houver deslocamento
                 adicionar_horario_faltante(v, f"V x 1 (+{v}m)")
        if soma_VT > 0:
            adicionar_horario_faltante(soma_VT, f"VT (Soma V +{soma_VT}m)")

        # GERAÇÃO E FILTRO DE ALERTES C
        alertas_confluencia = gerar_alertas_confluencia(rodada_int, vela_str, horario_base_dt_func)

        for alerta_c in alertas_confluencia:
            # Rodada_Resultante é None se o deslocamento for 0
            rodada_resultante_c = alerta_c.get('Rodada_Resultante')
            
            horarios_brutos_list.append({
                'Timestamp_dt': alerta_c['Timestamp_dt'],
                'Origem_Bruta': 'C', 
                'Rodada': str(rodada_int),
                'RA_Soma': '-', 
                'R': r_final_func, 
                'C': cotacao_final_func,
                'Sub_Origem_C': alerta_c['Origem_C'],
                'Rodada_Resultante': rodada_resultante_c 
            })
            
        horarios_brutos_list.sort(key=lambda x: x['Timestamp_dt'])
        
        # CONSOLIDAÇÃO INTERNA DE ALERTAS
        horarios_consolidados = consolidar_alertas_internamente(horarios_brutos_list)
        
        df_final = pd.DataFrame(horarios_consolidados)
        # Garante que seja string para evitar conflitos na concatenação
        df_final['Rodada_Resultante'] = df_final['Rodada_Resultante'].astype(str).replace('None', None) 
        
        return df_final, faltantes_V, None, r_final_func, cotacao_final_func, horario_base_dt_func, ra_soma_final_func

# --------------------------------------------------------------------------------------
# --- GERENCIAMENTO DE ESTADO E CONSOLIDAÇÃO FINAL DE HISTÓRICO ---
# --------------------------------------------------------------------------------------

COLUNAS_ESTADO = [
    'Rodada', 'RA_Soma', 'Horário Focado', 'Origem', 'R', 'C', 
    'Sinalizacao', 'Sub_Origem_C', 'Timestamp_dt', 'Resultado_Vela', 'Rodada_Resultante'
]

# **Inicialização forçada com tipos 'object' para máxima compatibilidade**
if 'historico_alertas' not in st.session_state:
    st.session_state.historico_alertas = pd.DataFrame(columns=COLUNAS_ESTADO)
    tipo_forca = {col: 'object' for col in COLUNAS_ESTADO}
    st.session_state.historico_alertas = st.session_state.historico_alertas.astype(tipo_forca)


def consolidar_historico(novo_df, horario_base_dt, rank_finais: Dict[int, int], top_1_minuto_00_59: int):
    
    historico_atualizado = st.session_state.historico_alertas.copy()
    
    # 1. Garante que todas as colunas essenciais existem em AMBOS os DataFrames
    for col in COLUNAS_ESTADO:
        if col not in novo_df.columns: 
            if col in ['R', 'C', 'RA_Soma', 'Resultado_Vela']:
                novo_df[col] = '-'
            elif col in ['Sinalizacao', 'Sub_Origem_C', 'Origem']:
                novo_df[col] = ''
            elif col in ['Timestamp_dt', 'Rodada_Resultante']:
                novo_df[col] = None 
    
    # Filtra alertas antigos
    historico_atualizado = historico_atualizado[
        historico_atualizado['Timestamp_dt'] >= horario_base_dt.replace(second=0, microsecond=0)
    ].copy()
    
    # 2. Concatenação de DataFrames
    novo_df_limpo = novo_df[COLUNAS_ESTADO].copy()
    
    # Preenche NaNs/Nones com strings compatíveis para evitar erros de concatenação de tipos
    for col in ['Rodada_Resultante', 'RA_Soma', 'R', 'C', 'Resultado_Vela']:
         novo_df_limpo[col] = novo_df_limpo[col].fillna('-').astype(str).replace('None', '-')
         
    # Garante que as colunas string estejam com o mesmo tipo
    for col in ['Rodada', 'Origem', 'Sinalizacao', 'Sub_Origem_C']:
        historico_atualizado[col] = historico_atualizado[col].astype('object')
        novo_df_limpo[col] = novo_df_limpo[col].astype('object')


    historico_completo = pd.concat([historico_atualizado, novo_df_limpo], ignore_index=True)
    
    Consolidado_dict = {} 
    
    # 3. Processamento e Consolidação
    for _, row in historico_completo.iterrows():
        horario_focado = row['Horário Focado']
        chave_consolidada = horario_focado
        
        try:
            minuto_focado = datetime.strptime(horario_focado, "%H:%M:%S").minute
        except ValueError:
            minuto_focado = -1
            
        final_minuto = minuto_focado % 10
        sinalizacao = ""
        if minuto_focado == top_1_minuto_00_59:
            sinalizacao = "(T1)"
        elif final_minuto in rank_finais:
            rank = rank_finais[final_minuto]
            sinalizacao = f"(T{rank})"

        rodada_resultante_limpa = str(row.get('Rodada_Resultante', '-')).replace('None', '-')
        
        if chave_consolidada not in Consolidado_dict:
            Consolidado_dict[chave_consolidada] = {
                'Rodadas': {row['Rodada']}, 
                'Origens': set(row['Origem'].split(' / ')), 
                'R': row['R'],
                'C': row['C'],
                'Sinalizacao': sinalizacao, 
                'Sub_Origem_C': set(s.strip() for s in str(row.get('Sub_Origem_C', '')).split(' / ') if s.strip()), 
                'Timestamp_dt': row['Timestamp_dt'],
                'Resultado_Vela': row.get('Resultado_Vela', '-'),
                'Rodadas_Resultantes': {rodada_resultante_limpa} 
            }
        else:
            Consolidado_dict[chave_consolidada]['Rodadas'].add(row['Rodada'])
            Consolidado_dict[chave_consolidada]['Origens'].update(set(row['Origem'].split(' / ')))
            
            if rodada_resultante_limpa != '-':
                Consolidado_dict[chave_consolidada]['Rodadas_Resultantes'].add(rodada_resultante_limpa)
            
            novas_sub_origens = set(s.strip() for s in str(row.get('Sub_Origem_C', '')).split(' / ') if s.strip())
            Consolidado_dict[chave_consolidada]['Sub_Origem_C'].update(novas_sub_origens)
            
            def obter_prioridade(sinal):
                if sinal == "(T1)": return 0
                match = re.search(r'\(T(\d)\)', sinal)
                if match: return int(match.group(1))
                return 99

            prioridade_nova = obter_prioridade(sinalizacao)
            prioridade_atual = obter_prioridade(Consolidado_dict[chave_consolidada]['Sinalizacao'])
            
            if prioridade_nova < prioridade_atual:
                Consolidado_dict[chave_consolidada]['Sinalizacao'] = sinalizacao
            
            if Consolidado_dict[chave_consolidada]['Resultado_Vela'] == '-' and row.get('Resultado_Vela', '-') != '-':
                 Consolidado_dict[chave_consolidada]['Resultado_Vela'] = row['Resultado_Vela']
            

    dados_finais = []
    for horario, data in Consolidado_dict.items():
        sub_origens_limpas = [s for s in data['Sub_Origem_C'] if s]
        origem_final_str = ' / '.join(sorted(list(data['Origens'])))
        
        rodadas_resultantes_validas = [r for r in data['Rodadas_Resultantes'] if r != '-']
        
        if rodadas_resultantes_validas:
            id_origem_final = ', '.join(sorted(list(set(rodadas_resultantes_validas)), key=int))
        else:
            id_origem_final = ', '.join(sorted(list(data['Rodadas']), key=int))
            
        dados_finais.append({
            'Horário Focado': horario,
            'ID de Origem': id_origem_final, 
            'Origem': origem_final_str, 
            'R': data['R'],
            'C': data['C'],
            'Sinalizacao': data['Sinalizacao'], # Mantém o nome original para o estado
            'Sub_Origem_C': ' / '.join(sorted(list(set(sub_origens_limpas)))),
            'Timestamp_dt': data['Timestamp_dt'],
            'Resultado_Vela': data['Resultado_Vela']
        })

    historico_final = pd.DataFrame(dados_finais)
    
    # Garante que TODAS as colunas de estado estejam presentes antes de salvar na session state
    for col in COLUNAS_ESTADO:
        if col not in historico_final.columns:
            historico_final[col] = '-' if col in ['R', 'C', 'RA_Soma', 'Resultado_Vela'] else None
            
    historico_final = historico_final.sort_values(by='Timestamp_dt').reset_index(drop=True)
    
    st.session_state.historico_alertas = historico_final


# --------------------------------------------------------------------------------------
# --- 4. INTERFACE STREAMLIT: LAYOUT PRINCIPAL E GERAÇÃO DE ALERTAS ---
# --------------------------------------------------------------------------------------

st.title("⚡ Ferramenta de Análise Contínua")

st.markdown("Cole os dados brutos (**Rodada**, **Vela** e **Horário**) nas três linhas abaixo.")
dados_brutos = st.text_area(
    "Cole os Dados Aqui:",
    height=150,
    placeholder="Exemplo:\n3293215\n1.38x\n11:10:23 (Vela < 10.00x acionará APENAS o cálculo de RA)"
)

if st.button("Adicionar Rodada e Gerar Alertas", type="primary"):
    
    linhas = dados_brutos.strip().split('\n')
    
    if len(linhas) < 3:
        st.error("Por favor, cole os três dados em linhas separadas: **Rodada**, **Vela** e **Horário**.")
    else:
        rodada_input = linhas[0].strip()
        vela_input = linhas[1].strip()
        horario_input = linhas[2].strip()

        try:
            rodada_int = int(rodada_input)
            
            with st.spinner(f'Analisando Rodada {rodada_int} e consolidando histórico...'): 
                
                parte_numerica = vela_input.replace('x', '').replace(',', '.')
                vela_float_total = float(parte_numerica) if parte_numerica else 0.0

                df_top_minutos_completos, rank_finais, top_1_minuto_completo = obter_analise_finais_estatica()
                
                # INICIALIZAÇÃO CORRIGIDA AQUI
                r_final = 'N/A'
                cotacao_final = 'N/A'
                horario_base_dt = datetime.now()
                
                novo_df_bruto, faltantes_V, _, r_final_retorno, cotacao_final_retorno, horario_base_dt, ra_soma_final = analisar_e_gerar_alertas(rodada_input, vela_input, horario_input)
                
                # Atualiza as variáveis que serão exibidas
                if r_final_retorno is not None and r_final_retorno != '-':
                    r_final = r_final_retorno
                if cotacao_final_retorno is not None and cotacao_final_retorno != '-':
                    cotacao_final = cotacao_final_retorno
                
                
                if novo_df_bruto is not None and not novo_df_bruto.empty:
                    
                    consolidar_historico(novo_df_bruto, horario_base_dt, rank_finais, top_1_minuto_completo)
                    
                    st.success(f"Rodada {rodada_input} adicionada. Alertas atualizados. RA Soma: {ra_soma_final}")

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
                            st.session_state.historico_alertas = pd.DataFrame(columns=COLUNAS_ESTADO)
                            tipo_forca = {col: 'object' for col in COLUNAS_ESTADO}
                            st.session_state.historico_alertas = st.session_state.historico_alertas.astype(tipo_forca)
                            st.rerun()

                else:
                    st.warning(f"Rodada {rodada_input} adicionada, mas NENHUM alerta foi gerado. (Vela < 10.00x com RA Soma=0, ou sem faltantes para vela > 10.00x)")
                    
        except ValueError:
            st.error("Erro de formato: A Rodada deve ser um número inteiro. Verifique a Vela e o Horário.")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado: {e}")


# --------------------------------------------------------------------------------------
# --- 5. EXIBIÇÃO PRINCIPAL: HISTÓRICO DE ALERTAS ---
# --------------------------------------------------------------------------------------

st.markdown("---")
st.subheader("🔔 Histórico de Alertas Focados (Ativos)")

if not st.session_state.historico_alertas.empty:
    
    df_exibicao = st.session_state.historico_alertas.copy()
    
    # Cria as colunas que serão exibidas
    df_exibicao['Horário'] = df_exibicao['Sinalizacao'] + ' ' + df_exibicao['Horário Focado']
    df_exibicao['Resultado Vela'] = df_exibicao['Resultado_Vela']
    df_exibicao['ID de Origem'] = df_exibicao['ID de Origem']
    df_exibicao['Det. RA/C'] = df_exibicao['Sub_Origem_C'].apply(lambda x: x if x else '-')
    
    colunas_finais = ['Horário', 'Resultado Vela', 'ID de Origem', 'R', 'C', 'Origem', 'Det. RA/C']
    
    # Filtra apenas as colunas que serão exibidas
    df_exibicao = df_exibicao[colunas_finais]
    
    st.dataframe(
        df_exibicao, 
        hide_index=True,
        column_order=colunas_finais, 
        column_config={
            "Horário": st.column_config.TextColumn(
                "Horário Focado (Sinalizado)", 
                help="Sinalização de prioridade (T1 a T5)." 
            ),
             "Resultado Vela": st.column_config.TextColumn(
                "Resultado Vela (N/A)",
                help="Resultado da vela. (A inserção manual foi removida para estabilidade.)",
                width="small" 
            ),
             "ID de Origem": st.column_config.TextColumn(
                "Rodada Resultante",
                help="Rodada Resultante (Rodada Original + Minutos Deslocados)."
            ),
            "Origem": st.column_config.TextColumn(
                "Origem (RA, V, VT, C)",
                help="RA=Rodadas Adicionadas; V=Faltantes Vela; VT=Soma Faltantes; C=Confluência Numérica.",
                width="small"
            ),
            "R": st.column_config.TextColumn("R (Resultado)"),
            "C": st.column_config.TextColumn("C (Cotação)"),
            "Det. RA/C": st.column_config.TextColumn(
                "Det. RA/C",
                help="Detalhes do RA (Antes/Exata/Depois) ou Confluência (Vela/H:Residuo/Rodada)."
            )
        }
    )
    
else:
    st.info("Nenhuma rodada adicionada ou todos os alertas se passaram. Insira os dados para começar.")
