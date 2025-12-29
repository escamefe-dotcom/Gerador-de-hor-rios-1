import streamlit as st
from datetime import datetime, timedelta
import re
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Analista VIP - Histórico", layout="wide")

st.title("⚡ Gerador de Sinais com Histórico")

# Inicializa o histórico na memória se ele ainda não existir
if 'historico' not in st.session_state:
    st.session_state.historico = []

# Área de entrada
entrada = st.text_area("Cole os dados da rodada (Vela e Horário):", height=100, placeholder="7.80x\n09:09:13")

if st.button("GERAR E SALVAR"):
    if entrada:
        try:
            # Extração de dados
            vela_f = float(re.search(r"(\d+[.,]\d+)", entrada).group(1).replace(',', '.'))
            hora_s = re.search(r"(\d{2}:\d{2}:\d{2})", entrada).group(1)
            h_orig = datetime.strptime(hora_s, "%H:%M:%S")
            
            res = []
            # Regras de soma
            if 1.01 <= vela_f <= 1.09: res.append(h_orig + timedelta(minutes=10))
            elif 4.00 <= vela_f <= 4.99: res.append(h_orig + timedelta(minutes=4))
            elif 5.00 <= vela_f <= 5.99:
                res.append(h_orig + timedelta(minutes=5))
                res.append(h_orig + timedelta(minutes=10))
            elif 7.00 <= vela_f <= 7.99: res.append(h_orig + timedelta(minutes=3))
            elif 12.00 <= vela_f <= 12.99: res.append(h_orig + timedelta(minutes=13))

            if res:
                horarios_formatados = ", ".join([r.strftime('%H:%M:%S') for r in res])
                
                # Adiciona ao histórico (memória da sessão)
                nova_entrada = {
                    "ID": len(st.session_state.historico) + 1,
                    "Vela Base": f"{vela_f}x",
                    "Horário Original": hora_s,
                    "Próximas Entradas": horarios_formatados,
                    "Data": datetime.now().strftime("%d/%m/%Y")
                }
                # Insere no início da lista para o mais recente aparecer no topo
                st.session_state.historico.insert(0, nova_entrada)
                
                st.success("Sinal gerado e adicionado à tabela!")
                
                # Exibe o sinal atual para cópia rápida
                msg_copia = f"✅ SINAL GERADO\n📊 Vela: {vela_f}x\n🕒 Hora: {hora_s}\n🚀 Entradas: {horarios_formatados}"
                st.code(msg_copia, language=None)
            else:
                st.warning("Vela sem regra cadastrada.")
        except Exception:
            st.error("Erro ao ler os dados. Certifique-se de colar a vela e o horário.")

# Exibição da Tabela
st.markdown("---")
st.subheader("📜 Histórico de Análises")

if st.session_state.historico:
    # Transforma a lista de memória em uma tabela visual (DataFrame)
    df = pd.DataFrame(st.session_state.historico)
    st.table(df) # Ou st.dataframe(df) para uma tabela interativa
    
    if st.button("Limpar Histórico"):
        st.session_state.historico = []
        st.rerun()
else:
    st.info("Nenhuma análise feita ainda.")
