import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import xml.etree.ElementTree as ET
import requests
import io
import re
import math
import os
import numpy as np
from datetime import datetime, timedelta, date, time as dtime

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
if 'ventana_state' not in st.session_state: st.session_state['ventana_state'] = 7
if 'dias_state' not in st.session_state: st.session_state['dias_state'] = ["Lun","Mar","Mié","Jue","Vie"]
if 'clima_real_state' not in st.session_state: st.session_state['clima_real_state'] = True
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
    "01: CFX-VAL-01 Determinista (Control)": {
        "nlp": False, "ml": False, "pr": 100, "ur": 50.0, "ut": 1.0, "temp": 27.5, "hum": 70.0, "jornada": (8, 17), "dias": ["Lun","Mar","Mié","Jue","Vie"],
        "desc": "Baseline determinista. IA desactivada y umbrales inalcanzables. EVB nulo: punto cero para medir desplazamientos."
    },
    "02: CFX-VAL-02 Ciclones (Otoño)": {
        "nlp": True, "ml": True, "pr": 15, "ur": 1.5, "ut": 3.0, "temp": 28.5, "hum": 74.8, "jornada": (8, 17), "dias": ["Lun","Mar","Mié","Jue","Vie"],
        "desc": "Meses críticos Sept-Nov. Pr y Ur bajos: hiper-sensible a lluvias convectivas frecuentes. Alta humedad extiende el Tr."
    },
    "03: CFX-VAL-03 Estiaje (Ventana Seca)": {
        "nlp": True, "ml": True, "pr": 45, "ur": 5.0, "ut": 2.0, "temp": 26.4, "hum": 65.6, "jornada": (8, 17), "dias": ["Lun","Mar","Mié","Jue","Vie"],
        "desc": "Feb-Mar. Pr alto y baja humedad: el modelo reconoce ventanas de oportunidad y no penaliza injustificadamente."
    },
    "04: CFX-VAL-04 OPEX Moderado": {
        "nlp": True, "ml": True, "pr": 25, "ur": 2.5, "ut": 5.5, "temp": 27.8, "hum": 70.0, "jornada": (8, 17), "dias": ["Lun","Mar","Mié","Jue","Vie"],
        "desc": "Protección de costos indirectos. Si la lluvia arruina media jornada, se descarta el día para proteger el OPEX."
    },
    "05: CFX-VAL-05 HEAT Evaporación": {
        "nlp": True, "ml": True, "pr": 20, "ur": 3.5, "ut": 2.5, "temp": 32.5, "hum": 55.0, "jornada": (8, 17), "dias": ["Lun","Mar","Mié","Jue","Vie"],
        "desc": "Sequía y radiación alta. El Random Forest minimiza Tr; la habilitación topológica post-lluvia se acelera."
    },
    "06: CFX-VAL-06 Vaguada (Saturación)": {
        "nlp": True, "ml": True, "pr": 15, "ur": 2.0, "ut": 4.0, "temp": 24.5, "hum": 95.0, "jornada": (8, 17), "dias": ["Lun","Mar","Mié","Jue","Vie"],
        "desc": "Escenario adverso: baja temperatura + 95% humedad anulan la evaporación. La terracería colapsa (Tr > 72h)."
    },
    "07: CFX-VAL-07 Fallo NLP (Ceguera Semántica)": {
        "nlp": False, "ml": True, "pr": 25, "ur": 3.0, "ut": 3.0, "temp": 28.0, "hum": 70.0, "jornada": (8, 17), "dias": ["Lun","Mar","Mié","Jue","Vie"],
        "desc": "Desactiva el Transformer Zero-Shot. El sistema recurre al fallback RegEx; valida el valor de la semántica en el Ic."
    },
    "08: CFX-VAL-08 Fallo PIML (Ceguera Térmica)": {
        "nlp": True, "ml": False, "pr": 25, "ur": 3.0, "ut": 3.0, "temp": 28.0, "hum": 70.0, "jornada": (8, 17), "dias": ["Lun","Mar","Mié","Jue","Vie"],
        "desc": "Desactiva el Random Forest. Tr estático (48h arcillas) ignorando el microclima; mide el aporte de la IA termodinámica."
    },
    "09: CFX-VAL-09 Fast-Tracking 11h (L-D)": {
        "nlp": True, "ml": True, "pr": 20, "ur": 4.0, "ut": 1.5, "temp": 28.2, "hum": 72.0, "jornada": (7, 18), "dias": ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"],
        "desc": "Jornada 11h, Lun-Dom. El impacto pluviométrico se diluye sobre un divisor Hw mayor. Evalúa la absorción por horas extra."
    },
    "10: CFX-VAL-10 Collapse (Worst-Case)": {
        "nlp": True, "ml": True, "pr": 10, "ur": 1.0, "ut": 6.0, "temp": 25.0, "hum": 88.0, "jornada": (8, 17), "dias": ["Lun","Mar","Mié","Jue","Vie"],
        "desc": "Máxima sensibilidad. Cualquier llovizna se registra; con poco remanente operativo se cancela el día. Límite superior de la deriva."
    },
    "11: CFX-VAL-11 Arcilla A-7-6": {
        "nlp": True, "ml": True, "pr": 22, "ur": 2.0, "ut": 4.0, "temp": 27.0, "hum": 70.0, "jornada": (8, 17), "dias": ["Lun","Mar","Mié","Jue","Vie"],
        "desc": "Estratos cohesivos de alta plasticidad (Ic=3.0). El RF computa Tr asintóticamente alto por retención capilar."
    },
    "12: CFX-VAL-12 Granular A-1-a": {
        "nlp": True, "ml": True, "pr": 22, "ur": 5.0, "ut": 2.0, "temp": 27.0, "hum": 70.0, "jornada": (8, 17), "dias": ["Lun","Mar","Mié","Jue","Vie"],
        "desc": "Permeabilidad y flujo gravitacional (Ic=2.0). Tolerancia de lámina alta: restitución rápida del Módulo Resiliente."
    },
    "13: CFX-VAL-13 Depresión (Llovizna Persistente)": {
        "nlp": True, "ml": True, "pr": 10, "ur": 0.5, "ut": 6.5, "temp": 25.0, "hum": 85.0, "jornada": (8, 17), "dias": ["Lun","Mar","Mié","Jue","Vie"],
        "desc": "Baja presión sin inundación pero satura la obra. Ur muy bajo + Ut alto: las trazas constantes paralizan la terracería."
    },
    "14: CFX-VAL-14 Fast-Tracking 11h": {
        "nlp": True, "ml": True, "pr": 20, "ur": 3.0, "ut": 2.0, "temp": 28.2, "hum": 72.0, "jornada": (7, 18), "dias": ["Lun","Mar","Mié","Jue","Vie"],
        "desc": "Ventana operativa extendida (Hw=11h). Un evento de 2h se diluye; verifica el operador de cuantización Q."
    },
    "15: CFX-VAL-15 Isla de Calor (38°C)": {
        "nlp": True, "ml": True, "pr": 20, "ur": 3.5, "ut": 2.5, "temp": 38.0, "hum": 45.0, "jornada": (8, 17), "dias": ["Lun","Mar","Mié","Jue","Vie"],
        "desc": "Sequía extrema. El ML dictamina secado ultrarrápido (Tr→0); los frentes se habilitan casi inmediatamente."
    },
    "16: CFX-VAL-16 Saturación Atmosférica (98%)": {
        "nlp": True, "ml": True, "pr": 20, "ur": 3.5, "ut": 2.5, "temp": 24.0, "hum": 98.0, "jornada": (8, 17), "dias": ["Lun","Mar","Mié","Jue","Vie"],
        "desc": "Niebla densa: el aire no absorbe humedad, se detiene la evaporación. El RF castiga severamente la recuperación."
    },
    "17: CFX-VAL-17 OPEX Severo": {
        "nlp": True, "ml": True, "pr": 18, "ur": 2.0, "ut": 7.0, "temp": 27.5, "hum": 70.0, "jornada": (8, 17), "dias": ["Lun","Mar","Mié","Jue","Vie"],
        "desc": "Frontera financiera. Con Ut=7.0h, una hora de lluvia encarece demasiado; se descartan días con mínimas perturbaciones."
    },
    "18: CFX-VAL-18 Flash Floods (Torrencial)": {
        "nlp": True, "ml": True, "pr": 12, "ur": 15.0, "ut": 1.0, "temp": 28.0, "hum": 75.0, "jornada": (8, 17), "dias": ["Lun","Mar","Mié","Jue","Vie"],
        "desc": "Aísla aguaceros torrenciales (Ur=15mm), ignorando lloviznas. Solo inyecta EVB ante volúmenes masivos de agua."
    },
    "19: CFX-VAL-19 Blind (Referencia Ciega)": {
        "nlp": False, "ml": False, "pr": 25, "ur": 3.0, "ut": 3.0, "temp": 28.0, "hum": 70.0, "jornada": (8, 17), "dias": ["Lun","Mar","Mié","Jue","Vie"],
        "desc": "Apaga semántica y termodinámica. Penalizaciones estáticas: contraste para medir los días que salva la IA."
    },
    "20: CFX-VAL-20 Cisne Negro (Stress Máximo)": {
        "nlp": True, "ml": True, "pr": 8, "ur": 0.1, "ut": 8.0, "temp": 25.0, "hum": 88.0, "jornada": (8, 17), "dias": ["Lun","Mar","Mié","Jue","Vie"],
        "desc": "Tensión máxima: cualquier rocío (0.1mm) paraliza. Fuerza la mutación salvaje de la Ruta Crítica y al Agente Prescriptivo."
    }
}

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
        # AE-03: los presets ahora también fijan los días laborables
        if 'dias' in p:
            st.session_state.dias_state = p['dias']
        # Los presets son ensayos de estrés: usan override manual de temp/humedad
        st.session_state.clima_real_state = False
        
        st.session_state.combo_ubicacion = "Santo Domingo Oeste - Autopista Duarte"
        st.session_state.lat_actual = 18.5743
        st.session_state.lon_actual = -70.1063
        st.session_state.ubicacion_nombre = "Santo Domingo Oeste - Autopista Duarte"

