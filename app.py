import streamlit as st
from datetime import datetime, timedelta

def calcular_sistema_personalizado(vela_base_str: str, horario_base_str: str, rodada_base_int: int, vela_calculo_float: float, horario_calculo_str: str) -> tuple[str, float]:
    """
    Função principal que aplica a lógica de cálculo personalizada.
    (O corpo da função é o mesmo, mas agora com st.error para reportar erros)
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
# INTERFACE STREAMLIT COM TEXT_AREA
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
submitted = st.button("Calcular Resultados")

# Área de Processamento e Resultados
if submitted:
    
    # 1. Processar a entrada: Separar as linhas e remover espaços em branco
    linhas = [linha.strip() for linha in dados_colados.split('\n') if linha.strip()]
    
    if len(linhas) != 5:
        st.error(f"Erro: Você deve colar **5 linhas de dados**. Foram detectadas {len(linhas)}.")
    else:
        try:
            # 2. Atribuir os valores (conversão de tipos)
            VelaBase = linhas[0]  # 1.03x
            HorarioBase = linhas[1] # 20:49:55
            # Rodada Base deve ser Int
            RodadaBase = int(linhas[2]) # 3294634
            # Vela de Cálculo deve ser Float (remove 'x' se existir)
            VelaCalculo = float(linhas[3].replace('x', '')) # 16.64
            HorarioCalculo = linhas[4] # 20:49:09

            st.divider()
            st.subheader("Resultados")

            # 3. Chama a função de cálculo
            novo_horario, resultado_formula = calcular_sistema_personalizado(
                vela_base_str=VelaBase,
                horario_base_str=HorarioBase,
                rodada_base_int=RodadaBase,
                vela_calculo_float=VelaCalculo,
                horario_calculo_str=HorarioCalculo
            )
            
            # 4. Exibe os resultados
            if novo_horario and resultado_formula is not None:
                st.success("Cálculo Realizado com Sucesso!")
                
                # Exibe a lógica aplicada
                min_adicionados = int(VelaBase.split('.')[-1].replace('x', '')[0]) + int(VelaBase.split('.')[-1].replace('x', '')[1])
                st.info(f"**Passo 1 & 2 (Horário):** {HorarioBase} + {min_adicionados} minutos = **{novo_horario}**")
                
                dois_ultimos_rodada = RodadaBase % 100
                minuto_calculo = datetime.strptime(HorarioCalculo, "%H:%M:%S").minute
                st.info(f"**Passo 3 (Fórmula):** 0.6 * {dois_ultimos_rodada} + {VelaCalculo} + {minuto_calculo} = **{resultado_formula:.2f}**")
                
                st.markdown(f"### Resultado Final: `{novo_horario} / {resultado_formula:.2f}`")

        except ValueError as e:
            st.error(f"Erro ao converter os dados. Verifique se os números e horários estão no formato correto. Detalhe: {e}")
