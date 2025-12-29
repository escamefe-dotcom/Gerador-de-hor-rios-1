import streamlit as st
from datetime import datetime, timedelta
import re

st.set_page_config(page_title="Analista VIP", page_icon="⚡")

st.title("⚡ Analisador Instantâneo")
st.markdown("Cole os dados da rodada abaixo (Vela e Horário juntos).")

# Campo para colar tudo de uma vez
entrada = st.text_area("Cole aqui:", placeholder="Exemplo:\n7.80x\n09:09:13", height=150)

def processar_dados(texto):
    try:
        # Encontra o número da vela (ex: 7.80 ou 7,80)
        vela_busca = re.search(r"(\d+[.,]\d+)", texto)
        # Encontra o horário (formato 00:00:00)
        hora_busca = re.search(r"(\d{2}:\d{2}:\d{2})", texto)

        if not vela_busca or not hora_busca:
            return None

        vela = float(vela_busca.group(1).replace(',', '.'))
        hora_str = hora_busca.group(1)
        h_orig = datetime.strptime(hora_str, "%H:%M:%S")
        
        proximos = []
        # Aplicando suas regras exatas
        if 1.01 <= vela <= 1.09:
            proximos.append(h_orig + timedelta(minutes=10))
        elif 4.00 <= vela <= 4.99:
            proximos.append(h_orig + timedelta(minutes=4))
        elif 5.00 <= vela <= 5.99:
            proximos.append(h_orig + timedelta(minutes=5))
            proximos.append(h_orig + timedelta(minutes=10))
        elif 7.00 <= vela <= 7.99:
            proximos.append(h_orig + timedelta(minutes=3))
        elif 12.00 <= vela <= 12.99:
            proximos.append(h_orig + timedelta(minutes=13))

        if not proximos:
            return f"Vela {vela}x não possui regra cadastrada."

        # Formatação para copiar e colar
        msg = f"✅ **SINAL GERADO**\n\n📊 Vela Base: {vela}x\n🕒 Horário: {hora_str}\n\n🚀 **ENTRADAS:**\n"
        for p in proximos:
            msg += f"👉 {p.strftime('%H:%M:%S')}\n"
        
        return msg
    except:
        return "Erro ao processar. Verifique se os dados estão corretos."

if st.button("GERAR ANÁLISE"):
    if entrada:
        resultado = processar_dados(entrada)
        if "SINAL GERADO" in str(resultado):
            st.markdown("---")
            st.subheader("📋 Resultado (Clique no ícone para copiar):")
            st.code(resultado, language=None)
        else:
            st.warning(resultado)
    else:
        st.info("Aguardando dados...")