# ==============================================================================
# MÓDULOS DE INTELIGENCIA ARTIFICIAL Y MACHINE LEARNING (CORREGIDO)
# ==============================================================================
try:
    from transformers import pipeline
    from sklearn.ensemble import RandomForestRegressor
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
    """
    PARCHE APLICADO: Generador de datos sintéticos basados en física real.
    Entrena al Random Forest para que devuelva HORAS de secado respondiendo
    correctamente a la temperatura y humedad.
    """
    if not IA_DISPONIBLE: return None
    np.random.seed(42)
    X_train = []
    y_train = []
    
    # Creamos 2000 permutaciones físicas para entrenar a la IA
    for _ in range(2000):
        lluvia = np.random.uniform(0.1, 100.0)
        temp = np.random.uniform(15.0, 45.0)
        hum = np.random.uniform(30.0, 100.0)
        suelo = np.random.choice([1, 2, 3]) 
        
        # Fórmula física real de evaporación 
        evap_rate = max(0.1, (temp / 15.0) * ((100.0 - hum) / 40.0))
        factor_suelo = {1: 1.5, 2: 1.0, 3: 0.5}[suelo] # 1 retiene más agua
        
        tr_horas = (lluvia / evap_rate) * factor_suelo
        
        X_train.append([lluvia, temp, hum, suelo])
        y_train.append(min(96.0, tr_horas)) # Cap máximo de 96 horas
        
    modelo = RandomForestRegressor(n_estimators=50, random_state=42)
    modelo.fit(X_train, y_train)
    return modelo

ml_tr_model = entrenar_modelo_termodinamico()

def calcular_tr_y_ic_dinamico(lluvia_mm, temp_c, humedad_pct, tipo_suelo_ic, usar_ia=True):
    if not usar_ia or not ml_tr_model:
        # Fallback ciego
        if tipo_suelo_ic >= 3.0: return 24.0, tipo_suelo_ic
        elif tipo_suelo_ic >= 2.0: return 12.0, tipo_suelo_ic
        elif tipo_suelo_ic >= 1.5: return 6.0, tipo_suelo_ic
        else: return 0.0, tipo_suelo_ic
        
    suelo_cat = 1 if tipo_suelo_ic >= 3.0 else (2 if tipo_suelo_ic >= 2.0 else 3)
    
    # La IA ahora predice HORAS reales
    tr_horas = ml_tr_model.predict([[lluvia_mm, temp_c, humedad_pct, suelo_cat]])[0]
    
    # Penalización del coeficiente basada en el daño hídrico prolongado
    tr_dias = tr_horas / 24.0
    ic_dinamico = round(tipo_suelo_ic + (tr_dias * 0.5), 2)
    return round(tr_horas, 1), ic_dinamico

def agente_prescriptivo_mitigacion(df_tareas, evb_total):
    """Genera un mini-informe prescriptivo del estado analizado (siempre devuelve contenido)."""
    reporte = []

    # --- Base de datos: solo actividades reales ---
    act = df_tareas[(df_tareas['IsSummary'] == False) & (df_tareas['IsMilestone'] == False)].copy()
    act['_imp'] = pd.to_numeric(act['Días Impacto'], errors='coerce').fillna(0)
    act['_tr']  = pd.to_numeric(act['Tr (Secado/Horas)'], errors='coerce').fillna(0)
    act['_ic']  = pd.to_numeric(act['Ic_Estimado'], errors='coerce').fillna(0)

    n_total = len(act)
    afectadas = act[act['_imp'] > 0]
    n_afect = len(afectadas)
    criticas = act[act['Ruta Crítica'].astype(str) == "Sí"]
    n_crit = len(criticas)
    pct = (n_afect / n_total * 100.0) if n_total > 0 else 0.0

    # --- 1) Resumen ejecutivo del estado ---
    if evb_total <= 0 and n_afect == 0:
        nivel = "🟢 ESTABLE"
    elif evb_total < 5:
        nivel = "🟡 RIESGO MODERADO"
    else:
        nivel = "🔴 RIESGO ALTO"
    reporte.append(
        f"📋 **Informe de Estado — {nivel}**<br>"
        f"El proyecto acumula un retraso climático estimado de **{int(round(evb_total))} días hábiles**. "
        f"Se analizaron **{n_total} actividades**, de las cuales **{n_afect} ({pct:.0f}%)** presentan impacto pluviométrico "
        f"y **{n_crit}** se encuentran sobre la Ruta Crítica estocástica."
    )

    # Estado estable: no hay nada más que prescribir
    if n_afect == 0:
        reporte.append("✅ **Diagnóstico:** El riesgo climático actual es absorbido por las holguras del cronograma. No se requieren medidas de mitigación.")
        return reporte

    # --- 2) Cuello de botella principal (mayor impacto) ---
    peor = afectadas.loc[afectadas['_imp'].idxmax()]
    reporte.append(
        f"🧠 **Cuello de botella principal:** **'{peor['Actividad']}'** concentra el mayor impacto "
        f"({int(peor['_imp'])} días), con un tiempo de secado inferido de **{peor['_tr']:.0f} h** "
        f"y coeficiente de vulnerabilidad Ic={peor['_ic']:.1f}."
    )

    # --- 3) Top de actividades más afectadas ---
    top = afectadas.sort_values('_imp', ascending=False).head(3)
    lineas = "<br>".join(
        f"&nbsp;&nbsp;• **{t['Actividad']}** — {int(t['_imp'])} d "
        f"({'Ruta Crítica' if str(t['Ruta Crítica'])=='Sí' else 'con holgura'})"
        for _, t in top.iterrows()
    )
    reporte.append(f"📌 **Actividades más afectadas:**<br>{lineas}")

    # --- 4) Recomendación logística con verificación de solapamiento (Ec. 6.10) ---
    tierras = afectadas[afectadas['_tr'] >= 12.0]
    refugios = act[act['_ic'] <= 1.0]
    refugio_solapado = None
    if not tierras.empty and not refugios.empty:
        eb_ini = pd.to_datetime(peor.get('Inicio Nuevo'), errors='coerce')
        eb_fin = pd.to_datetime(peor.get('Fin Nuevo'), errors='coerce')
        if pd.notna(eb_ini) and pd.notna(eb_fin):
            for _, ref in refugios.iterrows():
                er_ini = pd.to_datetime(ref.get('Inicio Nuevo'), errors='coerce')
                er_fin = pd.to_datetime(ref.get('Fin Nuevo'), errors='coerce')
                if pd.notna(er_ini) and pd.notna(er_fin) and max(eb_ini, er_ini) <= min(eb_fin, er_fin):
                    refugio_solapado = ref
                    break

    if refugio_solapado is not None:
        reporte.append(
            f"👉 **Estrategia recomendada (Ec. 6.10 — solapamiento confirmado):** Reasignar temporalmente la "
            f"maquinaria del frente bloqueado hacia el nodo refugio estructural **'{refugio_solapado['Actividad']}'** "
            f"(Ic={refugio_solapado['_ic']:.1f}), cuya ventana operativa se solapa con el período de parálisis, "
            f"evitando que los recursos queden inactivos."
        )
    elif not tierras.empty:
        reporte.append(
            "⚠️ **Estrategia recomendada:** No hay frentes estructurales con ventana solapada al período de parálisis. "
            "Se recomienda **reprogramar el inicio** del frente afectado hacia una ventana de menor probabilidad de lluvia "
            "o evaluar la **movilización de recursos** a otro proyecto durante el secado."
        )
    else:
        reporte.append(
            "👉 **Estrategia recomendada:** Los impactos provienen de lluvias de baja persistencia. Se recomienda "
            "**ajustar la secuencia de tareas** para ejecutar las partidas sensibles en las ventanas secas detectadas "
            "y reforzar el drenaje superficial de los frentes activos."
        )

    if n_crit > 0:
        reporte.append(
            f"🚨 **Atención Ruta Crítica:** {n_crit} actividad(es) crítica(s) absorbieron el retraso y empujan la fecha "
            f"de término del proyecto. Prioriza su mitigación: cualquier día ganado en ellas se traduce directamente en "
            f"adelanto del hito final."
        )
    return reporte

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
        
        # ============================================================
        # CORRECCIÓN RAÍZ (Flaw of Averages): se almacena el ARREGLO de
        # valores históricos de lluvia por día-calendario, NO el promedio.
        # Esto permite calcular P(d|Ur) frecuentista real DENTRO de la
        # simulación contra el umbral Ur del usuario (Ec. 5.4.2 de la tesis),
        # y alimentar el suelo con la magnitud de los EVENTOS reales de lluvia.
        # ============================================================
        clima_map = {}
        for dia_mes, grupo in df_daily.groupby('dia_mes'):
            valores = grupo['mm'].astype(float).tolist()           # lluvia de cada año para ese día
            fechas = grupo['fecha_full'].tolist()
            # última fecha histórica en que llovió de forma significativa
            fechas_lluvia = [f for f, v in zip(fechas, valores) if v > 0.5]
            clima_map[dia_mes] = {
                'valores_mm': valores,                              # array histórico (núcleo frecuentista)
                'n_anios': len(valores),
                'probabilidad': float((grupo['mm'] > 0.5).mean()),  # se mantiene para referencia/gráficos
                'mm_promedio': float(grupo['mm'].mean()),           # se mantiene solo para reportes
                # AE-04: temperatura y humedad REALES (ERA5) de ese día-calendario.
                # Permiten alimentar el modelo termodinámico con clima hiperlocal real
                # en lugar de un override global uniforme.
                'temp_dia': float(grupo['temp'].mean()),
                'hum_dia': float(grupo['hum'].mean()),
                'ultima_fecha_lluvia': max(fechas_lluvia) if fechas_lluvia else None
            }
        
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

