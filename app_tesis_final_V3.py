import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import xml.etree.ElementTree as ET
import requests
import io
import re
import math
import os
from datetime import datetime, timedelta, date

# LIBRERÍAS PREMIUM Y UI
import plotly.express as px
import plotly.graph_objects as go
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode, GridUpdateMode

# LIBRERÍAS DE MAPA Y GRAFOS
try:
    import folium
    from streamlit_folium import st_folium
    import networkx as nx
except ImportError:
    st.error("⚠️ Falta instalar librerías. Ejecuta: pip install folium streamlit-folium networkx plotly streamlit-aggrid")
    st.stop()

# ==============================================================================
# CONFIGURACIÓN INICIAL DE ESTADOS (SESSION STATE)
# ==============================================================================
if 'jornada_state' not in st.session_state: st.session_state['jornada_state'] = (8, 17)
if 'nlp_state' not in st.session_state: st.session_state['nlp_state'] = True
if 'ml_state' not in st.session_state: st.session_state['ml_state'] = True
if 'ag_state' not in st.session_state: st.session_state['ag_state'] = True
if 'temp_state' not in st.session_state: st.session_state['temp_state'] = 30.0
if 'hum_state' not in st.session_state: st.session_state['hum_state'] = 85.0
if 'pr_state' not in st.session_state: st.session_state['pr_state'] = 65
if 'ur_state' not in st.session_state: st.session_state['ur_state'] = 5.0
if 'ut_state' not in st.session_state: st.session_state['ut_state'] = 3.0
if 'desc_actual' not in st.session_state: st.session_state['desc_actual'] = "Ajuste manual de las variables estocásticas y logísticas del proyecto."
if 'lat_actual' not in st.session_state: st.session_state['lat_actual'] = 18.4758
if 'lon_actual' not in st.session_state: st.session_state['lon_actual'] = -69.7781
if 'ubicacion_nombre' not in st.session_state: st.session_state['ubicacion_nombre'] = "Santo Domingo Este - PROPACC LAS DAMAS"
if 'combo_ubicacion' not in st.session_state: st.session_state['combo_ubicacion'] = "Santo Domingo Este - PROPACC LAS DAMAS"
if 'simulacion_activa' not in st.session_state: st.session_state['simulacion_activa'] = False
if 'resultados_finales' not in st.session_state: st.session_state['resultados_finales'] = None
if 'audit_decision' not in st.session_state: st.session_state['audit_decision'] = None
if 'project_name' not in st.session_state: st.session_state['project_name'] = "Proyecto"

# ==============================================================================
# DICCIONARIO MAESTRO DE COORDENADAS
# ==============================================================================
COORDENADAS_RD = {
    "Santo Domingo Este - PROPACC LAS DAMAS": (18.4758, -69.7781),
    "Azua - Azua de Compostela (Cabecera)": (18.4532, -70.7349), "Baoruco - Neiba (Cabecera)": (18.4833, -71.4167),
    "Barahona - Santa Cruz de Barahona (Cabecera)": (18.2085, -71.1008), "Dajabón - Dajabón (Cabecera)": (19.5488, -71.7083),
    "Distrito Nacional - Santo Domingo (Centro)": (18.4861, -69.9312), "Duarte - San Francisco de Macorís (Cabecera)": (19.3009, -70.2525),
    "El Seibo - Santa Cruz de El Seibo (Cabecera)": (18.7656, -69.0389), "Elías Piña - Comendador (Cabecera)": (18.8767, -71.7029),
    "Espaillat - Moca (Cabecera)": (19.6267, -70.2764), "Hato Mayor - Hato Mayor del Rey (Cabecera)": (18.7622, -69.2565),
    "Hermanas Mirabal - Salcedo (Cabecera)": (19.3735, -70.4188), "Independencia - Jimaní (Cabecera)": (18.4877, -71.8515),
    "La Altagracia - Higüey (Cabecera)": (18.6147, -68.7171), "La Romana - La Romana (Cabecera)": (18.4273, -68.9728),
    "La Vega - Concepción de La Vega (Cabecera)": (19.2208, -70.5292), "María Trinidad Sánchez - Nagua (Cabecera)": (19.3667, -69.8511),
    "Monseñor Nouel - Bonao (Cabecera)": (18.9272, -70.3973), "Monte Cristi - San Fernando (Cabecera)": (19.8483, -71.6450),
    "Monte Plata - Monte Plata (Cabecera)": (18.8078, -69.7848), "Pedernales - Pedernales (Cabecera)": (18.0333, -71.7431),
    "Peravia - Baní (Cabecera)": (18.2796, -70.3319), "Puerto Plata - San Felipe (Cabecera)": (19.7934, -70.6884),
    "Samaná - Santa Bárbara (Cabecera)": (19.2056, -69.3262), "San Cristóbal - San Cristóbal (Cabecera)": (18.4162, -70.1112),
    "San José de Ocoa - Ocoa (Cabecera)": (18.5438, -70.5070), "San Juan - San Juan de la Maguana (Cabecera)": (18.8059, -71.2299),
    "San Pedro de Macorís - SPM (Cabecera)": (18.4637, -69.3041), "Sánchez Ramírez - Cotuí (Cabecera)": (19.0512, -70.1468),
    "Santiago - Santiago de los Caballeros (Cabecera)": (19.4517, -70.6970), "Santiago Rodríguez - Sabaneta (Cabecera)": (19.4791, -71.3457),
    "Valverde - Mao (Cabecera)": (19.5517, -71.0779)
}

