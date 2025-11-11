import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

# Define a chave de estado de sessão para o histórico
if 'historico' not in st.session_state:
    st.session_state.historico = []

def calcular_sistema_personalizado(vela_base_str: str, horario_base_str: str, rodada_base_int: int, vela_calculo_float: float, horario_calculo_str: str) -> tuple[str, float]:
    """
    Função principal que aplica a lógica de cálculo personalizada.
    """
    FORMATO_HORARIO = "%H:%M:%S"
    
    # --- 1° Passo: Soma dos dígitos da Vela Base ---
    try:
        parte_decimal = vela_base_str.split('.')[-1].replace('x', '')
        if len(parte_decimal) < 2:
             st.error("ERRO (Vela Base): Deve ter pelo menos dois dígitos decimais após o ponto.")
             return None, None
             
        digito1 = int(parte_decimal[0])
        digito2 = int(parte_decimal[1])
        soma_minutos = digito1 + digito2
    except (IndexError, ValueError):
        st.error("ERRO (Vela Base): Formato incorreto. Use o formato 'X.XXx' (ex: '1.03x').")
        return None, None

    # --- 2° Passo: Somar o resultado ao Horário Base ---
    try:
        horario_base = datetime.strptime(horario_base_str, FORMATO_HORARIO)
        novo_horario_dt = horario_base + timedelta(minutes=soma_minutos)
        novo_horario_str = novo_horario_dt.strftime(FORMATO_HORARIO)
    except ValueError:
        st.error("ERRO (Horário Base): Formato incorreto. Use 'HH:MM:SS' (ex: '20:49:55').")
        return None, None

    # --- 3° Passo: Aplicar a Fórmula ---
    
    dois_ultimos_rodada = rodada_base_int % 100

    try:
        minuto_vela_calculo = datetime.strptime(horario_calculo_str, FORMATO_HORARIO).minute
    except ValueError:
        st.error("ERRO (Horário da Vela de Cálculo): Formato incorreto. Use 'HH:MM:SS'.")
        return None, None
    
    # Fórmula: 0,6 * (2 Últimos Dígitos da Rodada) + Vela para Cálculo + Minuto da Vela de Cálculo
    resultado_formula = 0.6 * dois_ultimos_rodada + vela_calculo_float + minuto_vela_calculo

    return novo_horario_str, resultado_formula

# =========================================================================
# INTERFACE STREAMLIT
# =========================================================================

st.set_page_config(page_title="Calculadora Personalizada", layout="centered")
st.title("🧮 Calculadora de Sistema Personalizado")

st.markdown("---")

# Instruções de Colagem
st.subheader("Entrada Rápida de Dados")
st.warning("🚨 **IMPORTANTE:** Cole os 5 valores **EXATAMENTE NESTA ORDEM**, um em cada linha:")
st.code("""1. Vela Base (ex: 1.03x)
2. Horário Base (ex: 20:49:55)
3. Rodada Base (ex: 3294634)
4. Vela para Cálculo (ex: 16.64x ou 16.64)
5. Horário da Vela p/ Cálculo (ex: 20:49:09)""")

# Campo de entrada de texto de múltiplas linhas
default_values = "1.03x\n20:49:55\n3294634\n16.64\n20:49:09"

dados_colados = st.text_area(
    "Cole os 5 valores abaixo (Um por Linha)",
    value=default_values,
    height=150,
    key="dados_input"
)

# Botão de Cálculo
submitted = st.button("Calcular e Salvar Resultado")

# Área de Processamento e Resultados
if submitted:
    
    # 1. Processar a entrada
    linhas = [linha.strip() for linha in dados_colados.split('\n') if linha.strip()]
    
    if len(linhas) != 5:
        st.error(f"Erro: Você deve colar **5 linhas de dados**. Foram detectadas {len(linhas)}.")
    else:
        try:
            VelaBase = linhas[0]
            HorarioBase = linhas[1]
            RodadaBase = int(linhas[2])
            VelaCalculo = float(linhas[3].replace('x', ''))
            HorarioCalculo = linhas[4]

            # 2. Chama a função de cálculo
            novo_horario, resultado_formula = calcular_sistema_personalizado(
                vela_base_str=VelaBase,
                horario_base_str=HorarioBase,
                rodada_base_int=RodadaBase,
                vela_calculo_float=VelaCalculo,
                horario_calculo_str=HorarioCalculo
            )
            
            # 3. Salva e exibe o resultado
            if novo_horario and resultado_formula is not None:
                
                # Cria o registro a ser salvo
                novo_registro = {
                    "Horário Final": novo_horario,
                    "Resultado Fórmula": f"{resultado_formula:.2f}",
                    "Vela Base": VelaBase,
                    "Rodada Base": RodadaBase,
                    "Horário Input": HorarioBase,
                }
                
                # Adiciona ao histórico (st.session_state)
                st.session_state.historico.append(novo_registro)
                
                st.success(f"Cálculo Salvo! Resultado: {novo_horario} / {resultado_formula:.2f}")

        except ValueError as e:
            st.error(f"Erro ao converter os dados. Verifique se os números e horários estão no formato correto. Detalhe: {e}")

# --- SEÇÃO DO HISTÓRICO ---
st.markdown("---")
st.subheader("📋 Histórico de Resultados")

if st.session_state.historico:
    
    # Converte o histórico em um DataFrame
    df_historico = pd.DataFrame(st.session_state.historico)
    
    # Ordena o DataFrame pelo 'Horário Final' em ordem crescente
    df_historico_ordenado = df_historico.sort_values(by="Horário Final", ascending=True)
    
    # Exibe a tabela
    st.dataframe(df_historico_ordenado, use_container_width=True, hide_index=True)
    
    # Botão para limpar o histórico
    if st.button("Limpar Histórico"):
        st.session_state.historico = []
        st.experimental_rerun() # Reinicia a aplicação para atualizar a tabela
        
else:
    st.info("O histórico está vazio. Calcule o primeiro resultado para começar a registrar.")
