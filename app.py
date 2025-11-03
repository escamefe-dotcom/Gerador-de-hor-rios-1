import streamlit as st
from datetime import datetime, timedelta
from typing import List, Tuple
import pandas as pd

# --- FUNÇÕES DE ANÁLISE ---

def calcular_faltantes_seletivos(digitos_presentes: List[int]) -> Tuple[List[int], int]:
    """Identifica os números faltantes que completam uma sequência (máximo 3 faltantes)."""
    digitos_presentes = sorted(list(set(digitos_presentes)))
    todos_faltantes_seletivos = set()
    
    # Busca faltantes entre dígitos consecutivos (máximo 3 faltantes)
    for i in range(len(digitos_presentes) - 1):
        d1 = digitos_presentes[i]
        d2 = digitos_presentes[i+1]
        diferenca = d2 - d1
        
        if 2 <= diferenca <= 4:
            for d in range(d1 + 1, d2):
                todos_faltantes_seletivos.add(d)
    
    # Incluir faltantes que ligam ao 0 (se faltar 3 ou menos)
    if digitos_presentes and digitos_presentes[0] > 0 and digitos_presentes[0] <= 4:
        for d in range(1, digitos_presentes[0]):
            todos_faltantes_seletivos.add(d)

    # Incluir faltantes que ligam ao 9 (se faltar 3 ou menos)
    if digitos_presentes and digitos_presentes[-1] < 9 and (9 - digitos_presentes[-1]) <= 3:
        for d in range(digitos_presentes[-1] + 1, 10):
            todos_faltantes_seletivos.add(d)

    faltantes_finais = sorted(list(todos_faltantes_seletivos))
    soma_total = sum(faltantes_finais)

    return faltantes_finais, soma_total

def formatar_resultado_r(r_bruto: float) -> float:
    """Aplica a regra de formatação para o Resultado R."""
    if r_bruto <= 100:
        return r_bruto
    else:
        parte_inteira = int(r_bruto)
        soma_digitos = sum(int(d) for d in str(parte_inteira))
        parte_decimal = r_bruto - parte_inteira
        
        return round(soma_digitos + parte_decimal, 1)