# ==============================================================================
# BASE DE DATOS DE ENSAYOS (PRESETS DE VALIDACIÓN - PRO ADVANCED)
# ==============================================================================
PRESETS_MODELOS = {
    "Personalizado (Ajuste Manual)": {
        "desc": "Modo de operación libre. Ajuste los deslizadores paramétricos según su criterio profesional forense.",
    },
    "01: CFX-VAL-01-BASE (Determinista Puro)": {
        "nlp": False, "ml": False, "pr": 100, "ur": 50.0, "ut": 1.0, "temp": 27.5, "hum": 70.0, "jornada": (8, 17),
        "desc": "Baseline determinista. Capa IA desactivada y umbrales inalcanzables. El motor CPM arrojará una inyección EVB nula (Cero desviación algorítmica)."
    },
    "02: CFX-VAL-02-CICLO (Sensibilidad Otoño)": {
        "nlp": True, "ml": True, "pr": 40, "ur": 1.5, "ut": 3.0, "temp": 28.5, "hum": 74.8, "jornada": (8, 17),
        "desc": "Simula los meses críticos de ciclones (Sept-Oct). Alta humedad y captura de eventos pluviométricos convectivos frecuentes."
    },
    "03: CFX-VAL-03-ESTIAJE (Ventana Seca)": {
        "nlp": True, "ml": True, "pr": 70, "ur": 5.0, "ut": 2.0, "temp": 26.4, "hum": 65.6, "jornada": (8, 17),
        "desc": "Simula Enero-Febrero. Reconoce la 'ventana seca' reduciendo drásticamente el EVB. Valida que el modelo no penalice falsamente el Gantt."
    },
    "04: CFX-VAL-04-OPEX (Estrés Logístico Moderado)": {
        "nlp": True, "ml": True, "pr": 60, "ur": 2.5, "ut": 5.5, "temp": 27.8, "hum": 70.0, "jornada": (8, 17),
        "desc": "Protección de costos indirectos. Si la lluvia drena > 2.5h, se pierde el día completo para proteger el OPEX de la maquinaria pesada."
    },
    "05: CFX-VAL-05-HEAT (Evaporación Extrema)": {
        "nlp": True, "ml": True, "pr": 50, "ur": 3.5, "ut": 2.5, "temp": 32.0, "hum": 55.0, "jornada": (8, 17),
        "desc": "Radiación extrema. Random Forest computa Tr mínimo. Tras una precipitación, la alta temperatura seca rápidamente el estrato."
    },
    "06: CFX-VAL-06-VAGUADA (Saturación Extrema)": {
        "nlp": True, "ml": True, "pr": 30, "ur": 1.0, "ut": 4.0, "temp": 24.5, "hum": 95.0, "jornada": (8, 17),
        "desc": "Saturación capilar. Baja temperatura y altísima humedad anulan la evapotranspiración latente. Genera bloqueos prolongados."
    },
    "07: CFX-VAL-07-NLP (Auditoría Semántica)": {
        "nlp": False, "ml": True, "pr": 60, "ur": 3.0, "ut": 3.0, "temp": 28.0, "hum": 70.0, "jornada": (8, 17),
        "desc": "Desactiva Transformer NLP. El sistema utiliza heurística de expresiones regulares para asignar vulnerabilidades de materiales."
    },
    "08: CFX-VAL-08-ML (Auditoría Termodinámica)": {
        "nlp": True, "ml": False, "pr": 60, "ur": 3.0, "ut": 3.0, "temp": 28.0, "hum": 70.0, "jornada": (8, 17),
        "desc": "Desactiva Random Forest. El modelo utiliza retrasos fijos ignorando el microclima térmico e hídrico del entorno real."
    },
    "09: CFX-VAL-09-OVERTIME (Turnos Extendidos)": {
        "nlp": True, "ml": True, "pr": 50, "ur": 4.0, "ut": 1.5, "temp": 28.2, "hum": 72.0, "jornada": (7, 18),
        "desc": "Dilución del impacto. Al expandir la jornada operativa (11 horas), el daño porcentual a la ruta crítica decrece."
    },
    "10: CFX-VAL-10-COLLAPSE (Worst-Case General)": {
        "nlp": True, "ml": True, "pr": 20, "ur": 0.5, "ut": 6.0, "temp": 25.0, "hum": 88.0, "jornada": (8, 17),
        "desc": "Estrés sistémico medio. Captura trazas mínimas de lluvia y penaliza agresivamente la eficiencia. Obliga alertas prescriptivas."
    },
    # ---- NUEVOS 10 MODELOS AVANZADOS (11-20) ----
    "11: CFX-VAL-11-CLAY (Hipersensibilidad Cohesiva)": {
        "nlp": True, "ml": True, "pr": 60, "ur": 2.0, "ut": 4.0, "temp": 27.0, "hum": 70.0, "jornada": (8, 17),
        "desc": "Audita la respuesta PIML en arcillas A-7-6. Almacena agua capilar, obligando a NetworkX a empujar fechas tempranas (ES') asintóticamente."
    },
    "12: CFX-VAL-12-GRAN (Infiltración Darciana)": {
        "nlp": True, "ml": True, "pr": 60, "ur": 5.0, "ut": 2.0, "temp": 27.0, "hum": 70.0, "jornada": (8, 17),
        "desc": "Evalúa suelos A-1-a. Alta permisividad pluvial que demuestra la rápida infiltración gravitacional en bases granulares."
    },
    "13: CFX-VAL-13-DEPR (Depresión Tropical)": {
        "nlp": True, "ml": True, "pr": 15, "ur": 0.5, "ut": 6.5, "temp": 25.0, "hum": 85.0, "jornada": (8, 17),
        "desc": "Baja presión atmosférica. Simula llovizna constante. Prescribe paralización total al registrar trazas que destruyen la tracción mecánica."
    },
    "14: CFX-VAL-14-SHIFT (Fast-Tracking Logístico)": {
        "nlp": True, "ml": True, "pr": 55, "ur": 3.0, "ut": 2.0, "temp": 28.2, "hum": 72.0, "jornada": (7, 18),
        "desc": "Verificación del operador de cuantización Q. El incremento del divisor de ventana (Hw) amortigua las anomalías climáticas matutinas."
    },
    "15: CFX-VAL-15-HEAT (Isla de Calor Estival)": {
        "nlp": True, "ml": True, "pr": 65, "ur": 3.5, "ut": 2.5, "temp": 38.0, "hum": 45.0, "jornada": (8, 17),
        "desc": "Temperatura llevada a sus límites. Evalúa el límite asintótico del secado (Tr → 0) post-lluvia, ahorrando holguras."
    },
    "16: CFX-VAL-16-HUM (Punto de Rocío/Niebla)": {
        "nlp": True, "ml": True, "pr": 65, "ur": 3.5, "ut": 2.5, "temp": 24.0, "hum": 98.0, "jornada": (8, 17),
        "desc": "Anulación del déficit de presión de vapor. Aire saturado impide la evapotranspiración. Genera bloqueos masivos."
    },
    "17: CFX-VAL-17-OPEX (Restricción Financiera Severa)": {
        "nlp": True, "ml": True, "pr": 50, "ur": 2.0, "ut": 7.0, "temp": 27.5, "hum": 70.0, "jornada": (8, 17),
        "desc": "Intolerancia a la ineficiencia económica. Con Ut=7.0h, una sola hora de lluvia descarta la jornada operativa para blindar el flujo de caja."
    },
    "18: CFX-VAL-18-FLASH (Lluvias Convectivas Torrenciales)": {
        "nlp": True, "ml": True, "pr": 10, "ur": 15.0, "ut": 1.0, "temp": 28.0, "hum": 75.0, "jornada": (8, 17),
        "desc": "Filtra lloviznas (Ur=15mm). Aísla e impacta la matriz topológica exclusivamente bajo aguaceros masivos que desbordan drenajes."
    },
    "19: CFX-VAL-19-BLIND (Fallo Cognitivo Cruzado)": {
        "nlp": False, "ml": False, "pr": 60, "ur": 3.0, "ut": 3.0, "temp": 28.0, "hum": 70.0, "jornada": (8, 17),
        "desc": "Muerte de ambas IAs. Todo se procesa con penalizaciones deterministas ciegas. Sirve de contraste forense para medir los días salvados por la IA."
    },
    "20: CFX-VAL-20-SWAN (Cisne Negro / Colapso Asintótico)": {
        "nlp": True, "ml": True, "pr": 10, "ur": 0.1, "ut": 8.0, "temp": 25.0, "hum": 88.0, "jornada": (8, 17),
        "desc": "Prueba de tensión máxima. Cualquier traza pluviométrica paraliza la obra completa. Evalúa que Kahn no entre en bucle de recursión infinita."
    }
}

