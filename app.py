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

# --- FUNÇÃO NOVA: CALCULAR COTAÇÃO ---

def calcular_cotacao(faltantes: List[int]) -> str:
    """
    Calcula a Cotação (C) com base nos dois faltantes, aplicando um desconto de 20%.
    Ex: [4, 5] -> 45 -> 45 * 0.80 = 36. Resultado: '36 a 45x'
    """
    if len(faltantes) != 2:
        return "-"
    
    # 1. Forma o número de dois dígitos
    # Ex: [4, 5] se torna 45. O número deve ser formado pelos dígitos em ordem crescente.
    str_faltantes = "".join(map(str, faltantes))
    valor_original = int(str_faltantes)
    
    # 2. Calcula o valor com 20% de desconto (0.80 do valor original)
    valor_minimo_bruto = valor_original * 0.80
    
    # Arredonda para o inteiro mais próximo, conforme o padrão de resultados
    valor_minimo = round(valor_minimo_bruto)
    
    # 3. Formata a string de Cotação
    return f"{valor_minimo} a {valor_original}x"


# --- 1. FUNÇÕES DE CÁLCULO (CACHED) ---

@st.cache_data(show_spinner=False)
def calcular_faltantes_seletivos(digitos_presentes: List[int]) -> Tuple[List[int], int]:
    """
    Identifica EXATAMENTE dois números faltantes.
    A regra é: encontrar a sequência contígua de 4 dígitos (d, d+1, d+2, d+3) 
    que exige EXATAMENTE 2 faltantes, que começa com o MENOR dígito possível (d), 
    e onde NENHUM dos faltantes é o dígito 0.
    """
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
        
        # Condição principal: deve ter EXATAMENTE 2 presentes e 2 faltantes.
        if len(digitos_presentes_na_seq) == 2 and len(digitos_faltantes_na_seq) == 2:
            
            # NOVA RESTRIÇÃO: O dígito 0 não pode ser um dos faltantes escolhidos.
            if 0 not in digitos_faltantes_na_seq:
                
                # Prioriza a sequência que começa com o MENOR dígito (d)
                if inicio_seq < melhor_inicio:
                    melhor_inicio = inicio_seq
                    melhor_sequencia_faltantes = sorted(digitos_faltantes_na_seq)
            
    
    # Retorno Final
    if melhor_sequencia_faltantes:
        faltantes_finais = melhor_sequencia_faltantes
    else:
        # Fallback: Se nenhuma sequência válida (sem 0 no resultado) foi encontrada, 
        # pega os 2 menores faltantes globais que NÃO SÃO 0.
        faltantes_finais = sorted([f for f in faltantes_globais if f != 0])[:2] 
        
    
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
        return None, None, None, None, None
    
    # Extração de dígitos
    digitos_vela_str = ''.join(c for c in vela_str if c.isdigit())
    digitos_vela = [int(d) for d in digitos_vela_str]
    digitos_horario_str = ''.join(c for c in horario_str if c.isdigit())
    digitos_horario = [int(d) for d in digitos_horario_str]
    
    if not digitos_vela or not digitos_horario:
        return None, None, None, None, None
    
    # Cálculo de faltantes
    faltantes_V, soma_VT = calcular_faltantes_seletivos(digitos_vela)
    faltantes_H, soma_HT = calcular_faltantes_seletivos(digitos_horario)
    
    # CÁLCULO DA COTAÇÃO (C)
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
            'C': cotacao_C # Adiciona a Cotação (C) aqui
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
        # Pega o R e C do primeiro item do grupo (todos são iguais para a mesma rodada)
        r_consolidado = grupo[0]['R']
        c_consolidado = grupo[0]['C']

        horarios_consolidados.append({
            'Rodada': str(rodada),
            'Horário Focado': horario_final_dt.strftime("%H:%M:%S"),
            'Origem': ' / '.join(origens_consolidadas),
            'R': r_consolidado,
            'C': c_consolidado, # Adiciona C aqui também
            'Timestamp_dt': horario_final_dt 
        })
        
        i = j
    
    # Retorno deve incluir Cotação (C)
    return pd.DataFrame(horarios_consolidados), faltantes_V, faltantes_H, r_formatado, cotacao_C, horario_base_dt

# --- 2. GERENCIAMENTO DE ESTADO E CONSOLIDAÇÃO DE HISTÓRICO ---

# Atualiza a coluna C no DataFrame de estado
if 'historico_alertas' not in st.session_state:
    st.session_state.historico_alertas = pd.DataFrame(columns=['Rodada', 'Horário Focado', 'Origem', 'R', 'C', 'Timestamp_dt'])

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
                'C': row['C'], # Mantém Cotação
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
            'C': data['C'], # Inclui Cotação na saída final
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
                
                # Atualiza o unpack dos retornos
                novo_df_bruto, faltantes_V, faltantes_H, r_final, cotacao_final, horario_base_dt = analisar_e_gerar_alertas(rodada, vela_input, horario_input)
                
                if novo_df_bruto is not None and not novo_df_bruto.empty:
                    
                    consolidar_historico(novo_df_bruto, horario_base_dt)
                    
                    st.success(f"Rodada {rodada} adicionada com sucesso. Faltantes (V): {', '.join(map(str, faltantes_V))}. Histórico atualizado.")
                    
                    st.markdown("---")
                    col1, col2, col3 = st.columns(3) # Coluna extra para a Cotação
                    with col1:
                        st.metric(label=f"Resultado R", value=r_final)
                    with col2:
                        st.metric(label="Cotação (C)", value=cotacao_final)
                    with col3:
                        st.metric(label="Horário Base", value=horario_input)
                    
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
    
    # Inclui a coluna 'C' na exibição
    df_exibicao = st.session_state.historico_alertas.drop(columns=['Timestamp_dt', 'Rodada']) 
    
    st.dataframe(
        df_exibicao, 
        hide_index=True,
        column_order=['Horário Focado', 'R', 'C', 'Origem'] # Nova ordem
    )
    
else:
    st.info("Nenhuma rodada adicionada ou todos os alertas se passaram. Insira os dados para começar.")
    
if st.button("Limpar TODO o Histórico", help="Apaga todos os alertas ativos."):
    # Atualiza a coluna C no DataFrame de estado
    st.session_state.historico_alertas = pd.DataFrame(columns=['Rodada', 'Horário Focado', 'Origem', 'R', 'C', 'Timestamp_dt'])
    st.rerun()
