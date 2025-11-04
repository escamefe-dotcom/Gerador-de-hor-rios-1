# CÓDIGO COM A NOVA LÓGICA REFORÇADA PARA DOIS FALTANTES

import streamlit as st
# ... (restante dos imports) ...
from typing import List, Tuple
import pandas as pd
import re
from datetime import datetime, timedelta
# ... (restante do setup) ...

# ... (restante do código até o bloco de faltantes) ...

@st.cache_data(show_spinner=False)
def calcular_faltantes_seletivos(digitos_presentes: List[int]) -> Tuple[List[int], int]:
    """
    Identifica EXATAMENTE dois números faltantes, priorizando:
    1. O preenchimento de buracos menores.
    2. O primeiro número do menor buraco e o último do buraco seguinte.
    """
    digitos_presentes = sorted(list(set(digitos_presentes)))
    
    # Se houver 0 ou 1 dígito, não há sequência para analisar, retorna vazio.
    if len(digitos_presentes) <= 1:
        return [], 0
    
    # 1. Identificar todos os buracos (sequências faltantes)
    buracos = []
    
    # Adicionar 0 no final se 9 estiver presente para fechar o ciclo (9 -> 0)
    # Mas para o cálculo de buracos sequenciais, usamos 10 no lugar de 0.
    digitos_extendidos = digitos_presentes + [digitos_presentes[0] + 10]
    
    # Mapear os buracos sequenciais
    for i in range(len(digitos_presentes)):
        d1 = digitos_presentes[i]
        d2 = digitos_extendidos[i+1] % 10 # Se d2 for 10 ou mais, volta para 0..9

        # O d2 real (que encerra o buraco)
        d2_real = digitos_extendidos[i+1] 
        
        diferenca = d2_real - d1
        
        if diferenca > 1:
            # Lista de números que faltam no buraco
            faltantes = [(d1 + j) % 10 for j in range(1, diferenca)]
            buracos.append({
                'tamanho': diferenca - 1,
                'faltantes': faltantes,
                'd1': d1,
                'd2': d2,
                'tipo': 'circular' if d2_real >= 10 else 'sequencial'
            })

    # 2. Ordenar os buracos por tamanho (prioriza o menor buraco)
    buracos.sort(key=lambda x: x['tamanho'])
    
    faltantes_finais = []
    
    if buracos:
        # Pega o primeiro faltante (o menor do menor buraco)
        primeiro_buraco = buracos[0]['faltantes']
        if primeiro_buraco:
            faltantes_finais.append(primeiro_buraco[0])
            
        # Pega o segundo faltante
        if len(faltantes_finais) < 2:
            # Se o primeiro buraco for maior que 1, pega o último dele
            if len(primeiro_buraco) > 1:
                faltantes_finais.append(primeiro_buraco[-1])
            elif len(buracos) > 1:
                # Se não, pega o primeiro do segundo menor buraco
                segundo_buraco = buracos[1]['faltantes']
                if segundo_buraco:
                    faltantes_finais.append(segundo_buraco[0])

        # Se ainda faltar, e houver um terceiro buraco, pega o último elemento do maior buraco encontrado
        if len(faltantes_finais) < 2:
            buracos.sort(key=lambda x: x['tamanho'], reverse=True) # Busca o maior
            if buracos and buracos[0]['faltantes']:
                 # Garante que não repete o primeiro selecionado
                 if buracos[0]['faltantes'][-1] != faltantes_finais[0]:
                    faltantes_finais.append(buracos[0]['faltantes'][-1])

    # Se ainda faltarem números para completar 2, preenche com o menor número que não está na lista.
    if len(faltantes_finais) < 2:
        for i in range(10):
            if i not in digitos_presentes and i not in faltantes_finais:
                faltantes_finais.append(i)
                if len(faltantes_finais) == 2:
                    break


    # Garante que temos exatamente 2, elimina duplicatas e ordena
    faltantes_finais = sorted(list(set(faltantes_finais)))
    faltantes_finais = faltantes_finais[:2]

    soma_total = sum(faltantes_finais)

    return faltantes_finais, soma_total


# ... (restante do código) ...