# Callback para aplicar el preset
def aplicar_preset():
    seleccion = st.session_state.selector_preset
    st.session_state['desc_actual'] = PRESETS_MODELOS[seleccion]['desc']
    
    if seleccion != "Personalizado (Ajuste Manual)":
        p = PRESETS_MODELOS[seleccion]
        st.session_state.nlp_state = p['nlp']
        st.session_state.ml_state = p['ml']
        st.session_state.pr_state = p['pr']
        st.session_state.ur_state = float(p['ur'])
        st.session_state.ut_state = float(p['ut'])
        st.session_state.temp_state = float(p['temp'])
        st.session_state.hum_state = float(p['hum'])
        st.session_state.jornada_state = p['jornada']
        
        # Volar automáticamente a Propacc Las Damas
        st.session_state.combo_ubicacion = "Santo Domingo Este - PROPACC LAS DAMAS"
        st.session_state.lat_actual = 18.4758
        st.session_state.lon_actual = -69.7781
        st.session_state.ubicacion_nombre = "Santo Domingo Este - PROPACC LAS DAMAS"

# ==============================================================================
# MÓDULOS DE INTELIGENCIA ARTIFICIAL Y MACHINE LEARNING
# ==============================================================================
try:
    from transformers import pipeline
    from sklearn.ensemble import RandomForestRegressor
    import numpy as np
    import warnings
    warnings.filterwarnings("ignore")
    IA_DISPONIBLE = True
except ImportError:
    st.sidebar.error("⚠️ Faltan librerías de IA.")
    IA_DISPONIBLE = False

@st.cache_resource(show_spinner=False)
def cargar_motor_nlp():
    if not IA_DISPONIBLE: return None
    try: return pipeline("zero-shot-classification", model="Recognai/zeroshot_selectra_medium")
    except: return None

nlp_classifier = cargar_motor_nlp()

def calcular_ic_ia(nombre_tarea, usar_ia=True):
    nombre_str = str(nombre_tarea).lower()
    if not usar_ia or not nlp_classifier:
        if any(w in nombre_str for w in ['acero', 'hormigon', 'hormigón', 'encofrado', 'vaciado', 'muro', 'alcantarilla', 'losa', 'zapata', 'columna', 'viga', 'platea', 'fundacion', 'fundación', 'estructura', 'paisajismo', 'limpieza', 'grama', 'terminacion', 'terminación']): return 1.0
        elif any(w in nombre_str for w in ['pintura', 'señalizacion', 'señalización']): return 1.5
        elif any(w in nombre_str for w in ['base', 'subbase', 'sub-base', 'granular', 'afirmado', 'asfalto', 'imprimacion', 'imprimación']): return 2.0
        elif any(w in nombre_str for w in ['corte', 'relleno', 'subrasante', 'tierra', 'excavacion', 'excavación']): return 3.0
        return 1.5

    categorias = ["estructuras de hormigón y acero", "pavimento asfáltico y terminaciones", "bases granulares y subbases", "movimiento de tierras pesado y excavación"]
    mapa_ic = {categorias[0]: 1.0, categorias[1]: 1.5, categorias[2]: 2.0, categorias[3]: 3.0}
    try:
        res = nlp_classifier(nombre_str, categorias)
        return mapa_ic[res['labels'][0]]
    except: return 1.5

