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
    valor_original = int(str_faltantes)
    
    valor_minimo_bruto = valor_original * 0.80
    valor_minimo = round(valor_minimo_bruto)
    
    return f"{valor_minimo} a {valor_original}x"

@st.cache_data(show_spinner=False)
def calcular_faltantes_seletivos(digitos_presentes: List[int]) -> Tuple[List[int], int]:
    """Identifica EXATAMENTE dois números faltantes (Sequência de 4, sem 0 no resultado)."""
    # ... (Lógica inalterada, mantida por brevidade) ...
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
# --- NOVA LÓGICA DE CONFLUÊNCIA NUMÉRICA (C) ---
# --------------------------------------------------------------------------------------

def gerar_alertas_confluencia(rodada_completa: int, vela_str: str, horario_base_dt: datetime) -> List[Dict[str, Any]]:
    """
    Gera alertas de Confluência (CN) baseados em igualdades em pares de dígitos.
    Os alertas são gerados apenas se houver 2 ou mais ocorrências do par.
    Se o novo horário cair no passado, avança 1 hora.
    """
    confluencias = []
    horario_base_str = horario_base_dt.strftime("%H:%M:%S")

    # 1. Análise da Vela (XX.XXx)
    # Ex: 26.26x -> Pares 26
    vela_match = re.search(r'(\d{2})\.(\d{2})x', vela_str)
    if vela_match and vela_match.group(1) == vela_match.group(2):
        novo_minuto = int(vela_match.group(1))
        confluencias.append({'Origem_C': 'CN(Vela)', 'Novo_Minuto': novo_minuto})
    
    # 2. Análise do Horário (HH:MM:SS)
    # Ex: 16:12:12 -> Minuto 12 e Segundo 12 são iguais
    minuto_str = horario_base_dt.strftime("%M")
    segundo_str = horario_base_dt.strftime("%S")
    if minuto_str == segundo_str:
        novo_minuto = int(minuto_str)
        confluencias.append({'Origem_C': 'CN(H:M=S)', 'Novo_Minuto': novo_minuto})
        
    # 3. Análise dos 2 Últimos da Rodada (XX)
    # A rodada é um número grande. A confluência ocorre *dentro* dos últimos 2 dígitos (não aplicável).
    # Como a regra é "igualdades em duas ou mais decimais", e a Rodada é um inteiro,
    # presumimos que a regra se aplica a repetições de dígitos dentro dos últimos 2. 
    # Ex: Rodada 88 (não é o caso do 85)
    ultimos_dois_rodada = rodada_completa % 100
    if ultimos_dois_rodada >= 0: # Sempre verdadeiro, mas para análise
        d1 = ultimos_dois_rodada // 10
        d2 = ultimos_dois_rodada % 10
        if d1 == d2:
             novo_minuto = d1 * 11 % 60 # Ex: 88 -> minuto 88 % 60 = 28. (usando apenas o digito repetido)
             confluencias.append({'Origem_C': 'CN(Rodada)', 'Novo_Minuto': novo_minuto})
             
    # --- Geração dos Horários-Alvo ---
    alertas_confluencia = []
    horario_processamento_dt = datetime.now()

    for item in confluencias:
        novo_minuto = item['Novo_Minuto'] % 60 # Garante que o minuto esteja entre 0-59
        
        # Cria o novo timestamp, mantendo a Hora, Segundo e Dia do Horário Base
        horario_alvo_dt = horario_base_dt.replace(minute=novo_minuto, second=horario_base_dt.second)
        
        # Verifica a Regra: Se o horário gerado já passou, joga 1 hora para frente.
        # Compara com o horário ATUAL de processamento (datetime.now())
        if horario_alvo_dt < horario_processamento_dt:
            horario_alvo_dt += timedelta(hours=1)
        
        alertas_confluencia.append({
            'Timestamp_dt': horario_alvo_dt,
            'Horário Focado': horario_alvo_dt.strftime("%H:%M:%S"),
            'Origem_C': item['Origem_C'],
        })

    return alertas_confluencia

