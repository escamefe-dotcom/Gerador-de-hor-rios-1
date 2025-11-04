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
    """
    Identifica EXATAMENTE dois números faltantes, priorizando o preenchimento dos menores buracos.
    """
    digitos_presentes = sorted(list(set(digitos_presentes)))
    
    if len(digitos_presentes) <= 1:
        return [], 0
    
    # Adiciona o primeiro dígito + 10 ao final para fechar o ciclo (ex: 9 -> 4 vira 9 -> 14)
    digitos_ciclicos = digitos_presentes + [digitos_presentes[0] + 10]
    
    buracos = []
    
    # 1. Identificar e listar todos os buracos (sequências faltantes)
    for i in range(len(digitos_presentes)):
        d1 = digitos_presentes[i]
        d2_real = digitos_ciclicos[i+1]
        
        diferenca = d2_real - d1
        
        if diferenca > 1:
            # Números que faltam (aplicando % 10 para mantê-los entre 0-9)
            faltantes = [(d1 + j) % 10 for j in range(1, diferenca)]
            
            buracos.append({
                'tamanho': diferenca - 1,
                'd1': d1,
                'd2': d2_real % 10,
                'faltantes': faltantes
            })

    # 2. Ordenar os buracos por tamanho (prioriza o menor buraco)
    buracos.sort(key=lambda x: x['tamanho'])
    
    faltantes_finais = []
    
    # 3. Lógica de seleção dos DOIS números
    
    if buracos:
        
        # A. Seleciona o primeiro número (o menor do menor buraco)
        primeiro_buraco = buracos[0]['faltantes']
        if primeiro_buraco:
            faltantes_finais.append(primeiro_buraco[0])
        
        # B. Seleciona o segundo número
        if len(faltantes_finais) < 2:
            
            # Opção 1: Pega o último do menor buraco (se ele tiver pelo menos 2 faltantes)
            if len(primeiro_buraco) > 1:
                faltantes_finais.append(primeiro_buraco[-1])
            
            # Opção 2: Pega o primeiro do SEGUNDO menor buraco (se houver)
            elif len(buracos) > 1:
                segundo_buraco = buracos[1]['faltantes']
                if segundo_buraco:
                    faltantes_finais.append(segundo_buraco[0])

    # 4. Ajuste final para garantir EXATAMENTE 2 (em casos extremos, ou se as regras acima falharem)
    
    # Remove duplicatas e garante a ordem
    faltantes_finais = sorted(list(set(faltantes_finais)))
    
    # Preenche o segundo lugar com o menor dígito faltante global, se ainda estiver vazio.
    if len(faltantes_finais) < 2:
        for i in range(10):
            if i not in digitos_presentes and i not in faltantes_finais:
                faltantes_finais.append(i)
                if len(faltantes_finais) == 2:
                    break

    # Garante que temos no máximo 2
    faltantes_finais = faltantes_finais[:2]
    
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
    """Calcula os alertas brutos (APENAS VELA) e os consolida (minutos próximos) ANTES de retornar."""
    
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
    
    # Extração de dígitos
    digitos_vela_str = ''.join(c for c in vela_str if c.isdigit())
    digitos_vela = [int(d) for d in digitos_vela_str]
    digitos_horario_str = ''.join(c for c in horario_str if c.isdigit())
    digitos_horario = [int(d) for d in digitos_horario_str]
    
    if not digitos_vela or not digitos_horario:
        return None, None, None, None
    
    # Cálculo de faltantes usando a lógica corrigida
    faltantes_V, soma_VT = calcular_faltantes_seletivos(digitos_vela)
    faltantes_H, soma_HT = calcular_faltantes_seletivos(digitos_horario) # Mantido para fins de estrutura, mas não usado
    
    r_bruto = (ultimos_dois_rodada * 0.6) + vela_inteira + minuto_original
    r_formatado = formatar_resultado_r(r_bruto)
    
    horarios_brutos_list = []
    
    def adicionar_horario(soma: int, origem_completa: str):
        novo_horario_dt = horario_base_dt + timedelta(minutes=soma)
        
        if origem_completa.startswith('V x'):
            origem_simples = 'V'
        elif origem_completa.startswith('H x'):
            origem_simples = 'H' # Não deve ocorrer, mas mantemos a estrutura de checagem
        else:
            origem_simples = origem_completa.split(' ')[0] 
        
        horarios_brutos_list.append({
            'Timestamp_dt': novo_horario_dt, 
            'Origem_Bruta': origem_simples,
            'Rodada': str(rodada),
            'R': r_formatado,
        })
        
    # Geração de alertas baseados APENAS na VELA (V)
    for v in faltantes_V:
        adicionar_horario(v, f"V x 1 (+{v}m)")
        adicionar_horario(v * 10, f"V x 10 (+{v*10}m)")
        
    if soma_VT > 0:
        adicionar_horario(soma_VT, f"VT (Soma V +{soma_VT}m)")
        
    horarios_brutos_list.sort(key=lambda x: x['Timestamp_dt'])
    
    # Consolidação de Minutos Próximos
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

        horarios_consolidados.append({
            'Rodada': str(rodada),
            'Horário Focado': horario_final_dt.strftime("%H:%M:%S"),
            'Origem': ' / '.join(origens_consolidadas),
            'R': r_formatado,
            'Timestamp_dt': horario_final_dt 
        })
        
        i = j
    
    return pd.DataFrame(horarios_consolidados), faltantes_V, faltantes_H, r_formatado, horario_base_dt

