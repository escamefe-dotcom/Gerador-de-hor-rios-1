import streamlit as st
from datetime import datetime, timedelta

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
    
    # 3a: Obter os 2 últimos dígitos da Rodada Base
    dois_ultimos_rodada = rodada_base_int % 100

    # 3b: Obter o minuto da Vela de Cálculo
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

st.markdown("""
Insira os cinco valores para realizar o cálculo, seguindo a sua lógica:
$$0,6 \\times (\\text{2 Últimos da Rodada}) + (\\text{Vela Cálculo}) + (\\text{Minuto Vela Cálculo})$$
""")

# Área de Entrada de Dados
with st.form("calculo_form"):
    st.subheader("Entrada de Dados")
    
    col1, col2 = st.columns(2)
    
    # Coluna 1: Dados em String/Horário
    with col1:
        vela_base = st.text_input("1. Vela Base (X.XXx)", value="1.03x")
        horario_base = st.text_input("2. Horário Base (HH:MM:SS)", value="20:49:55")
        horario_calculo = st.text_input("5. Horário da Vela p/ Cálculo (HH:MM:SS)", value="20:49:09")

    # Coluna 2: Dados Numéricos
    with col2:
        # Use um campo de texto e tente converter para inteiro
        rodada_base_str = st.text_input("3. Rodada Base (Número Inteiro)", value="3294634")
        try:
            rodada_base = int(rodada_base_str)
        except ValueError:
            rodada_base = 0 # Valor padrão para evitar erro antes da submissão
            
        # Use um campo de texto e tente converter para float
        vela_calculo_str = st.text_input("4. Vela p/ Cálculo (Número Decimal)", value="16.64")
        try:
            vela_calculo = float(vela_calculo_str)
        except ValueError:
            vela_calculo = 0.0 # Valor padrão

    # Botão de submissão do formulário
    submitted = st.form_submit_button("Calcular Resultados")

# Área de Resultados
if submitted:
    st.divider()
    st.subheader("Resultados")
    
    # Chama a função de cálculo
    novo_horario, resultado_formula = calcular_sistema_personalizado(
        vela_base_str=vela_base,
        horario_base_str=horario_base,
        rodada_base_int=rodada_base,
        vela_calculo_float=vela_calculo,
        horario_calculo_str=horario_calculo
    )
    
    # Exibe os resultados se não houver erro
    if novo_horario and resultado_formula is not None:
        st.success(f"**Cálculo Realizado com Sucesso!**")
        
        st.info(f"**Passo 1 & 2 (Horário):** {horario_base} + {int(vela_base.split('.')[-1].replace('x', '')[0]) + int(vela_base.split('.')[-1].replace('x', '')[1])} minutos = **{novo_horario}**")
        st.info(f"**Passo 3 (Fórmula):** O resultado final é **{resultado_formula:.2f}**")
        
        st.markdown(f"### Resultado Final: `{novo_horario} / {resultado_formula:.2f}`")