# --------------------------------------------------------------------------------------
# --- BLOCO ESTÁTICO E FALTANTES (Inalterados) ---
# --------------------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def obter_analise_finais_estatica() -> Tuple[pd.DataFrame, Dict[int, int], int]:
    # ... (Lógica inalterada) ...
    
    # Dicionário de mapeamento: Final de Minuto (chave) -> Rank (valor)
    rank_finais: Dict[int, int] = {
        8: 1,  # T1
        7: 2,  # T2
        0: 3,  # T3
        2: 4,  # T4
        9: 5,  # T5
    }
    
    top_1_minuto_completo = 50 
    
    dados_exibicao = [
        {'Sinal': "🎯", 'Minuto Exemplo': f"{top_1_minuto_completo:02d}", 'Final': f"{0} (Minuto Isolado)"},
        {'Sinal': "🔥", 'Minuto Exemplo': "08", 'Final': 'T1(8)'},
        {'Sinal': "🔥", 'Minuto Exemplo': "07", 'Final': 'T2(7)'},
        {'Sinal': "🔥", 'Minuto Exemplo': "00", 'Final': 'T3(0)'}, 
        {'Sinal': "🔥", 'Minuto Exemplo': "02", 'Final': 'T4(2)'},
        {'Sinal': "🔥", 'Minuto Exemplo': "09", 'Final': 'T5(9)'},
    ]
    df_top_5_display = pd.DataFrame(dados_exibicao)
        
    return df_top_5_display, rank_finais, top_1_minuto_completo

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
    # faltantes_H, soma_HT = calcular_faltantes_seletivos(digitos_horario) # Não usado na geração de alertas
    
    cotacao_C = calcular_cotacao(faltantes_V)
    
    r_bruto = (ultimos_dois_rodada * 0.6) + vela_inteira + minuto_original
    r_formatado = formatar_resultado_r(r_bruto)
    
    horarios_brutos_list = []
    
    # --- 1. GERAÇÃO DE ALERTAS DE FALTANTES (V e VT) ---
    def adicionar_horario_faltante(soma: int, origem_completa: str):
        novo_horario_dt = horario_base_dt + timedelta(minutes=soma)
        origem_simples = origem_completa.split(' ')[0] 
        
        horarios_brutos_list.append({
            'Timestamp_dt': novo_horario_dt, 
            'Origem_Bruta': origem_simples,
            'Rodada': str(rodada),
            'R': r_formatado,
            'C': cotacao_C,
            'Origem_C': '' # Campo vazio para Faltantes
        })
        
    for v in faltantes_V:
        adicionar_horario_faltante(v, f"V x 1 (+{v}m)")
        adicionar_horario_faltante(v * 10, f"V x 10 (+{v*10}m)")
        
    if soma_VT > 0:
        adicionar_horario_faltante(soma_VT, f"VT (Soma V +{soma_VT}m)")

    # --- 2. GERAÇÃO DE ALERTAS DE CONFLUÊNCIA NUMÉRICA (C) ---
    alertas_confluencia = gerar_alertas_confluencia(rodada, vela_str, horario_base_dt)
    
    for alerta_c in alertas_confluencia:
        horarios_brutos_list.append({
            'Timestamp_dt': alerta_c['Timestamp_dt'],
            'Origem_Bruta': 'C', # Origem 'C' para Confluência Numérica
            'Rodada': str(rodada),
            'R': r_formatado, # Repete R e C para o alerta de confluência
            'C': cotacao_C,
            'Origem_C': alerta_c['Origem_C'] # A Sub-Origem para o display
        })
        
    horarios_brutos_list.sort(key=lambda x: x['Timestamp_dt'])
    
    # --- 3. CONSOLIDAÇÃO DE ALERTAS (Faltantes + Confluência) ---
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
        
        # Determina o Horário Focado do grupo (Regra do Meio ou Último)
        if len(grupo) % 2 == 1:
            meio_index = len(grupo) // 2
            horario_final_dt = grupo[meio_index]['Timestamp_dt']
        else:
            horario_final_dt = grupo[-1]['Timestamp_dt']

        origens_consolidadas = sorted(list(set(item['Origem_Bruta'] for item in grupo)))
        sub_origens_confluencia = [item['Origem_C'] for item in grupo if item['Origem_C']]
        
        r_consolidado = grupo[0]['R']
        c_consolidado = grupo[0]['C']

        horarios_consolidados.append({
            'Rodada': str(rodada),
            'Horário Focado': horario_final_dt.strftime("%H:%M:%S"),
            'Origem': ' / '.join(origens_consolidadas),
            'R': r_consolidado,
            'C': c_consolidado, 
            'Timestamp_dt': horario_final_dt,
            'Sub_Origem_C': ' / '.join(sorted(list(set(sub_origens_confluencia)))) # Nova Coluna para Detalhe da Confluência
        })
        
        i = j
    
    return pd.DataFrame(horarios_consolidados), faltantes_V, None, r_formatado, cotacao_C, horario_base_dt