def extraer_calendario_xml(root, prefix):
    """Lee el calendario base del proyecto MSPDI: días laborables (weekday Python) y feriados."""
    map_daytype = {1:6, 2:0, 3:1, 4:2, 5:3, 6:4, 7:5}  # DayType MSPDI (1=Dom..7=Sab) -> weekday() Py
    cal_uid_node = root.find(prefix+"CalendarUID")
    cal_default = cal_uid_node.text if cal_uid_node is not None else None
    dias_idx = set(); feriados = {}
    cals = root.find(prefix+"Calendars")
    if cals is None: return [0,1,2,3,4], {}, None
    elegido = None
    for cal in cals.findall(prefix+"Calendar"):
        uid = cal.findtext(prefix+"UID")
        if cal_default and uid == cal_default: elegido = cal; break
        if elegido is None and cal.findtext(prefix+"IsBaseCalendar") == "1": elegido = cal
    if elegido is None: elegido = cals.find(prefix+"Calendar")
    if elegido is None: return [0,1,2,3,4], {}, None
    wds = elegido.find(prefix+"WeekDays")
    if wds is not None:
        for wd in wds.findall(prefix+"WeekDay"):
            dt_node = wd.findtext(prefix+"DayType"); working = wd.findtext(prefix+"DayWorking")
            if dt_node:
                if working == "1":
                    py = map_daytype.get(int(dt_node))
                    if py is not None: dias_idx.add(py)
            else:  # excepción embebida (forma antigua)
                tp = wd.find(prefix+"TimePeriod")
                if tp is not None and working == "0":
                    fd = tp.findtext(prefix+"FromDate"); td = tp.findtext(prefix+"ToDate")
                    if fd:
                        d0 = datetime.fromisoformat(fd).date(); d1 = datetime.fromisoformat(td).date() if td else d0
                        cur=d0
                        while cur<=d1: feriados[cur.strftime('%Y-%m-%d')]=True; cur+=timedelta(days=1)
    exc = elegido.find(prefix+"Exceptions")
    if exc is not None:  # excepciones forma nueva
        for e in exc.findall(prefix+"Exception"):
            if e.findtext(prefix+"DayWorking") == "0":
                tp = e.find(prefix+"TimePeriod")
                if tp is not None:
                    fd=tp.findtext(prefix+"FromDate"); td=tp.findtext(prefix+"ToDate")
                    if fd:
                        d0=datetime.fromisoformat(fd).date(); d1=datetime.fromisoformat(td).date() if td else d0
                        cur=d0
                        while cur<=d1: feriados[cur.strftime('%Y-%m-%d')]=True; cur+=timedelta(days=1)
    if not dias_idx: dias_idx={0,1,2,3,4}
    return sorted(dias_idx), feriados, cal_default

def generar_xml_ajustado(raw_bytes, prefix, df_final, hours_per_day):
    """Reescribe Duración/Inicio/Fin de cada tarea en el XML MSPDI original según el resultado
    de CHRONOFLUX, preservando calendarios, dependencias y todo lo demás. Solo se modifican las
    tareas hoja en su duración; resúmenes e hitos solo reciben fechas (Project recalcula su duración)."""
    NS = "http://schemas.microsoft.com/project"
    root = ET.fromstring(raw_bytes)
    by_id = {int(r['ID']): r for _, r in df_final.iterrows()}
    for task in root.iter(prefix+'Task'):
        idtxt = task.findtext(prefix+'ID')
        if idtxt is None: continue
        try: tid = int(idtxt)
        except: continue
        if tid not in by_id: continue
        r = by_id[tid]
        is_sum = (task.findtext(prefix+'Summary') == '1')
        is_mile = (task.findtext(prefix+'Milestone') == '1')
        def setext(tag, val):
            el = task.find(prefix+tag)
            if el is None: el = ET.SubElement(task, prefix+tag)
            el.text = val
        ini = r.get('Inicio Nuevo'); fin = r.get('Fin Nuevo')
        try:
            if ini is not None and not isinstance(ini, float):
                d = ini if hasattr(ini,'year') else datetime.fromisoformat(str(ini)).date()
                setext('Start', datetime.combine(d, dtime(8,0)).strftime('%Y-%m-%dT%H:%M:%S'))
        except: pass
        try:
            if fin is not None and not isinstance(fin, float):
                d = fin if hasattr(fin,'year') else datetime.fromisoformat(str(fin)).date()
                setext('Finish', datetime.combine(d, dtime(17,0)).strftime('%Y-%m-%dT%H:%M:%S'))
        except: pass
        if not is_sum and not is_mile:
            try:
                dnv = float(r.get('Duración Nueva'))
                horas = int(round(dnv*hours_per_day))
                setext('Duration', f"PT{horas}H0M0S")
            except: pass
    ET.register_namespace('', NS)
    # Actualizar la FinishDate del encabezado del proyecto al máximo Fin Nuevo (cosmético;
    # MS Project la recalcula al abrir, pero evita mostrar la fecha vieja).
    try:
        import pandas as _pd
        fins = _pd.to_datetime(df_final['Fin Nuevo'], errors='coerce').dropna()
        if len(fins):
            fd = root.find(prefix+'FinishDate')
            if fd is not None:
                fd.text = _pd.Timestamp(fins.max()).strftime('%Y-%m-%dT17:00:00')
    except Exception:
        pass
    return ET.tostring(root, encoding='UTF-8', xml_declaration=True)

def auditar_xml(file):
    file.seek(0)
    raw = file.read()
    st.session_state['xml_raw'] = raw
    root = ET.fromstring(raw)
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
            pred_links = []
            type_map = {'0':'FF','1':'FS','2':'SF','3':'SS'}
            for link in task.findall(prefix + 'PredecessorLink'):
                p_uid = find_val(link, 'PredecessorUID')
                if p_uid:
                    pid = uid_to_id.get(p_uid, p_uid)
                    preds.append(pid)
                    ltype = type_map.get(find_val(link, 'Type') or '1', 'FS')
                    try: pred_links.append((int(pid), ltype))
                    except: pass
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
                'OrigPreds': orig_preds, 'PredLinks': pred_links, 'Errores': " | ".join(errores) if errores else "OK"
            })
    # Guardar metadatos para la reescritura del XML y el uso del calendario real del proyecto
    st.session_state['xml_prefix'] = prefix
    st.session_state['xml_hpd'] = hours_per_day
    try:
        cd, cf, _ = extraer_calendario_xml(root, prefix)
        st.session_state['cal_dias'] = cd
        st.session_state['cal_feriados'] = cf
    except Exception:
        st.session_state['cal_dias'] = None; st.session_state['cal_feriados'] = {}
    return pd.DataFrame(tareas).sort_values('ID')

# ==============================================================================
# MOTOR CPM ESTOCÁSTICO V5 — CORRECCIONES DE AUDITORÍA LÓGICA APLICADAS
# ==============================================================================

# C-03: Función auxiliar para calcular desplazamiento en días HÁBILES (no calendario)
def contar_dias_habiles_shift(desde, hasta, dias_idx, feriados):
    """Cuenta cuántos días hábiles hay entre 'desde' (exclusive) y 'hasta' (inclusive)."""
    if desde is None or hasta is None or hasta <= desde:
        return 0
    c = desde
    n = 0
    while c < hasta:
        c += timedelta(days=1)
        if es_habil(c, dias_idx, feriados):
            n += 1
    return n