@st.cache_resource(show_spinner=False)
def entrenar_modelo_termodinamico():
    if not IA_DISPONIBLE: return None
    X = np.array([[40, 25, 85, 1], [15, 32, 60, 1], [50, 28, 90, 1],
                  [40, 25, 85, 2], [15, 32, 60, 2], [50, 28, 90, 2],
                  [40, 25, 85, 3], [15, 32, 60, 3], [50, 28, 90, 3]])
    y = np.array([3.5, 1.5, 4.0, 1.5, 0.5, 2.0, 2.0, 1.0, 3.0])
    modelo = RandomForestRegressor(n_estimators=100, random_state=42)
    modelo.fit(X, y)
    return modelo

ml_tr_model = entrenar_modelo_termodinamico()

def calcular_tr_y_ic_dinamico(lluvia_mm, temp_c, humedad_pct, tipo_suelo_ic, usar_ia=True):
    if not usar_ia or not ml_tr_model:
        if tipo_suelo_ic >= 3.0: return 48.0, tipo_suelo_ic
        elif tipo_suelo_ic >= 2.0: return 24.0, tipo_suelo_ic
        elif tipo_suelo_ic >= 1.5: return 12.0, tipo_suelo_ic
        else: return 0.0, tipo_suelo_ic
        
    suelo_cat = 1 if tipo_suelo_ic >= 3.0 else (2 if tipo_suelo_ic >= 2.0 else 3)
    tr_dias = ml_tr_model.predict([[lluvia_mm, temp_c, humedad_pct, suelo_cat]])[0]
    tr_horas = round(tr_dias * 24.0, 1)
    ic_dinamico = round(1.0 + tr_dias, 2)
    return tr_horas, ic_dinamico

def agente_prescriptivo_mitigacion(df_tareas, evb_total):
    sugerencias = []
    if evb_total < 3:
        return ["✅ **Red Logística Estable:** El riesgo climático actual es bajo y puede ser absorbido por las holguras normales del cronograma."]
    
    tierras = df_tareas[pd.to_numeric(df_tareas['Tr (Secado/Horas)'], errors='coerce') >= 48.0]
    if not tierras.empty:
        peor_tarea = tierras.loc[pd.to_numeric(tierras['Días Impacto'], errors='coerce').idxmax()]
        sugerencias.append(f"🧠 **Alerta Geotécnica:** La tarea **'{peor_tarea['Actividad']}'** es el principal cuello de botella. Tras las lluvias, este frente quedará inoperativo por saturación de agua (Alto Tiempo de Secado).")
        sugerencias.append("👉 **Estrategia Logística Sugerida:** Evite mantener los recursos inactivos esperando que el suelo recupere su capacidad de soporte. Se recomienda reasignar temporalmente la maquinaria y las cuadrillas de este frente hacia partidas estructurales (ej. Hormigonado, Encofrados o Acero).")
        sugerencias.append("⚙️ **Justificación Técnica:** Las tareas estructurales poseen inmunidad hídrica post-lluvia (Coeficiente de Impacto = 1.0). Al redirigir los recursos hacia estas actividades, se neutraliza la pérdida de horas-hombre y se mitiga significativamente el retraso global del proyecto.")
    return sugerencias

# ==============================================================================
# FUNCIONES DE SOPORTE Y DATOS CLIMÁTICOS
# ==============================================================================
def calcular_pascua(year):
    a = year % 19; b = year // 100; c = year % 100; d = b // 4; e = b % 4; f = (b + 8) // 25
    g = (b - f + 1) // 3; h = (19 * a + b - d - g + 15) % 30; i = c // 4; k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7; m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31; day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)

@st.cache_data
def obtener_feriados_rd():
    feriados = {}
    current_year = date.today().year
    for y in range(current_year, current_year + 3):
        pascua = calcular_pascua(y)
        feriados.update({
            date(y, 1, 1): "Año Nuevo", date(y, 1, 6): "Día de los Reyes", date(y, 1, 21): "Día de la Altagracia",
            date(y, 1, 26): "Día de Duarte", date(y, 2, 27): "Independencia", pascua - timedelta(days=2): "Viernes Santo",
            date(y, 5, 1): "Día del Trabajo", pascua + timedelta(days=60): "Corpus Christi",
            date(y, 8, 16): "Restauración", date(y, 9, 24): "Las Mercedes",
            date(y, 11, 6): "Constitución", date(y, 12, 25): "Navidad"
        })
    return feriados, current_year

feriados_dict, anio_actual = obtener_feriados_rd()

def es_habil(fecha, dias_ok_idx, feriados):
    if fecha.weekday() not in dias_ok_idx: return False
    if fecha in feriados: return False
    return True