def analisar_e_gerar_alertas(rodada, vela_str, horario_str):
    
    # --- 1. Extração de Componentes e Validação ---
    try:
        ultimos_dois_rodada = rodada % 100
        # Tenta extrair a parte inteira da vela. Ex: 23.89x -> 23
        parte_numerica = vela_str.replace('x', '')
        if '.' in parte_numerica:
            vela_inteira = int(float(parte_numerica))
        else:
            vela_inteira = int(parte_numerica)
            
        horario_base_dt = datetime.strptime(horario_str, "%H:%M:%S")
        minuto_original = horario_base_dt.minute
    except ValueError:
        return None, None, None, None
    
    digitos_vela_str = ''.join(c for c in vela_str if c.isdigit())
    digitos_vela = [int(d) for d in digitos_vela_str]
    
    digitos_horario_str = ''.join(c for c in horario_str if c.isdigit())
    digitos_horario = [int(d) for d in digitos_horario_str]
    
    # --- 2. Análise Seletiva de Faltantes ---
    
    faltantes_V, soma_VT = calcular_faltantes_seletivos(digitos_vela)
    faltantes_H, soma_HT = calcular_faltantes_seletivos(digitos_horario)
    
    # --- 3. Cálculo e Formatação do Resultado R ---
    
    r_bruto = (ultimos_dois_rodada * 0.6) + vela_inteira + minuto_original
    r_formatado = formatar_resultado_r(r_bruto)
    
    # --- 4. Geração de Horários Brutos ---
    
    horarios_brutos = []
    
    def adicionar_horario(soma: int, origem: str):
        novo_horario_dt = horario_base_dt + timedelta(minutes=soma)
        horarios_brutos.append({
            'horario': novo_horario_dt, 
            'origem': origem,
            'soma': soma
        })
        
    # a) Horários Individuais (x1 e x10)
    for v in faltantes_V:
        adicionar_horario(v, f"V x 1 (+{v}m)")
        adicionar_horario(v * 10, f"V x 10 (+{v*10}m)")
    for h in faltantes_H:
        adicionar_horario(h, f"H x 1 (+{h}m)")
        adicionar_horario(h * 10, f"H x 10 (+{h*10}m)")
        
    # b) Horários Totais (VT e HT)
    if soma_VT > 0:
        adicionar_horario(soma_VT, f"VT (Soma V +{soma_VT}m)")
    if soma_HT > 0:
        adicionar_horario(soma_HT, f"HT (Soma H +{soma_HT}m)")
        
    # c) Horário Médio Central (HM)
    if soma_VT > 0 or soma_HT > 0:
        soma_total_media = round((soma_VT + soma_HT) / 2)
        adicionar_horario(soma_total_media, f"HM (+{soma_total_media}m)")
        
    horarios_brutos.sort(key=lambda x: x['horario'])
    
    # --- 5. Consolidação de Horários Próximos ---
    
    horarios_consolidados = []
    i = 0
    while i < len(horarios_brutos):
        grupo = [horarios_brutos[i]]
        j = i + 1
        
        while j < len(horarios_brutos):
            diff = (horarios_brutos[j]['horario'] - horarios_brutos[j-1]['horario']).total_seconds()
            if diff <= 61: # Próximo minuto ou o mesmo
                grupo.append(horarios_brutos[j])
                j += 1
            else:
                break
        
        # Regra de Consolidação:
        if len(grupo) == 1:
            horario_final = grupo[0]['horario']
            origem_final = grupo[0]['origem']
        elif len(grupo) % 2 == 1:
            # Ímpar: pega o do meio
            meio_index = len(grupo) // 2
            horario_final = grupo[meio_index]['horario']
            origem_final = f"Consolidação de {len(grupo)} horários"
        else:
            # Par: pega o maior
            horario_final = grupo[-1]['horario']
            origem_final = f"Consolidação de {len(grupo)} horários"
        
        horarios_consolidados.append({
            'Horário Focado': horario_final.strftime("%H:%M:%S"),
            'Origem': origem_final,
            'R': r_formatado
        })
        
        i = j

    df = pd.DataFrame(horarios_consolidados)
    return df, faltantes_V, faltantes_H, r_formatado

# --- INTERFACE STREAMLIT ---

st.set_page_config(page_title="Ferramenta de Análise", layout="centered")
st.title("📊 Ferramenta de Análise de Padrões")
st.markdown("Insira os dados da rodada, vela e horário para gerar os horários focados e o Resultado R.")

# Caixas de entrada
rodada_input = st.text_input("1. Rodada (Apenas números, ex: 3267785)", key="rodada")
vela_input = st.text_input("2. Vela (Ex: 23.89x)", key="vela")
horario_input = st.text_input("3. Horário Base (Formato HH:MM:SS, ex: 11:53:13)", key="horario")

# Botão para iniciar a análise
if st.button("Analisar e Gerar Alertas"):
    
    if not rodada_input or not vela_input or not horario_input:
        st.error("Por favor, preencha todos os campos para iniciar a análise.")
    else:
        try:
            rodada = int(rodada_input)
            
            # Executa a lógica
            df_resultado, faltantes_V, faltantes_H, r_final = analisar_e_gerar_alertas(rodada, vela_input, horario_input)
            
            if df_resultado is not None:
                st.markdown("---")
                st.subheader("✅ Resultados da Análise")
                
                # Exibição dos faltantes e R
                st.markdown(f"**Faltantes Vela (V):** `{', '.join(map(str, faltantes_V))}` | **Faltantes Horário (H):** `{', '.join(map(str, faltantes_H))}`")
                st.markdown(f"**Resultado R:** **`{r_final}`**")
                
                # Exibição da Tabela
                st.markdown("---")
                st.subheader("🔔 Horários de Alerta Focados (Consolidados)")
                st.dataframe(df_resultado, hide_index=True)
                
            else:
                st.error("Ocorreu um erro ao processar os dados. Verifique o formato do Horário (HH:MM:SS) e os tipos de entrada.")
                
        except ValueError:
            st.error("Erro de formato: A Rodada deve ser um número inteiro. Verifique todos os campos.")
        except Exception as e:
            # Isso é útil para debugging no ambiente web
            st.error(f"Ocorreu um erro inesperado. {e}")