def avanzar_habiles(fecha, n, dias_idx, feriados):
    """Avanza 'n' días hábiles desde 'fecha' (inverso de contar_dias_habiles_shift).
    Con n<=0 devuelve la propia fecha llevada al siguiente día hábil."""
    d = fecha
    if n <= 0:
        while not es_habil(d, dias_idx, feriados): d += timedelta(days=1)
        return d
    c = 0
    while c < n:
        d += timedelta(days=1)
        if es_habil(d, dias_idx, feriados): c += 1
    return d

# ==============================================================================
# VENTANA CLIMATOLÓGICA: agrupa los registros históricos de ±W días alrededor de
# una fecha-calendario para estimar P(d|Ur) sobre una muestra robusta (~N×(2W+1))
# en lugar de la fecha aislada (N=10). Corrige el ruido de muestreo del estimador.
# ==============================================================================
def pool_ventana_climatica(cursor, clima, W):
    pool = []
    for off in range(-W, W + 1):
        kk = (cursor + timedelta(days=off)).strftime('%m-%d')
        h = clima.get(kk)
        if h:
            v = h.get('valores_mm')
            if v:
                pool.extend(v)
    return pool

def simular_cronograma(df, clima, prob_min, mm_min, dias_idx, feriados, reparar, umbral_horas, h_inicio, h_fin, use_nlp, use_ml, temp_global, hum_global, usar_clima_real=False, ventana_dias=7):
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
    fecha_inicio_calculada = {}
    res_temp = {}

    for tid in orden:
        row = G.nodes[tid]['data']
        new_preds = G.nodes[tid]['new_preds']
        note = "Corregido Auto" if (reparar == "Automática" and "Falta Predecesora" in row['Errores']) else row['Errores']
            
        start_dt = pd.to_datetime(row['Start_XML']).date() if pd.notna(row['Start_XML']) else None
        finish_dt = pd.to_datetime(row['Finish_XML']).date() if pd.notna(row['Finish_XML']) else None
        base_dur_float = float(row['Duration_Days'])
        
        # ============================================================
        # CPM TIPO-CONSCIENTE (Opción B): la propagación del retraso depende del
        # tipo de vínculo. FS/FF/SF propagan el retraso del FIN del predecesor;
        # SS propaga el retraso del INICIO. Como es un enfoque de delta sobre el
        # cronograma original de MS Project, los lags y el paralelismo ya vienen
        # incorporados en las fechas base; solo se suma el desfase climático.
        # ============================================================
        pred_links = row['PredLinks'] if isinstance(row.get('PredLinks'), list) else []
        tipados = {pid for pid, _ in pred_links}
        for p in [int(x.strip()) for x in new_preds.split(',') if x.strip().isdigit()]:
            if p not in tipados:
                pred_links = pred_links + [(p, 'FS')]  # predecesora auto-reparada => FS
        max_shift_dias = 0
        if pred_links and start_dt:
            for p, ltype in pred_links:
                if not G.has_node(p): continue
                if ltype == 'SS':
                    ini_base_pred = G.nodes[p]['data']['Start_XML']
                    ini_base_pred = pd.to_datetime(ini_base_pred).date() if pd.notna(ini_base_pred) else None
                    ini_new_pred = fecha_inicio_calculada.get(p)
                    if ini_base_pred and ini_new_pred:
                        shift = contar_dias_habiles_shift(ini_base_pred, ini_new_pred, dias_idx, feriados)
                        if shift > max_shift_dias: max_shift_dias = shift
                else:  # FS / FF / SF -> retraso del fin del predecesor
                    if fecha_fin_calculada.get(p) is not None:
                        fin_base_pred = G.nodes[p]['data']['Finish_XML']
                        fin_base_pred = pd.to_datetime(fin_base_pred).date() if pd.notna(fin_base_pred) else None
                        if fin_base_pred:
                            shift = contar_dias_habiles_shift(fin_base_pred, fecha_fin_calculada[p], dias_idx, feriados)
                            if shift > max_shift_dias: max_shift_dias = shift

        new_start = start_dt
        if max_shift_dias > 0 and start_dt:
            new_start = avanzar_habiles(start_dt, max_shift_dias, dias_idx, feriados)
        if new_start: fecha_inicio_calculada[tid] = new_start

        new_finish = finish_dt
        new_dur_float = base_dur_float
        
        stats_prob = 0.0; prob_acumulada = 0.0; dias_evaluados = 0; prob_pico = 0.0
        stats_mm = 0; rain_total = 0.0; retraso_teorico_dias = 0.0; last_rain_date = None

        ic_base = calcular_ic_ia(row['Name'], use_nlp)
        tr_horas_max = 0.0
        ic_dinamico_max = ic_base
        
        if not row['IsSummary'] and not row['IsMilestone'] and new_start:
            work_needed = math.ceil(base_dur_float) if base_dur_float > 0 else 1
            work_done = 0; cursor = new_start
            
            # --- MOTOR ESTOCÁSTICO V6: DEUDA DE SECADO MULTI-DÍA ---
            # El Tiempo de Recuperación (Tr) ya no es un interruptor binario: se reparte
            # como horas de inoperatividad que se consumen jornada a jornada (Ec. 5.5 + 5.9).
            lluvia_acumulada_terreno = 0.0       # humedad del suelo (mm equivalentes)
            deuda_secado_horas = 0.0             # horas de inoperatividad pendientes (recuperación)
            prob_vigente = 0.0                   # P(d|Ur) del evento que originó la deuda activa
            ic_vigente = 1.0                     # Q(Ic) severidad vigente (NLP·ML) — Ec. 5.9
            horas_jornada = float(h_fin - h_inicio) if h_fin > h_inicio else 8.0

            while work_done < work_needed:
                if es_habil(cursor, dias_idx, feriados):
                    k = cursor.strftime('%m-%d')
                    if k in clima:
                        h = clima[k]

                        # ============================================================
                        # PROBABILIDAD FRECUENTISTA SIMPLE  P(d) = n/N  (Ec. 5.4.2)
                        # n = años en que LLOVIÓ en esa fecha (ventana), N = total de años.
                        # Pr es un umbral sobre ESTA probabilidad (escala real 0-100%).
                        # El umbral de intensidad Ur se aplica POR SEPARADO sobre la
                        # magnitud del evento; NO se mezcla dentro de la probabilidad.
                        # ============================================================
                        if ventana_dias and ventana_dias > 0:
                            muestra = pool_ventana_climatica(cursor, clima, ventana_dias)
                        else:
                            muestra = h.get('valores_mm', None)

                        RAIN_REF = 1.0   # mm: define "llovió ese día" (traza significativa)
                        if muestra:
                            n = len(muestra)
                            dias_lluvia = [v for v in muestra if v >= RAIN_REF]
                            prob_dia = len(dias_lluvia) / n if n > 0 else 0.0          # P(d) = n/N simple
                            mm_evento = (sum(dias_lluvia) / len(dias_lluvia)) if dias_lluvia else 0.0  # magnitud típica
                        else:
                            prob_dia = h.get('probabilidad', 0.0)
                            mm_evento = h.get('mm_promedio', 0.0)

                        # ============================================================
                        # AE-04: fuente termodinámica (ERA5 real por defecto / override).
                        # ============================================================
                        if usar_clima_real:
                            temp_d = h.get('temp_dia', temp_global)
                            hum_d = h.get('hum_dia', hum_global)
                        else:
                            temp_d = temp_global
                            hum_d = hum_global

                        rain_total += h.get('mm_promedio', 0.0)
                        prob_acumulada += prob_dia
                        prob_pico = max(prob_pico, prob_dia)   # probabilidad representativa (pico)
                        dias_evaluados += 1

                        tasa_evaporacion = max(0.1, (temp_d / 10.0) * ((100.0 - hum_d) / 20.0))

                        # ============================================================
                        # GATE 1 (Pr): el día es de riesgo si llueve con frecuencia >= Pr.
                        # GATE 2 (Ur): además, la lluvia típica debe superar Ur mm para
                        #              detener faenas (lloviznas por debajo no impactan).
                        # ============================================================
                        if prob_dia >= prob_min and mm_evento >= mm_min:
                            lluvia_acumulada_terreno = max(0.0, lluvia_acumulada_terreno + mm_evento - tasa_evaporacion)
                            stats_mm = max(stats_mm, mm_evento)
                            if h['ultima_fecha_lluvia']: last_rain_date = h['ultima_fecha_lluvia'].date()

                            tr_horas, ic_dinamico = calcular_tr_y_ic_dinamico(lluvia_acumulada_terreno, temp_d, hum_d, ic_base, use_ml)
                            tr_horas_max = max(tr_horas_max, tr_horas)
                            ic_dinamico_max = max(ic_dinamico_max, ic_dinamico)

                            # La recuperación se suma a la deuda (secado solapado + lluvia activa).
                            horas_lluvia = mm_evento / 5.0          # intensidad de referencia 5 mm/h
                            deuda_secado_horas = max(deuda_secado_horas, tr_horas) + horas_lluvia
                            prob_vigente = prob_dia
                            # Q(Ic): severidad constructiva. El NLP fija ic_base (material) y el ML
                            # fija tr (que alimenta ic_dinamico). Este factor reintroduce la Ec. 5.9
                            # EVB = Σ P · Q(Ic), haciendo que AMBAS capas (NLP y ML) afecten el retraso.
                            ic_vigente = ic_dinamico
                        else:
                            lluvia_acumulada_terreno = max(0.0, lluvia_acumulada_terreno - tasa_evaporacion)

                        # ============================================================
                        # AE-01: PÉRDIDA FRACCIONAL CONTINUA DE LA JORNADA
                        # Se consume la jornada de hoy contra la deuda de secado. La fracción
                        # perdida es proporcional a las horas no productivas (Tr + lluvia),
                        # diluida por la duración de la jornada (Hw) — habilita el fast-tracking.
                        # ============================================================
                        if deuda_secado_horas > 1e-6:
                            horas_perdidas_hoy = min(horas_jornada, deuda_secado_horas)
                            # AE-01 (Ut/Hw_min como palanca OPEX monótona): Hw_min reduce la
                            # "ventana útil" que se necesita para que la jornada sea rentable.
                            # La fracción perdida se mide contra (jornada − Hw_min): cuanto mayor
                            # Hw_min, menor la ventana y mayor el impacto de una misma perturbación.
                            # Con Hw_min alto, hasta lluvias mínimas descartan el día (caso OPEX).
                            ventana_util = max(0.5, horas_jornada - umbral_horas)
                            fraccion_perdida = min(1.0, horas_perdidas_hoy / ventana_util)
                            # EVB = Σ P · Q(Ic) (Ec. 5.9): el impacto se pondera por la probabilidad
                            # frecuentista Y por la severidad constructiva Q(Ic). ic_vigente integra
                            # el material (NLP) y la recuperación tr (ML), así ambas capas son medibles.
                            retraso_teorico_dias += prob_vigente * fraccion_perdida * ic_vigente
                            deuda_secado_horas = max(0.0, deuda_secado_horas - horas_jornada)
                        # =========================================================

                work_done += 1 
                cursor += timedelta(days=1)
                
            # Se reporta la probabilidad REPRESENTATIVA (pico de la ventana) en lugar del
            # promedio diluido por toda la tarea, que enmascaraba los días de mayor riesgo.
            stats_prob = prob_pico if dias_evaluados > 0 else 0
            stats_prob_media = (prob_acumulada / dias_evaluados) if dias_evaluados > 0 else 0
                
            nota_cuantizacion = ""
            total_cuantizado = base_dur_float
            if retraso_teorico_dias > 0:
                total_cuantizado = base_dur_float + math.ceil(retraso_teorico_dias)
                retraso_cuantizado = total_cuantizado - base_dur_float
                if retraso_cuantizado != round(retraso_teorico_dias, 2):
                    nota_cuantizacion = f" (Q={round(retraso_cuantizado, 2)}d)"
            else:
                retraso_cuantizado = 0.0

            if note == "OK" and retraso_cuantizado > 0:
                note = f"Impacto Clima{nota_cuantizacion} [Ic={ic_dinamico_max}]"
            elif note != "OK" and retraso_cuantizado > 0:
                note += f" | Impacto Clima{nota_cuantizacion} [Ic={ic_dinamico_max}]"
            
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
            'Tr (Secado/Horas)': round(tr_horas_max, 1), 'Ic_Estimado': round(ic_dinamico_max, 2),
            'Pred. Orig': row['OrigPreds'], 'Pred. Nueva': new_preds,
            'Prob. Lluvia': f"{stats_prob:.0%}" if stats_prob > 0 else "-", 'mm Lluvia Max': round(stats_mm, 1) if stats_mm > 0 else "-",
            'Lluvia Total Acum (mm)': round(rain_total, 1), 'Fecha Última Lluvia': last_rain_date if last_rain_date else "-",
            'Días Impacto': redondear_duracion(new_dur_float) - redondear_duracion(base_dur_float), 'Estado': note,
            'IsRain': ((redondear_duracion(new_dur_float) - redondear_duracion(base_dur_float)) > 0), 'IsLogic': (new_preds != row['OrigPreds']) 
        }

    valid_efs = [data['EF'] for n, data in G.nodes(data=True) if data.get('EF') is not None]
    max_project_ef = max(valid_efs) if valid_efs else None

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
        inicio_nuevo = res_temp[tid].get('Inicio Nuevo')
        inicio_base = res_temp[tid].get('Inicio Base')
        # C-04 CORRECCIÓN: distinguir "Mutada por lluvia directa" vs "Empujada por cascada"
        fue_empujada_sin_lluvia = (
            tf_days <= 0 and
            impact == 0 and
            inicio_nuevo is not None and
            inicio_base is not None and
            inicio_nuevo > inicio_base
        )
        if fue_empujada_sin_lluvia:
            res_temp[tid]['Nivel Riesgo'] = "Crítico (Empujada)"
        elif tf_days <= 0 and impact > 0:
            res_temp[tid]['Nivel Riesgo'] = "Crítico (Mutada)"
        elif impact > 2:
            res_temp[tid]['Nivel Riesgo'] = "Alto"
        else:
            res_temp[tid]['Nivel Riesgo'] = "Normal"

    df_res = pd.DataFrame(list(res_temp.values())).sort_values('ID')
    df_res['Holgura (Días)'] = df_res['Holgura (Días)'].astype(object)
    df_res['Tr (Secado/Horas)'] = df_res['Tr (Secado/Horas)'].astype(object)
    df_res['Duración Nueva'] = df_res['Duración Nueva'].astype(object)
    df_res['Días Impacto'] = df_res['Días Impacto'].astype(object)
    df_res['Nivel Riesgo'] = df_res['Nivel Riesgo'].astype(object)

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
                # Las tareas RESUMEN no llevan duración pegable: MS Project la deriva
                # automáticamente de sus hijas. Se conservan Inicio/Fin Nuevo (roll-up
                # correcto) solo como referencia, pero la Duración Nueva y los Días Impacto
                # se dejan en blanco para evitar desfases al copiar/pegar.
                df_res.at[i, 'Duración Nueva'] = "-"
                df_res.at[i, 'Días Impacto'] = "-"
                df_res.at[i, 'Nivel Riesgo'] = "Resumen (auto)"
            else:
                df_res.at[i, 'Duración Nueva'] = "-"; df_res.at[i, 'Días Impacto'] = "-"; df_res.at[i, 'Nivel Riesgo'] = "Resumen (auto)"
                
            df_res.at[i, 'Prob. Lluvia'] = "-"; df_res.at[i, 'mm Lluvia Max'] = "-"
            df_res.at[i, 'Holgura (Días)'] = "-"; df_res.at[i, 'Ruta Crítica'] = "-"; df_res.at[i, 'Tr (Secado/Horas)'] = "-"
            
    df_res['ID'] = pd.to_numeric(df_res['ID'], errors='coerce')
    return df_res.sort_values('ID').reset_index(drop=True)

