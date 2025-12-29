import streamlit as st
from datetime import datetime, timedelta
import re

st.set_page_config(page_title="Gerador Instantâneo", page_icon="⚡")

st.title("⚡ Analisador "Colar e Gerar"")

# Campo de entrada única
entrada_bruta = st.text_area("Cole aqui os dados da rodada (Ex: 7.80x e o horário abaixo):", placeholder="7.80x\n09:09:13", height=100)

def extrair_e_calcular(texto):
    try:
        # Busca números decimais (vela) e o formato de hora HH:MM:SS
        vela_match = re.search(r"(\d+[.,]\d+)", texto)
        hora_match = re.search(r"(\d{2}:\d{2}:\d{2})", texto)
        
        if not vela_match or not hora_match:
            return None, "Não encontrei a vela ou o horário no texto."

        vela = float(vela_match.group(1).replace(',', '.'))
        hora_str = hora_match.group(1)
        h_orig = datetime.strptime(hora_str, "%H:%M:%S")
        
        res = []
        # Regras aplicadas
        if 1.01 <= vela <= 1.09: res.append(h_orig + timedelta(minutes=10))
        elif 4.00 <= vela <= 4.99: res.append(h_orig + timedelta(minutes=4))
        elif 5.00 <= vela <= 5.99:
            res.append(h_orig + timedelta(minutes=5))
            res.append(h_orig + timedelta(minutes=10))
        elif 7.00 <= vela <= 7.99: res.append(h_orig + timedelta(minutes=3))
        elif 12.00 <= vela <= 12.99: res.append(h_orig + timedelta(minutes=13))

        if not res:
            return None, f"Vela {vela}x não tem regra cadastrada."

        # Monta o texto para cópia
        texto_saida = f"✅ SINAL GERADO\n📊 Vela Base: {vela}x\n🕒 Horário: {hora_str}\n\n🚀 ENTRADAS:\n"
        for r in res:
            texto_saida += f"👉 {r.strftime('%H:%M:%S')}\n"
        
        return texto_saida, None
    except Exception as e:
        return None, "Erro ao processar os dados."

if st.button("Analisar Agora"):
    if entrada_bruta:
        resultado, erro = extrair_e_calcular(entrada_bruta)
        if erro:
            st.error(erro)
        else:
            st.subheader("📋 Resultado pronto para copiar:")
            st.code(resultado, language=None)
            st.success("Cálculo concluído!")
    else:
        st.warning("Cole os dados primeiro!")