@st.cache_data(ttl=timedelta(days=7), show_spinner=False)
def obtener_clima_horario_laboral(lat, lon, hora_inicio, hora_fin):
    lat_r = round(lat, 2); lon_r = round(lon, 2)
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat_r}&longitude={lon_r}&start_date=2014-01-01&end_date=2023-12-31&hourly=precipitation,temperature_2m,relative_humidity_2m&timezone=auto"
    try:
        r = requests.get(url)
        data = r.json()
        df = pd.DataFrame({
            'time': pd.to_datetime(data['hourly']['time']), 
            'mm': data['hourly']['precipitation'],
            'temp': data['hourly']['temperature_2m'],
            'hum': data['hourly']['relative_humidity_2m']
        })
        df['hora'] = df['time'].dt.hour
        df_laboral = df[(df['hora'] >= hora_inicio) & (df['hora'] <= hora_fin)].copy()
        df_laboral['fecha_date'] = df_laboral['time'].dt.date
        
        df_daily = df_laboral.groupby('fecha_date').agg(
            mm=('mm', 'sum'),
            temp=('temp', 'mean'),
            hum=('hum', 'mean')
        ).reset_index()
        
        df_daily['dia_mes'] = pd.to_datetime(df_daily['fecha_date']).dt.strftime('%m-%d')
        df_daily['fecha_full'] = pd.to_datetime(df_daily['fecha_date'])
        df_daily['lluvio'] = (df_daily['mm'] > 0.5).astype(int)
        
        clima_map = df_daily.groupby('dia_mes').agg(
            probabilidad=('lluvio', 'mean'), 
            mm_promedio=('mm', 'mean'),
            ultima_fecha_lluvia=('fecha_full', lambda x: x[df_daily.loc[x.index, 'mm'] > 0.5].max() if (df_daily.loc[x.index, 'mm'] > 0.5).any() else None)
        ).to_dict('index')
        
        df_daily['mes_num'] = pd.to_datetime(df_daily['fecha_date']).dt.month
        mapa_meses = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dic'}
        df_daily['Mes'] = df_daily['mes_num'].map(mapa_meses)
        df_grafico = df_daily.groupby(['mes_num', 'Mes']).agg(
            mm=('mm', 'mean'), 
            prob_lluvia=('lluvio', 'mean'),
            temp=('temp', 'mean'),
            hum=('hum', 'mean')
        ).reset_index()
        
        return df_grafico, clima_map, list(mapa_meses.values())
    except Exception as e: 
        return None, None, None

def redondear_duracion(val): return round(float(val), 2)

def auditar_xml(file):
    tree = ET.parse(file)
    root = tree.getroot()
    prefix = root.tag.split("}")[0] + "}" if "}" in root.tag else ""
    title = root.find(prefix + "Title")
    st.session_state['project_name'] = title.text if (title is not None and title.text) else "Proyecto_Exportado"
    hours_per_day = 8.0
    h_pd_node = root.find(prefix + "MinutesPerDay")
    if h_pd_node is not None and h_pd_node.text:
        try: hours_per_day = float(h_pd_node.text) / 60.0
        except: pass

    def parse_duration_days(dur_str):
        if not dur_str: return 0.0
        match = re.search(r'PT(\d+)H', dur_str)
        if match: return float(match.group(1)) / hours_per_day 
        return 0.0

    def find_val(el, tag):
        x = el.find(prefix + tag)
        return x.text if x is not None else None

    tareas, uid_to_id, valid_ids = [], {}, []

    for task in root.iter(prefix + 'Task'):
        uid = find_val(task, 'UID')
        row_id = find_val(task, 'ID')
        active = find_val(task, 'Active')
        summary = find_val(task, 'Summary')
        if uid and row_id: uid_to_id[uid] = row_id
        if active != '0' and summary == '0' and row_id:
            try: valid_ids.append(int(row_id))
            except: pass
    valid_ids.sort()

    for task in root.iter(prefix + 'Task'):
        active = find_val(task, 'Active')
        if active != '0': 
            tid = int(find_val(task, 'ID') or 0)
            is_summary = (find_val(task, 'Summary') == '1')
            is_milestone = (find_val(task, 'Milestone') == '1')
            preds = []
            for link in task.findall(prefix + 'PredecessorLink'):
                p_uid = find_val(link, 'PredecessorUID')
                if p_uid: preds.append(uid_to_id.get(p_uid, p_uid))
            orig_preds = ", ".join(preds)
            errores = []
            if not is_summary and not is_milestone:
                constraint = int(find_val(task, 'ConstraintType') or '0')
                if not preds and tid > 1 and constraint <= 1:
                    prev = [x for x in valid_ids if x < tid]
                    sug = prev[-1] if prev else "N/A"
                    errores.append(f"Falta Predecesora (Sugerido ID {sug})")
            
            tareas.append({
                'ID': tid, 'Name': find_val(task, 'Name'), 'WBS': find_val(task, 'WBS'),
                'Start_XML': find_val(task, 'Start'), 'Finish_XML': find_val(task, 'Finish'), 
                'Duration_Days': parse_duration_days(find_val(task, 'Duration')),
                'IsSummary': is_summary, 'IsMilestone': is_milestone,
                'OrigPreds': orig_preds, 'Errores': " | ".join(errores) if errores else "OK"
            })
    return pd.DataFrame(tareas).sort_values('ID')

