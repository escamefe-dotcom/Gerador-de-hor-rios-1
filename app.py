from datetime import datetime, timedelta

def calcular_sistema_personalizado(vela_base_str: str, horario_base_str: str, rodada_base_int: int, vela_calculo_float: float, horario_calculo_str: str) -> tuple[str, float]:
    """
    Aplica a lógica de cálculo personalizada em três passos.

    Args:
        vela_base_str (str): O valor da vela base (ex: "1.03x").
        horario_base_str (str): Horário de partida (ex: "20:49:55").
        rodada_base_int (int): Número da rodada base (ex: 3294634).
        vela_calculo_float (float): O valor da vela para o cálculo (ex: 16.64).
        horario_calculo_str (str): Horário da vela para o cálculo (ex: "20:49:09").

    Returns:
        tuple: (Novo horário formatado (str), Resultado da fórmula (float))
    """

    FORMATO_HORARIO = "%H:%M:%S"

    # --- 1° Passo: Soma dos dígitos da Vela Base ---
    try:
        # Pega a parte após o ponto decimal e remove o 'x' (ex: "1.03x" -> "03")
        parte_decimal = vela_base_str.split('.')[-1].replace('x', '')
        # Garante que temos pelo menos dois dígitos para a soma
        if len(parte_decimal) < 2:
             raise ValueError("A vela base deve ter pelo menos dois dígitos decimais.")
             
        digito1 = int(parte_decimal[0])
        digito2 = int(parte_decimal[1])
        soma_minutos = digito1 + digito2
    except (IndexError, ValueError) as e:
        print(f"ERRO (1° Passo): {e}")
        return None, None

    # --- 2° Passo: Somar o resultado ao Horário Base ---
    try:
        horario_base = datetime.strptime(horario_base_str, FORMATO_HORARIO)
        # Adiciona a soma dos dígitos (em minutos)
        novo_horario_dt = horario_base + timedelta(minutes=soma_minutos)
        novo_horario_str = novo_horario_dt.strftime(FORMATO_HORARIO)
    except ValueError as e:
        print(f"ERRO (2° Passo): {e}")
        return None, None

    # --- 3° Passo: Aplicar a Fórmula ---
    
    # 3a: Obter os 2 últimos dígitos da Rodada Base (usando módulo %)
    dois_ultimos_rodada = rodada_base_int % 100

    # 3b: Obter o minuto da Vela de Cálculo
    try:
        minuto_vela_calculo = datetime.strptime(horario_calculo_str, FORMATO_HORARIO).minute
    except ValueError as e:
        print(f"ERRO (3° Passo): {e}")
        return None, None
    
    # Fórmula: 0,6 * (2 Últimos Dígitos da Rodada) + Vela para Cálculo + Minuto da Vela de Cálculo
    resultado_formula = 0.6 * dois_ultimos_rodada + vela_calculo_float + minuto_vela_calculo

    return novo_horario_str, resultado_formula

# =========================================================================
# EXEMPLO DE USO (Utilizando seus últimos dados: 1.03x / 20:49:55 / 3294634 / 16.64x / 20:49:09)
# =========================================================================

# Variáveis de entrada
VelaBase = "1.03x"
HorarioBase = "20:49:55"
RodadaBase = 3294634
VelaCalculo = 16.64
HorarioCalculo = "20:49:09"

# Execução da função
horario_final, resultado_final = calcular_sistema_personalizado(
    vela_base_str=VelaBase,
    horario_base_str=HorarioBase,
    rodada_base_int=RodadaBase,
    vela_calculo_float=VelaCalculo,
    horario_calculo_str=HorarioCalculo
)

# Impressão do resultado
if horario_final and resultado_final is not None:
    print("\n--- Resultado do Sistema ---")
    print(f"Dados Utilizados: {VelaBase} | {HorarioBase} | {RodadaBase} | {VelaCalculo} | {HorarioCalculo}")
    print(f"1. Minutos Adicionados (0+3): {3}")
    print(f"2. Novo Horário: {horario_final}")
    print(f"3. Cálculo da Fórmula (0.6 * 34 + 16.64 + 49): {resultado_final:.2f}")
    print("\nRESULTADO FINAL:")
    print(f"{horario_final} / {resultado_final:.2f}")
else:
    print("\nNão foi possível completar o cálculo devido a um erro nos dados fornecidos.")