# ==============================================================================
# CONFIGURACIÓN Y ESTILO (UI/UX MODERN SAAS)
# ==============================================================================
st.set_page_config(page_title="CHRONOFLUX AI", layout="wide", page_icon="⚡")

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
    dias_sel = st.multiselect("Seleccionar:", ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"], key='dias_state')
    mapa_d = {"Lun":0,"Mar":1,"Mié":2,"Jue":3,"Vie":4,"Sáb":5,"Dom":6}
    dias_idx = [mapa_d[d] for d in dias_sel]
    
    st.markdown("---")
    st.header("🧠 Capa Cognitiva e Inteligencia Artificial")
    activar_nlp = st.toggle("Procesamiento de Lenguaje Natural (NLP)", key='nlp_state')
    activar_ml = st.toggle("Motor Random Forest (Tiempo Secado Tr)", key='ml_state')
    activar_ag = st.toggle("Agente Prescriptivo (Mitigación)", key='ag_state')
    
    st.markdown("---")
    st.subheader("🌡️ Termodinámica (Inferencia Continua)")
    usar_clima_real = st.toggle(
        "Usar clima real ERA5 (hiperlocal)", key='clima_real_state',
        help=("Activado: temperatura y humedad se toman de la serie histórica ERA5 de la "
              "coordenada, día a día (modo producción, fiel a la tesis). "
              "Desactivado: se usan los valores manuales de abajo como escenario de estrés "
              "(modo usado por los presets de validación).")
    )
    temp_global = st.slider("Temperatura Ambiente (°C) — escenario manual", 15.0, 45.0, step=0.5, key='temp_state',
                            disabled=usar_clima_real)
    hum_global = st.slider("Humedad Relativa (%) — escenario manual", 30.0, 100.0, step=1.0, key='hum_state',
                           disabled=usar_clima_real)

    st.markdown("<br><br>", unsafe_allow_html=True)
    try:
        with open("CHRONOFLUX_USER_MANUAL.pdf", "rb") as pdf_file:
            pdf_bytes = pdf_file.read()
        st.download_button(label="📄 Descargar Manual", data=pdf_bytes, file_name="CHRONOFLUX_USER_MANUAL.pdf", mime="application/pdf", use_container_width=True)
    except FileNotFoundError:
        st.download_button(label="📄 Descargar Manual", data=b"", file_name="error.txt", use_container_width=True, disabled=True)

# ---------------- BANNER DINÁMICO ----------------
banner_html = """
<div id="particles-js" style="position: relative; width: 100%; height: 120px; background-color: #0F172A; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);">
    <div style="position: absolute; top: 50%; left: 40px; transform: translateY(-50%); z-index: 10; color: white;">
        <h1 style="margin:0; font-weight: 800; font-family: 'Inter', sans-serif; font-size: 2.8rem; letter-spacing: 2px;">CHRONOFLUX AI</h1>
    </div>
</div>
<script src="https://cdn.jsdelivr.net/particles.js/2.0.0/particles.min.js"></script>
<script>
    particlesJS("particles-js", {
      "particles": {"number": {"value": 80}, "color": {"value": "#ffffff"}, "opacity": {"value": 0.3}, "size": {"value": 3}, "line_linked": {"enable": true, "color": "#38BDF8"}, "move": {"enable": true, "speed": 1.5}}
    });
</script>
"""

col_logo, col_banner = st.columns([1, 6], gap="medium")
with col_logo:
    st.markdown("<br>", unsafe_allow_html=True)
    try: st.image("logo_chronoflux.png", use_container_width=True)
    except: st.empty()
with col_banner:
    components.html(banner_html, height=135)

# ==============================================================================
# GEOLOCALIZACIÓN Y MAPA 
# ==============================================================================
def actualizar_desde_dropdown():
    coords = COORDENADAS_RD.get(st.session_state.combo_ubicacion, (18.4861, -69.9312))
    st.session_state['lat_actual'] = coords[0]; st.session_state['lon_actual'] = coords[1]
    st.session_state['ubicacion_nombre'] = st.session_state.combo_ubicacion

col_loc_1, col_loc_2 = st.columns([2, 1])

with col_loc_1:
    st.selectbox("📍 Buscar Ubicación de Proyecto:", sorted(list(COORDENADAS_RD.keys())), key='combo_ubicacion', on_change=actualizar_desde_dropdown)
    st.markdown(f"**Coordenadas de Análisis:** `Latitud: {st.session_state['lat_actual']:.6f}, Longitud: {st.session_state['lon_actual']:.6f}`")

with col_loc_2:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("✍️ Ingreso Manual de Coordenadas"):
        man_lat = st.number_input("Latitud", value=st.session_state['lat_actual'], format="%.6f")
        man_lon = st.number_input("Longitud", value=st.session_state['lon_actual'], format="%.6f")
        if st.button("Aplicar Coordenadas Manuales", type="secondary"):
            st.session_state['lat_actual'] = man_lat
            st.session_state['lon_actual'] = man_lon
            st.session_state['ubicacion_nombre'] = f"Coordenada Manual: {man_lat:.6f}, {man_lon:.6f}"
            st.rerun()

m = folium.Map(location=[st.session_state['lat_actual'], st.session_state['lon_actual']], zoom_start=12)
m.add_child(folium.LatLngPopup()) 
folium.Marker([st.session_state['lat_actual'], st.session_state['lon_actual']], popup=st.session_state['ubicacion_nombre'], icon=folium.Icon(color='red', icon='info-sign')).add_to(m)
map_data = st_folium(m, height=450, use_container_width=True, key="mapa_folium")

st.markdown("---")

# ==============================================================================
# GRÁFICA CLIMÁTICA Y RADAR
# ==============================================================================
st.subheader(f"🌦️ Comportamiento Climático Histórico ({st.session_state['ubicacion_nombre']})")
with st.spinner("Descargando micro-clima..."):
    df_g, clima, orden = obtener_clima_horario_laboral(st.session_state['lat_actual'], st.session_state['lon_actual'], h_inicio, h_fin)
    if df_g is not None:
        tab_precip, tab_temp, tab_hum = st.tabs(["🌧️ Lluvia (mm)", "🌡️ Temperatura (°C)", "💧 Humedad (%)"])
        with tab_precip:
            fig_clima = px.bar(df_g, x='Mes', y='mm', text='mm', color='mm', color_continuous_scale=px.colors.sequential.Blues, hover_data={'prob_lluvia': ':.1%'})
            fig_clima.update_traces(texttemplate='%{text:.1f}', textposition='outside')
            fig_clima.update_layout(coloraxis_showscale=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=400)
            st.plotly_chart(fig_clima, use_container_width=True)
            
        with tab_temp:
            fig_temp = px.bar(df_g, x='Mes', y='temp', text='temp', color='temp', color_continuous_scale=px.colors.sequential.Oranges)
            fig_temp.update_traces(texttemplate='%{text:.1f}°', textposition='outside')
            fig_temp.update_layout(coloraxis_showscale=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=400)
            st.plotly_chart(fig_temp, use_container_width=True)
            
        with tab_hum:
            fig_hum = px.bar(df_g, x='Mes', y='hum', text='hum', color='hum', color_continuous_scale=px.colors.sequential.Teal)
            fig_hum.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig_hum.update_layout(coloraxis_showscale=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', yaxis=dict(range=[0, 100]), height=400)
            st.plotly_chart(fig_hum, use_container_width=True)

st.markdown("---")
st.subheader(f"📡 Radar Satelital en Tiempo Real ({st.session_state['ubicacion_nombre']})")
windy_html = f"""<iframe width="100%" height="450" src="https://embed.windy.com/embed.html?type=map&location=coordinates&metricRain=mm&metricTemp=°C&metricWind=km/h&zoom=9&overlay=rain&product=ecmwf&level=surface&lat={st.session_state['lat_actual']}&lon={st.session_state['lon_actual']}" frameborder="0" style="border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);"></iframe>"""
components.html(windy_html, height=450)
st.markdown("---")

# ==============================================================================
# CARGA DE XML Y EJECUCIÓN DEL MOTOR
# ==============================================================================
uploaded = st.file_uploader("📂 Paso Final: Cargar Cronograma XML (MS Project)", type=['xml'])

if uploaded is not None and st.session_state.get('last_uploaded') != uploaded.name:
    st.session_state['simulacion_activa'] = False
    st.session_state['resultados_finales'] = None
    st.session_state['last_uploaded'] = uploaded.name

if uploaded:
    uploaded.seek(0)
    df_aud = auditar_xml(uploaded)
    errores = df_aud[(df_aud['Errores'] != 'OK')]
    
    if not errores.empty:
        st.warning(f"⚠️ {len(errores)} Tareas con problemas lógicos topológicos.")
        decision = st.radio("Acción de Auditoría:", ["Reparar Automáticamente (Recomendado)", "Descargar Errores (Excel)", "Ignorar"], horizontal=True)
        if decision == "Descargar Errores (Excel)":
            b = io.BytesIO()
            with pd.ExcelWriter(b) as w: errores.to_excel(w, index=False)
            st.download_button("Descargar Archivo de Errores", b.getvalue(), "Errores.xlsx")
            st.session_state['audit_decision'] = None
        elif decision == "Reparar Automáticamente (Recomendado)": st.session_state['audit_decision'] = "Automática"
        else: st.session_state['audit_decision'] = "Ignorar"
    else:
        st.success("✅ Estructura Lógica Perfecta")
        st.session_state['audit_decision'] = "OK"

    if st.session_state['audit_decision']:
        st.markdown("### 🚀 Simulación de Ruta Crítica Estocástica")

        # --- Calendario del proyecto (leído del XML) ---
        cal_dias_xml = st.session_state.get('cal_dias')
        usar_cal_xml = False
        if cal_dias_xml:
            nombres = {0:"Lun",1:"Mar",2:"Mié",3:"Jue",4:"Vie",5:"Sáb",6:"Dom"}
            dias_txt = ", ".join(nombres[d] for d in cal_dias_xml)
            n_fer = len(st.session_state.get('cal_feriados', {}))
            usar_cal_xml = st.toggle(
                "📅 Usar el calendario del proyecto (XML)", value=True, key='usar_cal_xml_state',
                help="Activado: el motor cuenta los días hábiles con el calendario embebido en tu XML de MS Project "
                     "(mismos días laborables y feriados). Así las fechas del XML ajustado coinciden con las de Project. "
                     "Desactivado: usa los días laborables seleccionados manualmente en la barra lateral.")
            if usar_cal_xml:
                st.info(f"Calendario del proyecto detectado → días laborables: **{dias_txt}**  ·  feriados/excepciones: **{n_fer}**")
        
        c_p, c_m, c_u = st.columns(3)
        prob = c_p.slider("Probabilidad de Lluvia (%) — Pr", 0, 100, key='pr_state',
                          help="Frecuencia histórica P(d)=n/N: %% de años en que llovió en esa fecha (ventana). Solo se evalúan días donde llueve al menos este %% de los años.") / 100.0
        mm = c_m.slider("Intensidad mínima (mm/día) — Ur", 0.0, 50.0, step=0.5, key='ur_state',
                        help="La lluvia típica del día debe superar estos mm para detener faenas. Lloviznas por debajo de Ur no generan impacto. Es un filtro SEPARADO de la probabilidad.")
        umbral_horas = c_u.slider(
            "Horas mínimas de jornada viable — Hw_min",
            1.0, 8.0, step=0.5, key='ut_state',
            help=(
                "Solo actúa en días que YA son de riesgo (pasaron Pr y Ur). Si tras lluvia + secado "
                "quedan menos horas productivas que este valor, la jornada se pierde completa."
            )
        )
        ventana_dias = 0  # Pr = n/N puro por fecha-calendario (Ec. 5.4.2 de la tesis, sin suavizado)
        
        if st.button("Ejecutar Cálculo Topológico e Inferencia IA", type="primary", use_container_width=True):
            with st.spinner("Procesando motor estocástico y modelos cognitivos termodinámicos..."):
                # Override del calendario con el del proyecto (XML) para que las fechas coincidan en Project
                dias_calc = dias_idx; feriados_calc = feriados_dict
                if usar_cal_xml and cal_dias_xml:
                    dias_calc = cal_dias_xml
                    feriados_calc = {**feriados_dict, **st.session_state.get('cal_feriados', {})}
                final = simular_cronograma(df_aud, clima, prob, mm, dias_calc, feriados_calc, st.session_state['audit_decision'], umbral_horas, h_inicio, h_fin, activar_nlp, activar_ml, temp_global, hum_global, usar_clima_real, ventana_dias)
                st.session_state['resultados_finales'] = final
                st.session_state['simulacion_activa'] = True
                
        if st.session_state['simulacion_activa'] and st.session_state['resultados_finales'] is not None:
            final = st.session_state['resultados_finales']
            act_impactadas = final[final['IsRain'] == True]
            count_impact = len(act_impactadas)
            
            tareas_evaluables = final[final['IsSummary'] == False]
            try:
                fin_base_max = pd.to_datetime(tareas_evaluables['Fin Base'].dropna()).max()
                fin_nuevo_max = pd.to_datetime(tareas_evaluables['Fin Nuevo'].dropna()).max()
                retraso_total_proyecto = (fin_nuevo_max - fin_base_max).days if pd.notna(fin_nuevo_max) and pd.notna(fin_base_max) else 0
            except: retraso_total_proyecto = 0
            
            st.markdown("### 📊 Panel de Resultados Gerenciales")
            st.markdown(f"""
            <div class="kpi-container">
                <div class="kpi-box">
                    <div class="kpi-title">Actividades Afectadas</div>
                    <div class="kpi-value">{count_impact} <span>/ {len(tareas_evaluables)} totales</span></div>
                </div>
                <div class="kpi-box">
                    <div class="kpi-title">Retraso del Proyecto</div>
                    <div class="kpi-value {'danger' if retraso_total_proyecto > 0 else ''}">+{max(0, retraso_total_proyecto)} <span>Días Calendario</span></div>
                </div>
                <div class="kpi-box">
                    <div class="kpi-title">Fecha Final Proyectada</div>
                    <div class="kpi-value" style="font-size: 2rem;">{fin_nuevo_max.strftime("%d %b %Y") if pd.notna(fin_nuevo_max) else 'N/A'}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if activar_ag:
                st.markdown("### 🤖 Agente Prescriptivo de Mitigación (IA)")
                consejos = agente_prescriptivo_mitigacion(final, retraso_total_proyecto)
                for consejo in consejos:
                    st.markdown(f'<div class="ia-card">{consejo}</div>', unsafe_allow_html=True)
            
            act_reales = final[(final['IsSummary'] == False) & (final['IsMilestone'] == False)]
            
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Gantt Comparativo", "📈 Curva de Avance Físico Acumulado", "📅 Riesgo Mensual", "⚠️ Tabla de Impactos"])
            
            with tab1:
                df_gantt = act_reales.copy()
                df_gantt['Inicio Nuevo'] = pd.to_datetime(df_gantt['Inicio Nuevo'])
                df_gantt['Fin Nuevo'] = pd.to_datetime(df_gantt['Fin Nuevo'])
                if not df_gantt.empty:
                    fig_gantt = px.timeline(df_gantt.sort_values('Inicio Nuevo'), x_start="Inicio Nuevo", x_end="Fin Nuevo", y="Actividad", color="Días Impacto", color_continuous_scale=px.colors.sequential.Tealgrn)
                    fig_gantt.update_yaxes(autorange="reversed")
                    fig_gantt.update_layout(height=600, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', template='plotly_white')
                    st.plotly_chart(fig_gantt, use_container_width=True)
            
            with tab2:
                df_base = act_reales[['Fin Base']].copy().rename(columns={'Fin Base':'Fecha'}).dropna()
                df_base['Tipo'] = 'Base'
                df_new = act_reales[['Fin Nuevo']].copy().rename(columns={'Fin Nuevo':'Fecha'}).dropna()
                df_new['Tipo'] = 'Sugerido'
                df_s = pd.concat([df_base, df_new])
                df_s['Count'] = 1
                df_s['Fecha'] = pd.to_datetime(df_s['Fecha'])
                df_s = df_s.sort_values('Fecha')
                df_s['Acumulado'] = df_s.groupby('Tipo')['Count'].cumsum()
                
                fig_s = px.line(df_s, x='Fecha', y='Acumulado', color='Tipo', color_discrete_map={'Base': '#94A3B8', 'Sugerido': '#AF1E2D'}, markers=True, template='plotly_white', line_shape='spline')
                fig_s.update_traces(line=dict(smoothing=1.3))
                fig_s.update_layout(yaxis_title="Tareas Terminadas (Acumulado)", xaxis_title="Fecha de Finalización")
                st.plotly_chart(fig_s, use_container_width=True)
                st.caption(
                    "📌 **Nota metodológica:** Esta gráfica representa el avance físico acumulado de tareas "
                    "(cantidad de actividades terminadas en el tiempo), no una Curva S de probabilidad acumulada "
                    "del tipo Monte Carlo. La separación entre ambas curvas visualiza el retraso cronológico "
                    "inducido por los eventos pluviométricos sobre la red topológica."
                )
                
            with tab3:
                df_hist = final[final['IsRain']==True].copy()
                if not df_hist.empty:
                    df_hist['Mes'] = pd.to_datetime(df_hist['Inicio Nuevo']).dt.month_name()
                    counts_mes = df_hist['Mes'].value_counts().reset_index()
                    counts_mes.columns = ['Mes', 'Qty']
                    fig_riesgo = px.bar(counts_mes, x='Mes', y='Qty', text='Qty', color_discrete_sequence=['#0EA5E9'], template='plotly_white')
                    st.plotly_chart(fig_riesgo, use_container_width=True)
                
            with tab4:
                df_pareto = final[final['IsSummary'] == False].sort_values('Días Impacto', ascending=False)
                gb = GridOptionsBuilder.from_dataframe(df_pareto[['ID', 'WBS', 'Actividad', 'Días Impacto', 'Tr (Secado/Horas)', 'Holgura (Días)', 'Ruta Crítica', 'Estado']])
                gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
                gridOptions = gb.build()
                AgGrid(df_pareto[['ID', 'WBS', 'Actividad', 'Días Impacto', 'Tr (Secado/Horas)', 'Holgura (Días)', 'Ruta Crítica', 'Estado']], gridOptions=gridOptions, theme='alpine')

            b_out = io.BytesIO()
            p_name = st.session_state.get('project_name', 'Proyecto')
            safe_name = "".join([c for c in p_name if c.isalnum() or c in (' ', '_')]).strip()
            
            columnas_exportar = ['ID', 'WBS', 'Actividad', 'Duración Base', 'Inicio Base', 'Fin Base', 'Duración Nueva', 'Inicio Nuevo', 'Fin Nuevo', 'Tr (Secado/Horas)', 'Pred. Orig', 'Pred. Nueva', 'Prob. Lluvia', 'mm Lluvia Max', 'Lluvia Total Acum (mm)', 'Fecha Última Lluvia', 'Días Impacto', 'Nivel Riesgo', 'Estado', 'Holgura (Días)', 'Ruta Crítica']
            cols_exist = [c for c in columnas_exportar if c in final.columns]
            df_export = final[cols_exist].copy()
            # ORDEN POR ID (orden original de MS Project) para que la columna de
            # 'Duración Nueva' se pueda copiar y pegar alineada fila a fila con el Project.
            if 'ID' in df_export.columns:
                df_export['_idnum'] = pd.to_numeric(df_export['ID'], errors='coerce')
                df_export = df_export.sort_values('_idnum').drop(columns=['_idnum'])

            with pd.ExcelWriter(b_out, engine='xlsxwriter') as w:
                df_export.to_excel(w, index=False, sheet_name="Reporte", startrow=2)
                wb = w.book; ws = w.sheets['Reporte']
                ncol = len(cols_exist)

                # --- Formatos ---
                fmt_title = wb.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#1E293B', 'font_color': 'white', 'font_size': 13, 'border': 1})
                fmt_sub   = wb.add_format({'italic': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#334155', 'font_color': '#E2E8F0', 'font_size': 9})
                fmt_head  = wb.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#0F172A', 'font_color': 'white', 'border': 1, 'text_wrap': True})
                # Semáforo (relleno por fila según severidad)
                rojo   = wb.add_format({'bg_color': '#F8B4B4', 'font_color': '#7F1D1D'})   # crítico
                naranja= wb.add_format({'bg_color': '#FDE2B4', 'font_color': '#7C2D12'})   # alto
                verde  = wb.add_format({'bg_color': '#BBF7D0', 'font_color': '#14532D'})   # normal/sin impacto
                # Variantes con formato SHORT DATE (num_format 14 = fecha corta del sistema)
                rojo_f   = wb.add_format({'bg_color': '#F8B4B4', 'font_color': '#7F1D1D', 'num_format': 14, 'align': 'center'})
                naranja_f= wb.add_format({'bg_color': '#FDE2B4', 'font_color': '#7C2D12', 'num_format': 14, 'align': 'center'})
                verde_f  = wb.add_format({'bg_color': '#BBF7D0', 'font_color': '#14532D', 'num_format': 14, 'align': 'center'})
                gris     = wb.add_format({'bg_color': '#E5E7EB', 'font_color': '#374151', 'italic': True})
                gris_f   = wb.add_format({'bg_color': '#E5E7EB', 'font_color': '#374151', 'italic': True, 'num_format': 14, 'align': 'center'})
                fmt_fecha_de = {id(rojo): rojo_f, id(naranja): naranja_f, id(verde): verde_f, id(gris): gris_f}
                cols_fecha = {'Inicio Base', 'Fin Base', 'Inicio Nuevo', 'Fin Nuevo', 'Fecha Última Lluvia'}
                fmt_celda = wb.add_format({'border': 1})

                # Título y subtítulo
                ws.merge_range(0, 0, 0, ncol-1, f"REPORTE CLIMÁTICO: {safe_name} | {st.session_state['ubicacion_nombre']}", fmt_title)
                ws.merge_range(1, 0, 1, ncol-1, "Orden por ID (igual que MS Project).  Semáforo: \u25CF Rojo = Ruta Crítica/Crítico  \u25CF Naranja = Alto  \u25CF Verde = Normal.  Resúmenes: duración la calcula MS Project.", fmt_sub)

                # Encabezados (fila 2)
                for j, c in enumerate(cols_exist):
                    ws.write(2, j, c, fmt_head)

                # Índices de columnas clave
                idx_riesgo = cols_exist.index('Nivel Riesgo') if 'Nivel Riesgo' in cols_exist else None
                idx_rc     = cols_exist.index('Ruta Crítica') if 'Ruta Crítica' in cols_exist else None
                idx_imp    = cols_exist.index('Días Impacto') if 'Días Impacto' in cols_exist else None

                # Pintado fila por fila (semáforo + fechas en formato corto)
                for r in range(len(df_export)):
                    fila = df_export.iloc[r]
                    riesgo = str(fila['Nivel Riesgo']) if idx_riesgo is not None else ""
                    rc = str(fila['Ruta Crítica']) if idx_rc is not None else ""
                    try: imp = float(fila['Días Impacto']) if idx_imp is not None else 0.0
                    except: imp = 0.0
                    if "Resumen" in riesgo:
                        fmt_fila = gris
                    elif "Crítico" in riesgo or rc == "Sí":
                        fmt_fila = rojo
                    elif riesgo == "Alto" or imp > 2:
                        fmt_fila = naranja
                    else:
                        fmt_fila = verde
                    fmt_fila_fecha = fmt_fecha_de.get(id(fmt_fila), fmt_fila)
                    for j, c in enumerate(cols_exist):
                        val = fila[c]
                        if c in cols_fecha:
                            dval = pd.to_datetime(val, errors='coerce')
                            if pd.notna(dval):
                                ws.write_datetime(3 + r, j, dval.to_pydatetime(), fmt_fila_fecha)
                            else:
                                ws.write(3 + r, j, "-", fmt_fila)
                        else:
                            if pd.isna(val): val = "-"
                            ws.write(3 + r, j, val, fmt_fila)

                # Ancho de columnas
                anchos = {'Actividad': 34, 'WBS': 10, 'Inicio Base': 12, 'Fin Base': 12, 'Inicio Nuevo': 12, 'Fin Nuevo': 12,
                          'Nivel Riesgo': 16, 'Estado': 26, 'Fecha Última Lluvia': 16, 'Lluvia Total Acum (mm)': 13}
                for j, c in enumerate(cols_exist):
                    ws.set_column(j, j, anchos.get(c, 11))
                ws.freeze_panes(3, 3)
                ws.autofilter(2, 0, 2 + len(df_export), ncol - 1)

                # ============================================================
                # HOJA 2: "Pegar en MS Project" — orden por ID, columna de
                # Duración Nueva lista para copiar/pegar. Resúmenes e hitos en
                # blanco (MS Project los recalcula). Las fechas de fin coinciden
                # con las de CHRONOFLUX al recalcular el Project con estas duraciones.
                # ============================================================
                ws2 = wb.add_worksheet("Pegar en MS Project")
                hdr2 = ['ID', 'WBS', 'Actividad', 'Duración Base (días)', 'Duración Nueva (días)', 'Días Impacto', 'Fin Nuevo (CHRONOFLUX)']
                t2 = wb.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#1E293B', 'font_color': 'white', 'font_size': 12, 'border': 1})
                s2 = wb.add_format({'italic': True, 'bg_color': '#334155', 'font_color': '#E2E8F0', 'font_size': 9})
                h2 = wb.add_format({'bold': True, 'align': 'center', 'bg_color': '#0F172A', 'font_color': 'white', 'border': 1, 'text_wrap': True})
                num2 = wb.add_format({'align': 'center', 'border': 1})
                dnew2 = wb.add_format({'align': 'center', 'border': 1, 'bold': True, 'bg_color': '#FEF9C3'})  # columna a copiar (resaltada)
                fecha2 = wb.add_format({'align': 'center', 'border': 1, 'num_format': 14})
                txt2 = wb.add_format({'border': 1})
                ws2.merge_range(0, 0, 0, len(hdr2)-1, "PEGAR EN MS PROJECT — Copia la columna amarilla 'Duración Nueva' sobre la columna Duración del Project (tareas hoja).", t2)
                ws2.merge_range(1, 0, 1, len(hdr2)-1, "Resúmenes e hitos van vacíos a propósito: MS Project recalcula su duración y fechas a partir de las hijas. Requiere que el calendario laboral del Project coincida con el configurado en CHRONOFLUX.", s2)
                for j, h in enumerate(hdr2): ws2.write(2, j, h, h2)
                for r in range(len(df_export)):
                    fila = df_export.iloc[r]
                    es_res = ("Resumen" in str(fila.get('Nivel Riesgo','')))
                    dn = fila.get('Duración Nueva')
                    ws2.write(3+r, 0, fila.get('ID'), num2)
                    ws2.write(3+r, 1, str(fila.get('WBS','')), num2)
                    ws2.write(3+r, 2, str(fila.get('Actividad','')), txt2)
                    db = pd.to_numeric(fila.get('Duración Base'), errors='coerce')
                    ws2.write(3+r, 3, int(db) if pd.notna(db) else "-", num2)
                    dnv = pd.to_numeric(dn, errors='coerce')
                    if es_res or pd.isna(dnv):
                        ws2.write(3+r, 4, "", dnew2)        # vacío: MS Project lo deriva
                        ws2.write(3+r, 5, "-", num2)
                    else:
                        ws2.write_number(3+r, 4, int(round(dnv)), dnew2)
                        imp = pd.to_numeric(fila.get('Días Impacto'), errors='coerce')
                        ws2.write(3+r, 5, int(imp) if pd.notna(imp) else 0, num2)
                    fn = pd.to_datetime(fila.get('Fin Nuevo'), errors='coerce')
                    if pd.notna(fn): ws2.write_datetime(3+r, 6, fn.to_pydatetime(), fecha2)
                    else: ws2.write(3+r, 6, "-", num2)
                for j, wd in enumerate([8, 12, 40, 16, 18, 12, 18]): ws2.set_column(j, j, wd)
                ws2.freeze_panes(3, 3)

            col_xml, col_xls = st.columns(2)

            # --- XML ajustado para reabrir en MS Project ---
            xml_ok = False
            if st.session_state.get('xml_raw') is not None:
                try:
                    xml_bytes = generar_xml_ajustado(
                        st.session_state['xml_raw'], st.session_state.get('xml_prefix', ''),
                        final, st.session_state.get('xml_hpd', 8.0))
                    col_xml.download_button(
                        "📐 Descargar XML ajustado (abrir en MS Project)", xml_bytes,
                        f"{safe_name}_AJUSTADO.xml", "application/xml",
                        type="primary", use_container_width=True,
                        help="XML con las duraciones nuevas ya inyectadas y el calendario original del proyecto. "
                             "Ábrelo en MS Project (Archivo → Abrir → .xml) y las fechas coincidirán con CHRONOFLUX.")
                    xml_ok = True
                except Exception as e:
                    col_xml.warning(f"No se pudo generar el XML ajustado: {e}")
            if not xml_ok:
                col_xml.info("Carga un XML de MS Project para habilitar la exportación ajustada.")

            # --- Excel de auditoría (se conserva) ---
            col_xls.download_button("📥 Reporte Gerencial (Excel · auditoría)", b_out.getvalue(), f"Reporte_Climatico_{safe_name}.xlsx", "application/vnd.ms-excel", use_container_width=True)
