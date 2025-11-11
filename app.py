from datetime import datetime, timedelta

def calcular_sistema_personalizado(vela_base_str, horario_base_str, rodada_base_int, vela_calculo_float, horario_calculo_str):
    """
    Aplica a lógica de cálculo personalizada.

    Args:
        vela_base_str (str): O valor da vela base (ex: "1.03x").
        horario_base_str (str): Horário de partida (ex: "20:49:55").
        rodada_base_int (int): Número da rodada base (ex: 3294634).
        vela_calculo_float (float): O valor da vela para o cálculo (ex: 16.64).
        horario_calculo_str (str): Horário da vela para o cálculo (ex: "20:49:09").

    Returns:
        tuple: (Novo horário formatado (str), Resultado da fórmula (float))
    """

    # --- 1° Passo: Soma dos dígitos da Vela Base ---
    # Extrai a parte decimal e soma os dois últimos dígitos
    try:
        # Pega a parte após o ponto decimal e garante que tem pelo menos 2 dígitos (ex: "03" de "1.03x")
        parte_decimal = vela_base_str.split('.')[-1].replace('x', '')
        digito1 = int(parte_decimal[0])
        digito2 = int(parte_decimal[1])
        soma_digitos = digito1 + digito2
    except (IndexError, ValueError) as e:
        print(f"Erro ao processar a vela base: {e}")
        return None, None

    # --- 2° Passo: Somar o resultado ao Horário Base ---
    formato_horario = "%H:%M:%S"
    try:
        horario_base = datetime.strptime(horario_base_str, formato_horario)
        # Adiciona a soma dos dígitos (em minutos)
        novo_horario_dt = horario_base + timedelta(minutes=soma_digitos)
        novo_horario_str = novo_horario_dt.strftime(formato_horario)
    except ValueError as e:
        print(f"Erro ao processar o horário base: {e}")
        return None, None

    # --- 3° Passo: Aplicar a Fórmula ---
    
    # 3a: Obter os 2 últimos dígitos da Rodada Base
    dois_ultimos_rodada = rodada_base_int % 100

    # 3b: Obter o minuto da Vela de Cálculo
    try:
        minuto_vela_calculo = datetime.strptime(horario_calculo_str, formato_horario).minute
    except ValueError as e:
        print(f"Erro ao processar o horário da vela de cálculo: {e}")
        return None, None
    
    # Fórmula: 0,6 * (2 Últimos Dígitos da Rodada) + Vela para Cálculo + Minuto da Vela de Cálculo
    resultado_formula = 0.6 * dois_ultimos_rodada + vela_calculo_float + minuto_vela_calculo

    return novo_horario_str, resultado_formula

# =========================================================================
# EXEMPLO DE USO (Utilizando os últimos dados que você forneceu)
# =========================================================================

# Dados de entrada
V1 = "1.03x"
H2 = "20:49:55"
R3 = 3294634
V4 = 16.64
H5 = "20:49:09"

# Executar a função
horario_final, resultado_final = calcular_sistema_personalizado(V1, H2, R3, V4, H5)

if horario_final and resultado_final is not None:
    print("\n--- Resultado do Cálculo ---")
    print(f"Horário Final: {horario_final}")
    print(f"Resultado da Fórmula: {resultado_final:.2f}")
    print(f"\nResultado Completo: {horario_final} / {resultado_final:.2f}")
