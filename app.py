import streamlit as st
from datetime import datetime, timedelta

# Configurações de estilo simples
st.set_page_config(page_title="Analisador de Velas", page_icon="📈")

st.title("📈 Calculadora de Próximos Horários")
st.markdown("Insira os dados da vela abaixo para calcular as entradas.")

# Função de cálculo baseada nas suas regras
def calcular_regras(vela, horario_str):
    try:
        formato = "%H:%M:%S"
        hora_orig = datetime.strptime(horario_str, formato)
        proximos = []

        # Regra 1: 1.01 até 1.09 -> +10 min
        if 1.01 <= vela <= 1.09:
            proximos.append(hora_orig + timedelta(minutes=10))

        # Regra 2: 4.00 até 4.99 -> +4 min
        elif 4.00 <= vela <= 4.99:
            proximos.append(hora_orig + timedelta(minutes=4))

        # Regra 3: 5.00 até 5.99 -> +5 min e +10 min
        elif 5.00 <= vela <= 5.99:
            proximos.append(hora_orig + timedelta(minutes=5))
            proximos.append(hora_orig + timedelta(minutes=10))

        # Regra 4: 7.00 até 7.99 -> +3 min
        elif 7.00 <= vela <= 7.99:
            proximos.append(hora_orig + timedelta(minutes=3))

        # Regra 5: 12.00 até 12.99 -> +13 min
        elif 12.00 <= vela <= 12.99:
            proximos.append(hora_orig + timedelta(minutes=13))

        return [h.strftime(formato) for h in proximos]
    except Exception:
        return None

# Interface de entrada
col1, col2 = st.columns(2)
with col1:
    vela_input = st.number_input("Valor da Vela:", min_value=0.0, step=0.01, format="%.2f")
with col2:
    hora_input = st.text_input("Horário (HH:MM:SS):", value=datetime.now().strftime("%H:%M:%S"))

if st.button("Gerar Análise"):
    if vela_input and hora_input:
        resultados = calcular_regras(vela_input, hora_input)
        
        if resultados:
            st.subheader("🚀 Próximos Horários Sugeridos:")
            for r in resultados:
                st.success(f"📌 Entrada confirmada para: **{r}**")
        else:
            st.info("Esta vela não se encaixa em nenhuma regra de soma.")
