import streamlit as st
from datetime import datetime, timedelta
from typing import List, Tuple
import pandas as pd

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
        # Nova Regra: 99 ou menos, exibir apenas o número inteiro (sem decimal).
        return str(int(r_bruto))
    else:
        # Maiores que 100 continuam com uma casa decimal (pós soma de dígitos)
        parte_inteira = int(r_bruto)
        soma_digitos = sum(int(d) for d in str(parte_inteira))
        parte_decimal = r_bruto - parte_inteira
        
        return str(round(soma_digitos + parte_decimal, 1))

@st.cache_data(show_spinner=False)
def analisar_e_gerar_alertas(rodada, vela_str, horario_str):
    """Calcula os alertas e retorna os dados brutos, incluindo o Timestamp."""
    
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
            # Esta coluna é essencial para a limpeza e ordenação
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

# Inicializa o histórico
if 'historico_alertas' not in st.session_state:
    st.session_state.historico_alertas = pd.DataFrame(columns=['Rodada', 'Horário Focado', 'Origem', 'R', 'Timestamp_dt'])

def consolidar_historico(novo_df, horario_base_dt):
    
    # Converte a coluna Timestamp_dt para datetime para comparação
    historico_atualizado = st.session_state.historico_alertas.copy()
    
    # 1. Limpeza: Remove alertas que já se passaram em relação ao novo Horário Base
    # Mantém apenas alertas cujo Timestamp_dt seja maior ou igual ao horário base
    historico_atualizado = historico_atualizado[
        historico_atualizado['Timestamp_dt'] >= horario_base_dt
    ]

    # 2. União: Adiciona os novos alertas
    historico_completo = pd.concat([historico_atualizado, novo_df], ignore_index=True)
    
    # 3. Consolidação de Horário Duplicado: Unifica as rodadas para o mesmo horário focado
    
    # Dicionário para armazenar o histórico unificado (chave: Horário Focado)
    consolidado_dict = {}
    
    for _, row in historico_completo.iterrows():
        horario = row['Horário Focado']
        
        if horario not in consolidado_dict:
            # Novo horário: inicializa o registro
            consolidado_dict[horario] = {
                'Rodadas': {row['Rodada']},
                'Origens': {row['Origem']},
                'R': row['R'],
                'Timestamp_dt': row['Timestamp_dt']
            }
        else:
            # Horário existente: adiciona a nova rodada e origem
            consolidado_dict[horario]['Rodadas'].add(row['Rodada'])
            consolidado_dict[horario]['Origens'].add(row['Origem'])

    # 4. Converte o dicionário de volta para um DataFrame para exibição
    
    dados_finais = []
    for horario, data in consolidado_dict.items():
        dados_finais.append({
            'Horário Focado': horario,
            'Rodada': ', '.join(sorted(list(data['Rodadas']), key=int)), # Ordena as rodadas
            'Origem': ', '.join(data['Origens']),
            'R': data['R'],
            'Timestamp_dt': data['Timestamp_dt']
        })

    historico_final = pd.DataFrame(dados_finais)
    
    # 5. Ordena pelo Timestamp e salva o estado
    historico_final = historico_final.sort_values(by='Timestamp_dt').reset_index(drop=True)
    
    # Atualiza o estado da sessão com o DataFrame completo, incluindo o Timestamp_dt
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
                
                # 1. Calcula os novos alertas
                novo_df_bruto, faltantes_V, faltantes_H, r_final, horario_base_dt = analisar_e_gerar_alertas(rodada, vela_input, horario_input)
                
                if novo_df_bruto is not None:
                    
                    # 2. Consolida, limpa o histórico e salva no estado
                    consolidar_historico(novo_df_bruto, horario_base_dt)
                    
                    # 3. Exibição de Resumo R (Melhoria de Formatação e Feedback)
                    st.success(f"Rodada {rodada} adicionada com sucesso. Histórico atualizado.")
                    
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(label=f"Resultado R da Rodada {rodada}", value=r_final)
                    with col2:
                        st.metric(label="Horário Base da Rodada", value=horario_input)
                    
                else:
                    st.error("Ocorreu um erro ao processar os dados. Verifique os formatos.")
                    
        except ValueError:
            st.error("Erro de formato: A Rodada deve ser um número inteiro. Verifique todos os campos.")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado: {e}")

# --- 4. EXIBIÇÃO DO HIST