# --- 2. GERENCIAMENTO DE ESTADO E CONSOLIDAÇÃO DE HISTÓRICO ---

if 'historico_bruto' not in st.session_state:
    st.session_state.historico_bruto = pd.DataFrame(columns=['Rodada', 'Vela', 'Horario', 'Minuto'])

if 'historico_alertas' not in st.session_state:
    # Adicionando a nova coluna Sub_Origem_C
    st.session_state.historico_alertas = pd.DataFrame(columns=['Rodada', 'Horário Focado', 'Origem', 'R', 'C', 'Sinalizacao', 'Sub_Origem_C', 'Timestamp_dt'])


def consolidar_historico(novo_df, horario_base_dt, rank_finais: Dict[int, int], top_1_minuto_00_59: int):
    # ... (Lógica inalterada para ranking e consolidação de Rodadas, R, C) ...
    
    historico_atualizado = st.session_state.historico_alertas.copy()
    
    historico_atualizado = historico_atualizado[
        historico_atualizado['Timestamp_dt'] >= horario_base_dt
    ]

    historico_completo = pd.concat([historico_atualizado, novo_df], ignore_index=True)
    
    consolidado_dict = {}
    
    for _, row in historico_completo.iterrows():
        horario_focado = row['Horário Focado']
        
        minuto_focado = datetime.strptime(horario_focado, "%H:%M:%S").minute
        final_minuto = minuto_focado % 10
        
        sinalizacao = ""
        
        # 1. Prioridade Máxima: TOP 1 MINUTO ISOLADO (Sinalização Principal: T1)
        if minuto_focado == top_1_minuto_00_59:
            sinalizacao = "(T1)"
        
        # 2. Demais do TOP 5: Mapeamento pelo RANK do Final de Minuto
        elif final_minuto in rank_finais:
            rank = rank_finais[final_minuto]
            sinalizacao = f"(T{rank})"
            
        chave_consolidada = horario_focado
        
        if chave_consolidada not in consolidado_dict:
            consolidado_dict[chave_consolidada] = {
                'Rodadas': {row['Rodada']},
                'Origens': {row['Origem']},
                'R': row['R'],
                'C': row['C'],
                'Sinalizacao': sinalizacao, 
                'Sub_Origem_C': {row.get('Sub_Origem_C', '')}, # Inicializa com a Sub_Origem
                'Timestamp_dt': row['Timestamp_dt']
            }
        else:
            consolidado_dict[chave_consolidada]['Rodadas'].add(row['Rodada'])
            consolidado_dict[chave_consolidada]['Origens'].add(row['Origem'])
            consolidado_dict[chave_consolidada]['Sub_Origem_C'].add(row.get('Sub_Origem_C', ''))
            
            # Lógica de Prioridade:
            def obter_prioridade(sinal):
                if sinal == "(T1)": return 0
                match = re.search(r'\(T(\d)\)', sinal)
                if match: return int(match.group(1))
                return 99

            prioridade_nova = obter_prioridade(sinalizacao)
            prioridade_atual = obter_prioridade(consolidado_dict[chave_consolidada]['Sinalizacao'])
            
            if prioridade_nova < prioridade_atual:
                consolidado_dict[chave_consolidada]['Sinalizacao'] = sinalizacao
            

    dados_finais = []
    for horario, data in consolidado_dict.items():
        # Limpa e consolida Sub_Origem_C, removendo strings vazias e duplicatas
        sub_origens_limpas = [s for s in data['Sub_Origem_C'] if s]
        
        dados_finais.append({
            'Horário Focado': horario,
            'Rodada': ', '.join(sorted(list(data['Rodadas']), key=int)), 
            'Origem': ' / '.join(data['Origens']),
            'R': data['R'],
            'C': data['C'],
            'Sinalização': data['Sinalizacao'],
            'Sub_Origem_C': ' / '.join(sorted(list(set(sub_origens_limpas)))),
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
                
                # 2. Obtém a Análise Estática do Top 5
                df_top_minutos_completos, rank_finais, top_1_minuto_completo = obter_analise_finais_estatica()
                
                # 3. Gera os Alertas (Faltantes + Confluência)
                novo_df_bruto, faltantes_V, _, r_final, cotacao_final, horario_base_dt = analisar_e_gerar_alertas(rodada, vela_input, horario_input)
                
                if novo_df_bruto is not None and not novo_df_bruto.empty:
                    
                    # 4. Consolida Alertas e aplica Sinalização
                    consolidar_historico(novo_df_bruto, horario_base_dt, rank_finais, top_1_minuto_completo)
                    
                    st.success(f"Rodada {rodada} adicionada. Alertas atualizados no corpo principal e estatísticas na barra lateral.")

                    # --- EXIBIÇÃO DE ESTATÍSTICAS E METRICAS NA BARRA LATERAL (Sidebar) ---
                    with st.sidebar:
                        st.subheader("💡 Última Análise")
                        col1_s, col2_s = st.columns(2)
                        with col1_s:
                            st.metric(label=f"Resultado R", value=r_final)
                        with col2_s:
                            st.metric(label="Cotação (C)", value=cotacao_final)
                        st.markdown(f"**Horário Base:** {horario_input}")
                        st.markdown("---")
                        
                        st.subheader("📊 Top Minutos (Estático)")
                        st.dataframe(
                            df_top_minutos_completos,
                            hide_index=True,
                            column_config={
                                "Sinal": st.column_config.TextColumn("Emoji"), 
                                "Minuto Exemplo": st.column_config.TextColumn("Minuto Exemplo"),
                                "Final": st.column_config.TextColumn("Classificação")
                            }
                        )
                        st.info(f"Classificação dos Finais: T1(8), T2(7), T3(0), T4(2), T5(9).")
                        
                        st.markdown("---")
                        if st.button("Limpar Histórico Completo", help="Apaga todos os alertas ativos e o histórico bruto para a estatística."):
                            st.session_state.historico_alertas = pd.DataFrame(columns=['Rodada', 'Horário Focado', 'Origem', 'R', 'C', 'Sinalizacao', 'Sub_Origem_C', 'Timestamp_dt'])
                            st.session_state.historico_bruto = pd.DataFrame(columns=['Rodada', 'Vela', 'Horario', 'Minuto'])
                            st.rerun()

                else:
                    st.error("Nenhum alerta gerado ou erro na extração de dados. Verifique a Vela e o Horário.")
                    
        except ValueError:
            st.error("Erro de formato: A Rodada deve ser um número inteiro. Verifique todos os campos.")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado: {e}")

# --- 4. EXIBIÇÃO PRINCIPAL: HISTÓRICO DE ALERTAS ---

st.markdown("---")
st.subheader("🔔 Histórico de Alertas Focados (Ativos)")

if not st.session_state.historico_alertas.empty:
    
    df_exibicao = st.session_state.historico_alertas.copy()
    
    # Prepara o Horário com o Sinal (T1, T2, etc.)
    df_exibicao['Horário'] = df_exibicao['Sinalização'] + ' ' + df_exibicao['Horário Focado']
    
    # Nova coluna para a Origem de Confluência, para ser mais informativa
    df_exibicao['Confluência'] = df_exibicao['Sub_Origem_C'].apply(lambda x: x if x else '-')
    
    df_exibicao = df_exibicao.drop(columns=['Timestamp_dt', 'Rodada', 'Sinalização', 'Horário Focado', 'Sub_Origem_C']) 
    
    st.dataframe(
        df_exibicao, 
        hide_index=True,
        column_order=['Horário', 'R', 'C', 'Origem', 'Confluência'], # Confluência no final
        column_config={
            "Horário": st.column_config.TextColumn(
                "Horário Focado (Sinalizado)", 
                help="Sinalização de prioridade (T1 a T5)." 
            ),
            "Origem": st.column_config.TextColumn(
                "Origem (V, VT, C)",
                help="V=Faltantes Vela; VT=Soma Faltantes; C=Confluência Numérica"
            ),
            "Confluência": st.column_config.TextColumn(
                "Det. Confluência",
                help="Detalhes dos padrões de Confluência Numérica (Vela, H:M=S, Rodada)"
            )
        }
    )
    
else:
    st.info("Nenhuma rodada adicionada ou todos os alertas se passaram. Insira os dados para começar.")