# --- 2. GERENCIAMENTO DE ESTADO E CONSOLIDAÇÃO DE HISTÓRICO ---

if 'historico_alertas' not in st.session_state:
    st.session_state.historico_alertas = pd.DataFrame(columns=['Rodada', 'Horário Focado', 'Origem', 'R', 'Timestamp_dt'])

def consolidar_historico(novo_df, horario_base_dt):
    
    historico_atualizado = st.session_state.historico_alertas.copy()
    
    historico_atualizado = historico_atualizado[
        historico_atualizado['Timestamp_dt'] >= horario_base_dt
    ]

    historico_completo = pd.concat([historico_atualizado, novo_df], ignore_index=True)
    
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
            consolidado_dict[horario_focado]['Rodadas'].add(row['Rodada'])
            consolidado_dict[horario_focado]['Origens'].add(row['Origem'])

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
                
                novo_df_bruto, faltantes_V, faltantes_H, r_final, horario_base_dt = analisar_e_gerar_alertas(rodada, vela_input, horario_input)
                
                if novo_df_bruto is not None and not novo_df_bruto.empty:
                    
                    consolidar_historico(novo_df_bruto, horario_base_dt)
                    
                    st.success(f"Rodada {rodada} adicionada com sucesso. Faltantes Encontrados: {', '.join(map(str, faltantes_V))}. Histórico atualizado.")
                    
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(label=f"Resultado R da Rodada {rodada}", value=r_final)
                    with col2:
                        st.metric(label="Horário Base da Rodada", value=horario_input)
                    
                else:
                    st.error("Nenhum alerta gerado (somente V) ou erro na extração de dados. Verifique a Vela e o Horário.")
                    
        except ValueError:
            st.error("Erro de formato: A Rodada deve ser um número inteiro. Verifique todos os campos.")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado: {e}")

# --- 4. EXIBIÇÃO DO HISTÓRICO ATUALIZADO ---

st.markdown("---")
st.subheader("🔔 Histórico de Alertas Focados (Ativos)")

if not st.session_state.historico_alertas.empty:
    
    df_exibicao = st.session_state.historico_alertas.drop(columns=['Timestamp_dt', 'Rodada']) 
    
    st.dataframe(
        df_exibicao, 
        hide_index=True,
        column_order=['Horário Focado', 'R', 'Origem'] 
    )
    
else:
    st.info("Nenhuma rodada adicionada ou todos os alertas se passaram. Insira os dados para começar.")
    
if st.button("Limpar TODO o Histórico", help="Apaga todos os alertas ativos."):
    st.session_state.historico_alertas = pd.DataFrame(columns=['Rodada', 'Horário Focado', 'Origem', 'R', 'Timestamp_dt'])
    st.rerun()
