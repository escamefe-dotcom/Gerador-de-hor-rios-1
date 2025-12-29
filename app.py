from flask import Flask, render_template, request
from datetime import datetime, timedelta

app = Flask(__name__)

def calcular_proximos_horarios(multiplicador, horario_str):
    try:
        formato = "%H:%M:%S"
        horario_original = datetime.strptime(horario_str, formato)
        proximos = []

        # Regra 1: 1.01 até 1.09 -> +10 min
        if 1.01 <= multiplicador <= 1.09:
            proximos.append(horario_original + timedelta(minutes=10))

        # Regra 2: 4.00 até 4.99 -> +4 min
        elif 4.00 <= multiplicador <= 4.99:
            proximos.append(horario_original + timedelta(minutes=4))

        # Regra 3: 5.00 até 5.99 -> +5 min e +10 min
        elif 5.00 <= multiplicador <= 5.99:
            proximos.append(horario_original + timedelta(minutes=5))
            proximos.append(horario_original + timedelta(minutes=10))

        # Regra 4: 7.00 até 7.99 -> +3 min
        elif 7.00 <= multiplicador <= 7.99:
            proximos.append(horario_original + timedelta(minutes=3))

        # Regra 5: 12.00 até 12.99 -> +13 min
        elif 12.00 <= multiplicador <= 12.99:
            proximos.append(horario_original + timedelta(minutes=13))

        return [h.strftime(formato) for h in proximos]
    except Exception as e:
        return []

@app.route('/', methods=['GET', 'POST'])
def index():
    resultado = None
    if request.method == 'POST':
        # Recebe os dados do formulário do site
        vela = float(request.form.get('vela').replace(',', '.'))
        horario = request.form.get('horario')
        
        horarios_calculados = calcular_proximos_horarios(vela, horario)
        
        if horarios_calculados:
            resultado = {
                "vela": vela,
                "original": horario,
                "proximos": horarios_calculados
            }
        else:
            resultado = {"erro": "Vela fora dos critérios de análise."}

    return render_template('index.html', resultado=resultado)

if __name__ == '__main__':
    app.run(debug=True)
