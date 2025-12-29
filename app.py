import streamlit as st
from datetime import datetime, timedelta
import re
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Gerador VIP", layout="wide")

st.title("⚡ Analisador de Sinais (Ordenado)")

# Inicializa o histórico na memória
if 'historico' not in st.session_state:
    st.session_state.historico = []

# Área de entrada
entrada = st.text_area("Cole os dados aqui:", height=100, placeholder="Exemplo:\n7.80x\n09:09:13")

if st.button("GERAR E SALVAR"):
    if entrada:
        try:
            # Extração de dados via Regex
            vela_match = re.search(r"(\d+[.,]\d+)", entrada)
            hora_match = re.search(r"(\d{2}:\d{2}:\d{2})", entrada)
            
            if vela_match and hora_match:
                vela_f = float(vela_match.group(1).replace(',', '.'))
                hora_s = hora_match.group(1)
                h_orig = datetime.strptime(hora_s, "%H:%M:%S")
                
                res = []
                # Suas Regras
                if 1.01 <= vela_f <= 1.09: res.append(h_orig + timedelta(minutes=10))
                elif 4.00 <= vela_f <= 4.99: res.append(h_orig + timedelta(minutes=4))
                elif 5.00 <= vela_f <= 5.99:
                    res.append(h_orig + timedelta(minutes=5))
                    res.append(h_orig + timedelta(minutes=10))
                elif 7.00 <= vela_f <= 7.99: res.append(h_orig + timedelta(minutes=3))
                elif 12.00 <= vela_f <= 12.99: res.append(h_orig + timedelta(minutes=13))

                if res:
                    # Formata os horários para exibição
                    horarios_formatados = " | ".join([r.strftime('%H:%M:%S') for r in res])
                    
                    # Salva no histórico incluindo o objeto datetime para ordenação correta
                    nova_entrada = {
                        "Vela": f"{vela_f}x",
                        "Próximas Entradas": horarios_formatados,
                        "Hora_Ref": res[0], # Usado para ordenar
                        "Gerado em": datetime.now().strftime("%H:%M:%S")
                    }
                    st.session_state.historico.append(nova_entrada)
                    
                    # ORDENAÇÃO: Organiza do horário mais cedo para o mais tarde
                    st.session_state.historico.sort(key=lambda x: x['Hora_Ref'])
                    
                    # Exibe para cópia
                    msg_copia = f"✅ SINAL GERADO\n📊 Vela: {vela_f}x\n🚀 Entradas: {horarios_formatados}"
                    st.code(msg_copia, language=None)
                else:
                    st.warning("Vela sem regra cadastrada.")
            else:
                st.error("Não encontrei vela ou horário no texto colado.")
        except Exception as e:
            st.error("Erro no processamento.")

# Exibição da Tabela
st.markdown("---")
st.subheader("📜 Histórico de Sinais (Cronológico)")

if st.session_state.historico:
    # Cria o DataFrame e remove a coluna de referência técnica antes de mostrar
    df = pd.DataFrame(st.session_state.historico)
    df_visual = df.drop(columns=['Hora_Ref']) 
    
    st.table(df_visual)
    
    if st.button("Limpar Histórico"):
        st.session_state.historico = []
        st.rerun()
else:
    st.info("Nenhuma análise no histórico.")
