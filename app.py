import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="Calculadora Pro")

st.title("📊 Gerador de Horários")

# Interface simplificada
valor_vela = st.number_input("Vela", min_value=0.0, format="%.2f")
hora_vela = st.text_input("Horário (HH:MM:SS)", value=datetime.now().strftime("%H:%M:%S"))

if st.button("Calcular"):
    try:
        h_orig = datetime.strptime(hora_vela, "%H:%M:%S")
        res = []
        
        # Suas Regras
        if 1.01 <= valor_vela <= 1.09: res.append(h_orig + timedelta(minutes=10))
        elif 4.00 <= valor_vela <= 4.99: res.append(h_orig + timedelta(minutes=4))
        elif 5.00 <= valor_vela <= 5.99:
            res.append(h_orig + timedelta(minutes=5))
            res.append(h_orig + timedelta(minutes=10))
        elif 7.00 <= valor_vela <= 7.99: res.append(h_orig + timedelta(minutes=3))
        elif 12.00 <= valor_vela <= 12.99: res.append(h_orig + timedelta(minutes=13))

        if res:
            for r in res:
                st.success(f"✅ Entrada: {r.strftime('%H:%M:%S')}")
        else:
            st.warning("Vela fora das regras.")
    except:
        st.error("Formato de hora inválido. Use HH:MM:SS")
