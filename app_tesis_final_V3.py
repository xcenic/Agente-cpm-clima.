import pandas as pd
import numpy as np

def calcular_EVB_estocastico(datos_clima, Pr, Ur, Ut, Ic, modelo_rf, H_w=8.0):
    """
    Motor Estocástico CHRONOFLUX: Calcula el Amortiguador de Valor Esperado (EVB_i)
    para una actividad específica, integrando ML termodinámico y protección OPEX.
    
    Parámetros:
    - datos_clima (DataFrame): Debe contener 'lluvia_mm', 'probabilidad', 'temperatura', 'humedad'.
    - Pr (float): Probabilidad mínima histórica (%).
    - Ur (float): Umbral de intensidad de lluvia (mm).
    - Ut (float): Umbral financiero de horas útiles requeridas.
    - Ic (float): Coeficiente de Impacto de la tarea.
    - modelo_rf (modelo predictivo): Su Random Forest ya entrenado.
    - H_w (float): Horas operativas de la jornada civil (Default: 8.0).
    
    Retorna:
    - EVB_total (float): Días totales a inyectar en el cronograma.
    """
    
    lluvia_acumulada = 0.0
    EVB_total = 0.0
    
    # Aseguramos que los índices estén limpios para la iteración
    datos_clima = datos_clima.reset_index(drop=True)
    
    for index, dia in datos_clima.iterrows():
        # Extracción segura de variables diarias
        lluvia_dia = float(dia.get('lluvia_mm', 0.0))
        prob_hist = float(dia.get('probabilidad', 0.0))
        temp_dia = float(dia.get('temperatura', 25.0))
        humedad_dia = float(dia.get('humedad', 70.0))
        
        # ---------------------------------------------------------
        # 1. TASA DE EVAPORACIÓN CONTINUA (Memoria del Terreno)
        # ---------------------------------------------------------
        # El calor resta agua al acumulado. Evita que el modelo crea 
        # que el terreno está inundado para siempre.
        tasa_evaporacion = (temp_dia / 10.0) * ((100.0 - humedad_dia) / 100.0)
        
        # Actualizamos la memoria del suelo (nunca puede ser menor a 0)
        lluvia_acumulada = max(0.0, lluvia_acumulada + lluvia_dia - tasa_evaporacion)
        
        # ---------------------------------------------------------
        # 2. COMPUERTA PROBABILÍSTICA Y VOLUMÉTRICA (Filtro)
        # ---------------------------------------------------------
        if (prob_hist >= Pr) and (lluvia_dia >= Ur):
            
            # El clima superó la tolerancia. La IA calcula el tiempo de secado (Tr).
            # Se formatea como un array 2D para cumplir con el estándar de Scikit-Learn.
            entrada_rf = np.array([[temp_dia, humedad_dia, lluvia_acumulada]])
            T_r = float(modelo_rf.predict(entrada_rf)[0])
            
            # Estimación del tiempo que estuvo lloviendo (ej. tasa de 5mm por hora)
            horas_lluvia = lluvia_dia / 5.0 
            
            # Matemáticas de tiempo útil (Jornada - Parada por lluvia - Parada por lodo)
            horas_restantes = H_w - (horas_lluvia + T_r)
            
            # ---------------------------------------------------------
            # 3. INDICATRIZ FINANCIERA OPEX (Corrección del Falso Positivo)
            # ---------------------------------------------------------
            # EL SIGNO DEBE SER '<'. Si quedan MENOS horas que el límite exigido (Ut),
            # se cancela el día para proteger el presupuesto.
            if horas_restantes < Ut:
                # Se cuantifica la pérdida basándose en la vulnerabilidad de la tarea
                EVB_total += (1.0 * Ic) 
            else:
                # Aunque llovió, el calor secó rápido y quedan horas útiles (> Ut).
                # La jornada es viable financieramente. No se inyecta retraso.
                pass
                
        else:
            # Día normal o lluvia por debajo del riesgo tolerable.
            # No se inyecta retraso.
            pass

    return round(EVB_total, 2)
