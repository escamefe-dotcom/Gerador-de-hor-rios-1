import streamlit as st
from datetime import datetime, timedelta

# Configuração da página
st.set_page_config(page_title="Gerador de Horários", page_icon="📊")

st.title("📊 Analisador de Velas")

def calcular_proximos_horarios(multiplicador, horario_str):
    try:
        formato = "%H:%M:%S"
        # Garante que o horário esteja no formato correto
        horario_original = datetime.strptime(horario_str, formato)
        proximos = []

        # Regra 1: 1.01 até 1.09 -> +10 min
        if 1.01 <= multiplicador <= 1.09:
            proximos.append(horario_original + timedelta(minutes=10))

        # Regra 2: 4.00 até 4.99 -> +4 min
        elif 4.00 <= multiplicador <= 4.99:
            proximos.append(horario_original + timedelta(minutes=4))

        # Regra 3: 5.00 até 5.99 -> +5 min e +10 min
        elif 5.00 <= multiplicador <= 5.99:
            proximos.append(horario_original + timedelta(minutes=5))
            proximos.append(horario_original + timedelta(minutes=10))

        # Regra 4: 7.00 até 7.99 -> +3 min
        elif 7.00 <= multiplicador <= 7.99:
            proximos.append(horario_original + timedelta(minutes=3))

        # Regra 5: 12.00 até 12.99 -> +13 min
        elif 12.00 <= multiplicador <= 12.99:
            proximos.append(horario_original + timedelta(minutes=13))

        return [h.strftime(formato) for h in proximos]
    except Exception as e:
        return None

# Interface do Usuário
vela = st.number_input("Digite o valor da Vela (Ex: 7.80):", min_value=1.0, step=0.01, format="%.2f")
horario = st.text_input("Digite o Horário da Vela (HH:MM:SS):", value="09:09:13")

if st.button("Calcular Próximos Horários"):
    resultados = calcular_proximos_horarios(vela, horario)
    
    if resultados:
        st.success(f"✅ Vela detectada: {vela}x")
        for h in resultados:
            st.write(f"🚀 **Próxima entrada sugerida: {h}**")
    else:
        st.warning("⚠️ Esta vela não se encaixa em nenhuma das regras cadastradas.")