def simular_cronograma(df, clima, prob_min, mm_min, dias_idx, feriados, reparar, umbral_horas, h_inicio, h_fin, use_nlp, use_ml, temp_global, hum_global):
    G = nx.DiGraph()
    for _, row in df.iterrows():
        tid = row['ID']
        G.add_node(tid, data=row.to_dict())
        new_preds = str(row['OrigPreds']) if pd.notna(row['OrigPreds']) else ""
        if reparar == "Automática" and "Falta Predecesora" in row['Errores']:
            match = re.search(r'ID (\d+)', row['Errores'])
            if match: new_preds = match.group(1)
        G.nodes[tid]['new_preds'] = new_preds
        if new_preds.strip():
            for p in new_preds.split(','):
                p = p.strip()
                if p.isdigit() and int(p) != tid: G.add_edge(int(p), tid)
                    
    try: orden = list(nx.topological_sort(G))
    except nx.NetworkXUnfeasible: orden = df['ID'].tolist() 
        
    fecha_fin_calculada = {}
    res_temp = {}

    for tid in orden:
        row = G.nodes[tid]['data']
        new_preds = G.nodes[tid]['new_preds']
        note = "Corregido Auto" if (reparar == "Automática" and "Falta Predecesora" in row['Errores']) else row['Errores']
            
        start_dt = pd.to_datetime(row['Start_XML']).date() if pd.notna(row['Start_XML']) else None
        finish_dt = pd.to_datetime(row['Finish_XML']).date() if pd.notna(row['Finish_XML']) else None
        base_dur_float = float(row['Duration_Days'])
        
        preds_list = [int(p.strip()) for p in new_preds.split(',') if p.strip().isdigit()]
        max_shift_dias = 0
        if preds_list and start_dt:
            for p in preds_list:
                if p in fecha_fin_calculada and fecha_fin_calculada[p] is not None:
                    fin_base_pred = G.nodes[p]['data']['Finish_XML']
                    fin_base_pred = pd.to_datetime(fin_base_pred).date() if pd.notna(fin_base_pred) else None
                    if fin_base_pred:
                        shift = (fecha_fin_calculada[p] - fin_base_pred).days
                        if shift > max_shift_dias: max_shift_dias = shift
                            
        new_start = start_dt
        if max_shift_dias > 0 and start_dt:
            new_start = start_dt + timedelta(days=max_shift_dias)
            while not es_habil(new_start, dias_idx, feriados): new_start += timedelta(days=1)
                
        new_finish = finish_dt
        new_dur_float = base_dur_float
        
        stats_prob = 0.0; prob_acumulada = 0.0; dias_evaluados = 0
        stats_mm = 0; rain_total = 0.0; retraso_teorico_dias = 0.0; last_rain_date = None

        ic_base = calcular_ic_ia(row['Name'], use_nlp)
        tr_horas, impacto_constructivo_ic = calcular_tr_y_ic_dinamico(mm_min, temp_global, hum_global, ic_base, use_ml)
        
        if not row['IsSummary'] and not row['IsMilestone'] and new_start:
            work_needed = math.ceil(base_dur_float) if base_dur_float > 0 else 1
            work_done = 0; cursor = new_start
            
            while work_done < work_needed:
                if es_habil(cursor, dias_idx, feriados):
                    k = cursor.strftime('%m-%d')
                    if k in clima:
                        h = clima[k]
                        rain_total += h['mm_promedio']
                        prob_acumulada += h['probabilidad']
                        dias_evaluados += 1
                        if h['probabilidad'] >= prob_min and h['mm_promedio'] >= mm_min:
                            stats_mm = max(stats_mm, h['mm_promedio'])
                            retraso_teorico_dias += (h['probabilidad'] * impacto_constructivo_ic)
                            if h['ultima_fecha_lluvia']: last_rain_date = h['ultima_fecha_lluvia'].date()
                    work_done += 1 
                cursor += timedelta(days=1)
                
            stats_prob = (prob_acumulada / dias_evaluados) if dias_evaluados > 0 else 0
                
            nota_cuantizacion = ""
            total_cuantizado = base_dur_float
            if retraso_teorico_dias > 0:
                duracion_total_teorica = base_dur_float + retraso_teorico_dias
                total_cuantizado = math.ceil(duracion_total_teorica * 2) / 2
                fraccion = total_cuantizado % 1
                horas_trabajadas = 8.0 if fraccion == 0 else (fraccion * 8.0)
                
                if horas_trabajadas < umbral_horas:
                    total_cuantizado = math.ceil(total_cuantizado)
                    
                retraso_cuantizado = total_cuantizado - base_dur_float
                if retraso_cuantizado != retraso_teorico_dias:
                    nota_cuantizacion = f" (Q={round(retraso_cuantizado, 2)}d)"
            else:
                retraso_cuantizado = 0.0

            if note == "OK" and retraso_cuantizado > 0:
                note = f"Impacto Clima{nota_cuantizacion} [Ic={impacto_constructivo_ic}]"
            elif note != "OK" and retraso_cuantizado > 0:
                note += f" | Impacto Clima{nota_cuantizacion} [Ic={impacto_constructivo_ic}]"
            
            dias_a_avanzar = math.ceil(total_cuantizado) if total_cuantizado > 0 else 1
            cursor_fin = new_start; dias_avanzados = 1
            while dias_avanzados < dias_a_avanzar:
                cursor_fin += timedelta(days=1)
                if es_habil(cursor_fin, dias_idx, feriados): dias_avanzados += 1
            
            new_finish = cursor_fin; new_dur_float = total_cuantizado
            is_pushed_by_pred = (new_start > start_dt) if start_dt else False
            if not is_pushed_by_pred and retraso_cuantizado == 0 and finish_dt:
                new_finish = finish_dt; new_dur_float = base_dur_float
            
        elif row['IsMilestone']:
            new_dur_float = 0; stats_prob = 0
            if new_start: new_finish = new_start
                
        fecha_fin_calculada[tid] = new_finish
        G.nodes[tid]['ES'] = new_start; G.nodes[tid]['EF'] = new_finish; G.nodes[tid]['dur_ajustada'] = new_dur_float

        res_temp[tid] = {
            'ID': tid, 'WBS': row['WBS'], 'Actividad': row['Name'], 'IsSummary': row['IsSummary'], 'IsMilestone': row['IsMilestone'],
            'Duración Base': redondear_duracion(base_dur_float), 'Inicio Base': start_dt, 'Fin Base': finish_dt,
            'Duración Nueva': redondear_duracion(new_dur_float), 'Inicio Nuevo': new_start, 'Fin Nuevo': new_finish,
            'Tr (Secado/Horas)': tr_horas, 'Ic_Estimado': impacto_constructivo_ic,
            'Pred. Orig': row['OrigPreds'], 'Pred. Nueva': new_preds,
            'Prob. Lluvia': f"{stats_prob:.0%}" if stats_prob > 0 else "-", 'mm Lluvia Max': round(stats_mm, 1) if stats_mm > 0 else "-",
            'Lluvia Total Acum (mm)': round(rain_total, 1), 'Fecha Última Lluvia': last_rain_date if last_rain_date else "-",
            'Días Impacto': redondear_duracion(new_dur_float) - redondear_duracion(base_dur_float), 'Estado': note,
            'IsRain': ((redondear_duracion(new_dur_float) - redondear_duracion(base_dur_float)) > 0), 'IsLogic': (new_preds != row['OrigPreds']) 
        }

    valid_efs = [data['EF'] for n, data in G.nodes(data=True) if data.get('EF') is not None]
    max_project_ef = max(valid_efs) if valid_efs else None

    # Backward Pass
    for tid in reversed(orden):
        node = G.nodes[tid]
        if node.get('EF') is None: continue

        succs = list(G.successors(tid))
        if not succs: node['LF'] = max_project_ef
        else:
            valid_ls = [G.nodes[s].get('LS') for s in succs if G.nodes[s].get('LS') is not None]
            if valid_ls:
                min_succ_ls = min(valid_ls); cursor = min_succ_ls - timedelta(days=1)
                while not es_habil(cursor, dias_idx, feriados): cursor -= timedelta(days=1)
                node['LF'] = cursor
            else: node['LF'] = max_project_ef

        dur = math.ceil(node.get('dur_ajustada', 0)); cursor = node['LF']
        if dur > 1:
            days_stepped = 1
            while days_stepped < dur:
                cursor -= timedelta(days=1)
                if es_habil(cursor, dias_idx, feriados): days_stepped += 1
        node['LS'] = cursor

        ef = node['EF']; lf = node['LF']; tf_days = 0
        if ef and lf and lf >= ef:
            c = ef
            while c < lf:
                c += timedelta(days=1)
                if es_habil(c, dias_idx, feriados): tf_days += 1
        elif ef and lf and lf < ef:
            c = lf
            while c < ef:
                c += timedelta(days=1)
                if es_habil(c, dias_idx, feriados): tf_days -= 1

        node['TF'] = tf_days; node['is_critical'] = (tf_days <= 0)
        res_temp[tid]['Holgura (Días)'] = tf_days; res_temp[tid]['Ruta Crítica'] = "Sí" if tf_days <= 0 else "No"
        impact = res_temp[tid]['Días Impacto']
        res_temp[tid]['Nivel Riesgo'] = "Crítico (Mutada)" if (tf_days <= 0 and impact > 0) else ("Alto" if impact > 2 else "Normal")

    df_res = pd.DataFrame(list(res_temp.values())).sort_values('ID')
    df_res['Holgura (Días)'] = df_res['Holgura (Días)'].astype(object)
    df_res['Tr (Secado/Horas)'] = df_res['Tr (Secado/Horas)'].astype(object)

    for i in df_res[df_res['IsSummary'] == True].index:
        wbs_val = str(df_res.at[i, 'WBS']); wbs_prefix = wbs_val + '.'
        children = df_res[(df_res['WBS'].astype(str).str.startswith(wbs_prefix)) & (df_res['IsSummary'] == False)]
        if children.empty and (df_res.at[i, 'ID'] == 0 or wbs_val == '0' or wbs_val == 'None'):
            children = df_res[df_res['IsSummary'] == False]
            
        if not children.empty:
            min_start = children['Inicio Nuevo'].dropna().min()
            max_finish = children['Fin Nuevo'].dropna().max()
            if pd.notna(min_start): df_res.at[i, 'Inicio Nuevo'] = min_start
            if pd.notna(max_finish): df_res.at[i, 'Fin Nuevo'] = max_finish
            
            if pd.notna(min_start) and pd.notna(max_finish) and max_finish >= min_start:
                c_dias = 0; cursor = min_start
                while cursor <= max_finish:
                    if es_habil(cursor, dias_idx, feriados): c_dias += 1
                    cursor += timedelta(days=1)
                
                df_res.at[i, 'Duración Nueva'] = c_dias
                impacto_resumen = c_dias - df_res.at[i, 'Duración Base']
                df_res.at[i, 'Días Impacto'] = impacto_resumen
                df_res.at[i, 'Nivel Riesgo'] = "Alto" if impacto_resumen > 0 else "Normal"
            else: df_res.at[i, 'Días Impacto'] = 0; df_res.at[i, 'Nivel Riesgo'] = "N/A"
                
            df_res.at[i, 'Prob. Lluvia'] = "-"; df_res.at[i, 'mm Lluvia Max'] = "-"
            df_res.at[i, 'Holgura (Días)'] = "-"; df_res.at[i, 'Ruta Crítica'] = "-"; df_res.at[i, 'Tr (Secado/Horas)'] = "-"
            
    df_res['ID'] = pd.to_numeric(df_res['ID'], errors='coerce')
    return df_res.sort_values('ID').reset_index(drop=True)

