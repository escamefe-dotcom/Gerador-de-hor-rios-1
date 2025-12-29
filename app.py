import streamlit as st
from datetime import datetime, timedelta
import re

# Configuração essencial
st.set_page_config(page_title="Gerador de Sinais")

st.title("⚡ Analisador de Rodadas")

# Campo único para colar (Ex: 7.80x e 09:09:13)
entrada = st.text_area("Cole os dados aqui:", height=100)

def calcular():
    try:
        # Extrai o número (vela) e o horário do texto colado
        vela_f = float(re.search(r"(\d+[.,]\d+)", entrada).group(1).replace(',', '.'))
        hora_s = re.search(r"(\d{2}:\d{2}:\d{2})", entrada).group(1)
        h_orig = datetime.strptime(hora_s, "%H:%M:%S")
        
        res = []
        # Suas regras de soma
        if 1.01 <= vela_f <= 1.09: res.append(h_orig + timedelta(minutes=10))
        elif 4.00 <= vela_f <= 4.99: res.append(h_orig + timedelta(minutes=4))
        elif 5.00 <= vela_f <= 5.99:
            res.append(h_orig + timedelta(minutes=5))
            res.append(h_orig + timedelta(minutes=10))
        elif 7.00 <= vela_f <= 7.99: res.append(h_orig + timedelta(minutes=3))
        elif 12.00 <= vela_f <= 12.99: res.append(h_orig + timedelta(minutes=13))

        if res:
            st.subheader("📋 Copie o Sinal:")
            msg = f"✅ SINAL GERADO\n📊 Vela: {vela_f}x\n🕒 Hora: {hora_s}\n\n🚀 ENTRADAS:\n"
            for r in res:
                msg += f"👉 {r.strftime('%H:%M:%S')}\n"
            st.code(msg, language=None)
        else:
            st.warning("Vela sem regra cadastrada.")
    except:
        st.error("Cole os dados no formato correto (Vela e Horário).")

if st.button("GERAR"):
    if entrada:
        calcular()
