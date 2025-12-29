import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(page_title="Gerador Pro", page_icon="📲")

st.title("📲 Gerador de Sinal (Copiar/Colar)")

# Entradas
valor_vela = st.number_input("Valor da Vela", min_value=0.0, format="%.2f", step=0.01)
hora_vela = st.text_input("Horário da Vela (HH:MM:SS)", value=datetime.now().strftime("%H:%M:%S"))

if st.button("Gerar e Copiar"):
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
            st.subheader("📋 Clique no ícone à direita para copiar:")
            
            # Criando o texto formatado para copiar
            texto_copiar = f"✅ SINAL CONFIRMADO\n📊 Vela Base: {valor_vela}x\n🕒 Horário: {hora_vela}\n\n🚀 ENTRADAS PARA:\n"
            for r in res:
                texto_copiar += f"👉 {r.strftime('%H:%M:%S')}\n"
            
            texto_copiar += "\n⚠️ Gestão sempre!"

            # Mostra o texto em um bloco de código (que tem botão de copiar automático)
            st.code(texto_copiar, language=None)
            
            # Opcional: Mostra um balão de sucesso
            st.success("Sinal gerado com sucesso!")
        else:
            st.warning("Vela fora das regras de análise.")
    except Exception as e:
        st.error("Erro: Verifique se o horário está no formato 00:00:00")