# ==============================================================================
# CONFIGURACIÓN Y ESTILO (UI/UX MODERN SAAS)
# ==============================================================================
st.set_page_config(page_title="CHRONOFLUX | Motor CPM Estocástico", layout="wide", page_icon="⚡")

st.markdown("""
    <style>
        .block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; }
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;800&display=swap');
        html, body, [class*="css"]  { font-family: 'Inter', sans-serif !important; }
        .stApp { background-color: #F8FAFC; } 
        #MainMenu {visibility: hidden;} footer {visibility: hidden;}
        [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E2E8F0; }
        
        .stButton>button { background-color: #AF1E2D; color: white !important; border-radius: 8px; border: none; transition: all 0.3s ease; font-weight: 600; padding: 0.5rem 1rem; box-shadow: 0 4px 6px -1px rgba(175, 30, 45, 0.2); }
        .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(175, 30, 45, 0.3); background-color: #901924; }
        
        [data-testid="stSidebar"] .stDownloadButton > button {
            background-color: #64748B !important; color: #FFFFFF !important; border: 1px solid #475569 !important; border-radius: 6px !important;
            font-weight: 500 !important; font-size: 0.9rem !important; width: 100% !important; box-shadow: none !important; transition: background-color 0.2s ease !important; margin-top: 20px;
        }
        [data-testid="stSidebar"] .stDownloadButton > button:hover { background-color: #475569 !important; border-color: #334155 !important; }

        .kpi-container { display: flex; justify-content: space-between; gap: 20px; margin-bottom: 30px; }
        .kpi-box { background-color: #FFFFFF; border-radius: 12px; padding: 24px; flex: 1; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05); border: 1px solid #F1F5F9; transition: transform 0.2s ease; position: relative; overflow: hidden; }
        .kpi-box:hover { transform: translateY(-4px); box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1); }
        .kpi-box::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 4px; background-color: #0F172A; }
        .kpi-title { font-size: 0.85rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 700; margin-bottom: 8px; }
        .kpi-value { font-size: 2.8rem; font-weight: 800; color: #0F172A; line-height: 1.1; letter-spacing: -0.02em; }
        .kpi-value span { font-size: 1.2rem; font-weight: 600; color: #94A3B8; }
        .kpi-value.danger { color: #AF1E2D; }
        .kpi-subtitle { font-size: 0.85rem; color: #94A3B8; margin-top: 8px; }
        .ia-card { background-color: #F0F9FF; padding: 1.5rem; border-left: 4px solid #0EA5E9; border-radius: 8px; margin-bottom: 1rem; color: #0369A1; font-weight: 500; font-size: 0.95rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05);}
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# INTERFAZ PRINCIPAL Y BARRA LATERAL
# ==============================================================================
with st.sidebar:
    st.header("🗂️ Casos de Ensayo (Presets)")
    st.selectbox("Seleccionar Modelo de Validación:", list(PRESETS_MODELOS.keys()), key="selector_preset", on_change=aplicar_preset)
    st.info(f"ℹ️ **Info:** {st.session_state['desc_actual']}")
    st.markdown("---")
    
    st.header("⚙️ Configuración Logística")
    st.subheader("1. Horario de Obra")
    h_inicio, h_fin = st.slider("Jornada", 0, 23, key='jornada_state')
    
    st.subheader("2. Días Laborables")
    dias_sel = st.multiselect("Seleccionar:", ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"], default=["Lun","Mar","Mié","Jue","Vie"])
    mapa_d = {"Lun":0,"Mar":1,"Mié":2,"Jue":3,"Vie":4,"Sáb":5,"Dom":6}
    dias_idx = [mapa_d[d] for d in dias_sel]
    
    st.markdown("---")
    st.header("🧠 Capa Cognitiva e Inteligencia Artificial")
    activar_nlp = st.toggle("Procesamiento de Lenguaje Natural (NLP)", key='nlp_state')
    activar_ml = st.toggle("Motor Random Forest (Tiempo Secado Tr)", key='ml_state')
    activar_ag = st.toggle("Agente Prescriptivo (Mitigación)", key='ag_state')
    
    st.markdown("---")
    st.subheader("🌡️ Termodinámica (Inferencia Continua)")
    temp_global = st.slider("Temperatura Ambiente (°C)", 15.0, 45.0, step=0.5, key='temp_state')
    hum_global = st.slider("Humedad Relativa (%)", 30.0, 100.0, step=1.0, key='hum_state')

    # ---------------- DESCARGA DE MANUAL (AL FINAL DE LA BARRA LATERAL) ----------------
    st.markdown("<br><br>", unsafe_allow_html=True)
    try:
        with open("CHRONOFLUX_USER_MANUAL.pdf", "rb") as pdf_file:
            pdf_bytes = pdf_file.read()
        st.download_button(
            label="📄 Descargar Manual de usuario",
            data=pdf_bytes,
            file_name="CHRONOFLUX_USER_MANUAL.pdf",
            mime="application/pdf",
            use_container_width=True,
            help="Descarga el manual operativo en formato PDF."
        )
    except FileNotFoundError:
        st.download_button(
            label="📄 Descargar Manual de usuario",
            data=b"Archivo no encontrado",
            file_name="error.txt",
            use_container_width=True,
            disabled=True,
            help="Coloque el archivo CHRONOFLUX_USER_MANUAL.pdf en la raíz."
        )

# ---------------- BANNER DINÁMICO DE RED (PARTICLES.JS) ----------------
banner_html = """
<div id="particles-js" style="position: relative; width: 100%; height: 120px; background-color: #0F172A; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);">
    <div style="position: absolute; top: 50%; left: 40px; transform: translateY(-50%); z-index: 10; color: white;">
        <h1 style="margin:0; font-weight: 800; font-family: 'Inter', sans-serif; font-size: 2.8rem; letter-spacing: 2px;">CHRONOFLUX AI</h1>
    </div>
</div>
<script src="https://cdn.jsdelivr.net/particles.js/2.0.0/particles.min.js"></script>
<script>
    particlesJS("particles-js", {
      "particles": {
        "number": {"value": 80, "density": {"enable": true, "value_area": 800}},
        "color": {"value": "#ffffff"},
