import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import xml.etree.ElementTree as ET
import requests
import io
import re
import math
from datetime import datetime, timedelta, date

import plotly.express as px
import plotly.graph_objects as go
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode, GridUpdateMode

try:
    import folium
    from streamlit_folium import st_folium
    import networkx as nx
    from streamlit_lottie import st_lottie
except ImportError:
    st.error("⚠️ Falta instalar librerías. Ejecuta: pip install folium streamlit-folium networkx plotly streamlit-aggrid streamlit-lottie")
    st.stop()

# ==============================================================================
# 1. CONFIGURACIÓN Y ESTILO (UI/UX MODERN SAAS 2026)
# ==============================================================================
st.set_page_config(page_title="CHRONOFLUX | CPM AI", layout="wide", page_icon="⚡")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
        html, body, [class*="css"]  { font-family: 'Inter', sans-serif !important; }
        .stApp { background-color: #F4F7F9; }
        #MainMenu {visibility: hidden;} footer {visibility: hidden;}
        .modern-banner {
            background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
            color: #FFFFFF; padding: 24px; border-radius: 16px; text-align: center;
            margin-bottom: 30px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1); border-bottom: 4px solid #AF1E2D;
        }
        .modern-banner h1 { font-size: 2rem; font-weight: 800; margin: 0; }
        .modern-banner p { font-size: 1.1rem; color: #94A3B8; margin-top: 8px; margin-bottom: 0; }
        [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E2E8F0; }
        .stButton>button {
            background-color: #AF1E2D; color: white !important; border-radius: 12px;
            border: none; transition: all 0.3s ease; font-weight: 600; padding: 0.5rem 1rem;
        }
        .stButton>button:hover { transform: translateY(-2px); background-color: #901924; }
        .manual-section {
            background-color: #F8FAFC; padding: 20px; border-radius: 12px;
            border-left: 4px solid #3B82F6; margin-bottom: 16px; border: 1px solid #E2E8F0;
        }
        .manual-section h4 { color: #1E293B; margin-top: 0; font-weight: 700; font-size: 1.1rem; }
        .kpi-container { display: flex; justify-content: space-between; gap: 20px; margin-bottom: 30px; }
        .kpi-box {
            background-color: #FFFFFF; border-radius: 16px; padding: 24px; flex: 1;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); border: 1px solid #E2E8F0; position: relative;
        }
        .kpi-box::before { content: ""; position: absolute; top: 0; left: 0; right: 0; height: 4px; background-color: #AF1E2D; }
        .kpi-title { font-size: 0.85rem; color: #64748B; text-transform: uppercase; font-weight: 600; margin-bottom: 8px; }
        .kpi-value { font-size: 2.5rem; font-weight: 800; color: #0F172A; line-height: 1.2; }
        .kpi-value span { font-size: 1.2rem; font-weight: 600; color: #94A3B8; }
        .kpi-value.danger { color: #EF4444; }
        .kpi-subtitle { font-size: 0.85rem; color: #94A3B8; margin-top: 8px; }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. DICCIONARIO DE IDIOMAS (i18n)
# ==============================================================================
TEXTS = {
    "ES": {
        "banner_sub": "Motor de Simulación Climática y Optimización Topológica CPM",
        "manual_title": "📘 VER MANUAL OPERATIVO DEL SISTEMA",
        "m_sec1_t": "1. Configuración de Entorno",
        "m_sec1_d": "Defina el horario, días laborables y observe el cálculo de feriados en el panel lateral.",
        "m_sec2_t": "2. Geolocalización (Caché Optimizado)",
        "m_sec2_d": "Haga clic en el mapa. El sistema memoriza zonas para cálculos inmediatos.",
        "m_sec3_t": "3. Carga y Simulación Avanzada",
        "m_sec3_d": "Suba su XML. El motor Expected Value Buffer recalculará la red y mutará la ruta crítica automáticamente.",
        "sb_config": "⚙️ Configuración",
        "sb_lang": "🌐 Idioma / Language",
        "sb_h1": "1. Horario de Obra",
        "sb_h2": "2. Días Laborables",
        "sb_h3": "3. Feriados Nacionales",
        "search_loc": "📍 Buscar Ubicación de Proyecto:",
        "coord_lbl": "Coordenadas de Análisis:",
        "chart_title": "🌦️ Comportamiento Climático Histórico",
        "radar_title": "📡 Radar Satelital en Tiempo Real",
        "upload_lbl": "📂 Paso Final: Cargar Cronograma XML (MS Project)",
        "btn_calc": "Ejecutar Cálculo y Optimizar Planificación",
        "kpi_panel": "📊 Panel de Resultados Gerenciales",
        "kpi_1_t": "Actividades Afectadas",
        "kpi_1_s": "totales",
        "kpi_1_sub": "Tareas de campo que sufrieron inyección de EVB.",
        "kpi_2_t": "Retraso del Proyecto",
        "kpi_2_s": "Días Calendario",
        "kpi_2_sub": "Desplazamiento final tras recalcular Ruta Crítica.",
        "kpi_3_t": "Fecha Final Proyectada",
        "kpi_3_sub": "Línea Base original:",
        "tab_1": "📊 Gantt Comparativo",
        "tab_2": "📈 Curva S (Interactiva)",
        "tab_3": "📅 Riesgo Mensual",
        "tab_4": "⚠️ Tabla de Impactos",
        "btn_down": "📥 Descargar Reporte Gerencial Completo (Excel)",
        "sim_start": "Iniciando simulación topológica...",
        "sim_done": "¡Simulación completada con éxito!"
    },
    "EN": {
        "banner_sub": "Climate Simulation Engine and CPM Topological Optimization",
        "manual_title": "📘 VIEW SYSTEM OPERATING MANUAL",
        "m_sec1_t": "1. Environment Setup",
        "m_sec1_d": "Define working hours, workdays, and observe holiday calculations in the sidebar.",
        "m_sec2_t": "2. Geolocation (Optimized Cache)",
        "m_sec2_d": "Click on the map. The system memorizes zones for immediate calculations.",
        "m_sec3_t": "3. Advanced Loading & Simulation",
        "m_sec3_d": "Upload your XML. The Expected Value Buffer engine will recalculate the network and mutate the critical path automatically.",
        "sb_config": "⚙️ Configuration",
        "sb_lang": "🌐 Idioma / Language",
        "sb_h1": "1. Working Hours",
        "sb_h2": "2. Workdays",
        "sb_h3": "3. National Holidays",
        "search_loc": "📍 Search Project Location:",
        "coord_lbl": "Analysis Coordinates:",
        "chart_title": "🌦️ Historical Climate Behavior",
        "radar_title": "📡 Real-Time Satellite Radar",
        "upload_lbl": "📂 Final Step: Upload XML Schedule (MS Project)",
        "btn_calc": "Run Calculation and Optimize Planning",
        "kpi_panel": "📊 Managerial Results Dashboard",
        "kpi_1_t": "Affected Activities",
        "kpi_1_s": "total",
        "kpi_1_sub": "Field tasks that suffered EVB injection.",
        "kpi_2_t": "Project Delay",
        "kpi_2_s": "Calendar Days",
        "kpi_2_sub": "Final displacement after Critical Path recalculation.",
        "kpi_3_t": "Projected End Date",
        "kpi_3_sub": "Original Baseline:",
        "tab_1": "📊 Comparative Gantt",
        "tab_2": "📈 S-Curve (Interactive)",
        "tab_3": "📅 Monthly Risk",
        "tab_4": "⚠️ Impacts Table",
        "btn_down": "📥 Download Complete Managerial Report (Excel)",
        "sim_start": "Starting topological simulation...",
        "sim_done": "Simulation completed successfully!"
    }
}

# ESTADOS Y MEMORIA CACHÉ
if 'lang' not in st.session_state: st.session_state['lang'] = "ES"
if 'lat_actual' not in st.session_state: st.session_state['lat_actual'] = 18.4861
if 'lon_actual' not in st.session_state: st.session_state['lon_actual'] = -69.9312
if 'ubicacion_nombre' not in st.session_state: st.session_state['ubicacion_nombre'] = "Distrito Nacional - Santo Domingo (Centro)"
if 'audit_decision' not in st.session_state: st.session_state['audit_decision'] = None
if 'project_name' not in st.session_state: st.session_state['project_name'] = "Proyecto"
if 'simulacion_activa' not in st.session_state: st.session_state['simulacion_activa'] = False
if 'resultados_finales' not in st.session_state: st.session_state['resultados_finales'] = None

# ==============================================================================
# 3. INTERFAZ LATERAL (CONFIGURACIÓN E IDIOMA)
# ==============================================================================
with st.sidebar:
    lang_choice = st.radio("🌐 Idioma / Language", ["Español", "English"], horizontal=True)
    st.session_state['lang'] = "ES" if lang_choice == "Español" else "EN"
    t = TEXTS[st.session_state['lang']] # Puntero al diccionario actual

    st.header(t["sb_config"])
    st.subheader(t["sb_h1"])
    h_inicio, h_fin = st.slider("Horas / Hours", 0, 23, (8, 17))
    
    st.subheader(t["sb_h2"])
    dias_sel = st.multiselect("Seleccionar / Select:", ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"], default=["Lun","Mar","Mié","Jue","Vie","Sáb"])
    mapa_d = {"Lun":0,"Mar":1,"Mié":2,"Jue":3,"Vie":4,"Sáb":5,"Dom":6}
    dias_idx = [mapa_d[d] for d in dias_sel]
    
    st.markdown("---")
    st.subheader(t["sb_h3"])
    anio_actual = date.today().year
    anio_ver = st.selectbox("Año / Year:", [anio_actual, anio_actual + 1, anio_actual + 2])

# Funciones de Backend (Mantienen la lógica en español internamente)
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
    return feriados
feriados_dict = obtener_feriados_rd()

with st.sidebar:
    f_show = {k:v for k,v in feriados_dict.items() if k.year == anio_ver}
    df_f = pd.DataFrame(list(f_show.items()), columns=['Fecha', 'Celebración']).sort_values('Fecha')
    df_f['Fecha'] = pd.to_datetime(df_f['Fecha']).dt.strftime('%d-%b')
    st.dataframe(df_f, hide_index=True, use_container_width=True, height=250)

# ENCABEZADO
col_izq, col_centro, col_der = st.columns([2, 1, 2])
with col_centro:
    try: st.image("logo_chronoflux.png", use_container_width=True)
    except: st.empty()

st.markdown(f"""
    <div class="modern-banner">
        <h1>CHRONOFLUX AI</h1>
        <p>{t["banner_sub"]}</p>
    </div>
""", unsafe_allow_html=True)

with st.expander(t["manual_title"]):
    st.markdown(f"""
    <div class="manual-section">
        <h4>{t["m_sec1_t"]}</h4><ul><li>{t["m_sec1_d"]}</li></ul>
    </div>
    <div class="manual-section">
        <h4>{t["m_sec2_t"]}</h4><ul><li>{t["m_sec2_d"]}</li></ul>
    </div>
    <div class="manual-section">
        <h4>{t["m_sec3_t"]}</h4><ul><li>{t["m_sec3_d"]}</li></ul>
    </div>
    """, unsafe_allow_html=True)

# ... [AQUÍ VA TODO EL BLOQUE DE LA BASE DE DATOS COORDENADAS_RD Y FUNCIONES DE CLIMA, IGUAL QUE ANTES] ...
COORDENADAS_RD = {
    "Distrito Nacional - Santo Domingo (Centro)": (18.4861, -69.9312),
    "Santiago - Santiago de los Caballeros": (19.4517, -70.6970),
    "La Altagracia - Punta Cana / Bávaro": (18.5601, -68.3725),
    "Ensayo 3 y 4: Las Damas": (18.4756, -69.7782)
}

def actualizar_desde_dropdown():
    coords = COORDENADAS_RD.get(st.session_state.combo_ubicacion, (18.4861, -69.9312))
    st.session_state['lat_actual'] = coords[0]; st.session_state['lon_actual'] = coords[1]
    st.session_state['ubicacion_nombre'] = st.session_state.combo_ubicacion

st.selectbox(t["search_loc"], sorted(list(COORDENADAS_RD.keys())), key='combo_ubicacion', on_change=actualizar_desde_dropdown)
st.markdown(f"**{t['coord_lbl']}** `Lat: {st.session_state['lat_actual']:.4f}, Lon: {st.session_state['lon_actual']:.4f}`")

m = folium.Map(location=[st.session_state['lat_actual'], st.session_state['lon_actual']], zoom_start=12)
folium.Marker([st.session_state['lat_actual'], st.session_state['lon_actual']], popup=st.session_state['ubicacion_nombre'], icon=folium.Icon(color='red')).add_to(m)
map_data = st_folium(m, height=450, use_container_width=True, key="mapa_folium")

if map_data and map_data.get("last_clicked"):
    st.session_state['lat_actual'] = map_data["last_clicked"]["lat"]
    st.session_state['lon_actual'] = map_data["last_clicked"]["lng"]
    st.session_state['ubicacion_nombre'] = f"Pin Manual: {st.session_state['lat_actual']:.4f}, {st.session_state['lon_actual']:.4f}"
    st.rerun()

st.markdown("---")
uploaded = st.file_uploader(t["upload_lbl"], type=['xml'])

if uploaded:
    # (ASUME QUE AQUI ESTAN TUS FUNCIONES auditar_xml Y simular_cronograma INTACTAS)
    
    st.markdown(f"### 🚀 Simulación de Ruta Crítica (CHRONOFLUX V8)")
    c_p, c_m, c_u = st.columns(3)
    prob = c_p.slider("Probabilidad (Pr)", 0, 100, 35) / 100.0
    mm = c_m.slider("Intensidad (Ur)", 0.0, 50.0, 2.5, 0.5)
    umbral_horas = c_u.slider("Umbral (Ut)", 1.0, 8.0, 3.0, 0.5)
    
    if st.button(t["btn_calc"], type="primary", use_container_width=True):
        st.toast(t["sim_start"], icon='🚀')
        # ... EJECUCIÓN DE TU CÓDIGO INTERNO ...
        # simulacion = simular_cronograma(...) 
        st.session_state['simulacion_activa'] = True
        st.toast(t["sim_done"], icon='✅')

    if st.session_state['simulacion_activa']: # Asumiendo que simulacion_activa es True
        # VARIABLES FICTICIAS PARA ESTE EJEMPLO (Se llenan con tus DataFrames)
        count_impact = 15
        len_tareas = 144
        retraso_total_proyecto = 14
        fin_nuevo_max_str = "25 Jul 2026"
        fin_base_max_str = "11 Jul 2026"
        
        st.markdown(f"### {t['kpi_panel']}")
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-box">
                <div class="kpi-title">{t['kpi_1_t']}</div>
                <div class="kpi-value">{count_impact} <span>/ {len_tareas} {t['kpi_1_s']}</span></div>
                <div class="kpi-subtitle">{t['kpi_1_sub']}</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-title">{t['kpi_2_t']}</div>
                <div class="kpi-value danger">+{max(0, retraso_total_proyecto)} <span>{t['kpi_2_s']}</span></div>
                <div class="kpi-subtitle">{t['kpi_2_sub']}</div>
            </div>
            <div class="kpi-box">
                <div class="kpi-title">{t['kpi_3_t']}</div>
                <div class="kpi-value" style="font-size: 2rem;">{fin_nuevo_max_str}</div>
                <div class="kpi-subtitle">{t['kpi_3_sub']} {fin_base_max_str}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2, tab3, tab4 = st.tabs([t['tab_1'], t['tab_2'], t['tab_3'], t['tab_4']])
        # ... AQUI VA LA LOGICA DE TUS GRAFICAS Y TABLAS INTACTA ...
        
        st.download_button(t["btn_down"], data="dummy", file_name="Reporte.xlsx", use_container_width=True, type="primary")
