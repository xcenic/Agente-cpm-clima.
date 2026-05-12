import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import xml.etree.ElementTree as ET
import requests
import io
import re
import math
from datetime import datetime, timedelta, date

# NUEVAS LIBRERÍAS PREMIUM Y UI
import plotly.express as px
import plotly.graph_objects as go
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode, GridUpdateMode

# LIBRERÍAS DE MAPA, GRAFOS Y ANIMACIONES
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
st.set_page_config(page_title="CHRONOFLUX | Motor CPM", layout="wide", page_icon="⚡")

# Inyección de CSS Avanzado
st.markdown("""
    <style>
        /* Importar fuente moderna y limpia */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
        
        /* Aplicar fuente a todo */
        html, body, [class*="css"]  {
            font-family: 'Inter', sans-serif !important;
        }
        
        /* Fondo de la aplicación (Gris muy claro, estilo Dashboard) */
        .stApp {
            background-color: #F4F7F9;
        }

        /* Ocultar elementos de menú predeterminados de Streamlit para un look más limpio */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* Banner Principal Moderno (Gradiente oscuro con acento rojo) */
        .modern-banner {
            background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
            color: #FFFFFF;
            padding: 24px;
            border-radius: 16px;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
            border-bottom: 4px solid #AF1E2D;
            position: relative;
            overflow: hidden;
        }
        .modern-banner h1 {
            font-size: 2rem;
            font-weight: 800;
            margin: 0;
            letter-spacing: -0.02em;
        }
        .modern-banner p {
            font-size: 1.1rem;
            color: #94A3B8;
            margin-top: 8px;
            margin-bottom: 0;
            font-weight: 400;
        }

        /* Estilo del Sidebar */
        [data-testid="stSidebar"] {
            background-color: #FFFFFF;
            border-right: 1px solid #E2E8F0;
        }
        
        /* Botones primarios redondeados con Hover Effects */
        .stButton>button {
            background-color: #AF1E2D;
            color: white !important;
            border-radius: 12px;
            border: none;
            transition: all 0.3s ease;
            font-weight: 600;
            padding: 0.5rem 1rem;
            box-shadow: 0 4px 6px -1px rgba(175, 30, 45, 0.2);
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(175, 30, 45, 0.3);
            background-color: #901924;
        }

        /* Contenedores blancos (Tarjetas de contenido) */
        .css-1r6slb0, .css-18e3th9, .css-1d391kg {
            background-color: #FFFFFF;
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1);
            border: 1px solid #F1F5F9;
        }

        /* Secciones del Manual (Neumorfismo plano) */
        .manual-section {
            background-color: #F8FAFC;
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid #3B82F6; /* Acento azul para información */
            margin-bottom: 16px;
            border-top: 1px solid #E2E8F0;
            border-right: 1px solid #E2E8F0;
            border-bottom: 1px solid #E2E8F0;
        }
        .manual-section h4 {
            color: #1E293B;
            margin-top: 0;
            font-weight: 700;
            font-size: 1.1rem;
        }
        .manual-section ul { color: #475569; }

        /* --- NUEVO SISTEMA DE KPIs ESTILO ENTERPRISE --- */
        .kpi-container {
            display: flex;
            justify-content: space-between;
            gap: 20px;
            margin-bottom: 30px;
        }
        .kpi-box {
            background-color: #FFFFFF;
            border-radius: 16px;
            padding: 24px;
            flex: 1;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
            border: 1px solid #E2E8F0;
            transition: transform 0.2s ease;
            position: relative;
            overflow: hidden;
        }
        .kpi-box:hover {
            transform: translateY(-4px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        }
        /* Línea de acento superior en los KPIs */
        .kpi-box::before {
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 4px;
            background-color: #AF1E2D;
        }
        .kpi-title {
            font-size: 0.85rem;
            color: #64748B;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .kpi-value {
            font-size: 2.5rem;
            font-weight: 800;
            color: #0F172A;
            line-height: 1.2;
        }
        .kpi-value span { font-size: 1.2rem; font-weight: 600; color: #94A3B8; }
        .kpi-value.danger { color: #EF4444; }
        .kpi-subtitle {
            font-size: 0.85rem;
            color: #94A3B8;
            margin-top: 8px;
        }

        /* Pestañas (Tabs) de Streamlit personalizadas */
        [data-baseweb="tab-list"] {
            gap: 8px;
            background-color: #FFFFFF;
            padding: 10px;
            border-radius: 12px;
            box-shadow: 0 1px 3px 0 rgba(0,0,0,0.1);
        }
        [data-baseweb="tab"] {
            padding: 10px 20px !important;
            border-radius: 8px !important;
            background-color: transparent !important;
            border: none !important;
        }
        [aria-selected="true"] {
            background-color: #F1F5F9 !important;
            color: #AF1E2D !important;
            font-weight: 600 !important;
        }
    </style>
""", unsafe_allow_html=True)

# CARGADOR DE ANIMACIONES LOTTIE
def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200: return None
        return r.json()
    except: return None

lottie_weather = load_lottieurl("https://lottie.host/809c951d-bca6-4d08-be94-06d95719bc4a/S82gPZpZIf.json")

# ESTADOS Y MEMORIA CACHÉ
if 'lat_actual' not in st.session_state: st.session_state['lat_actual'] = 18.4861
if 'lon_actual' not in st.session_state: st.session_state['lon_actual'] = -69.9312
if 'ubicacion_nombre' not in st.session_state: st.session_state['ubicacion_nombre'] = "Distrito Nacional - Santo Domingo (Centro)"
if 'audit_decision' not in st.session_state: st.session_state['audit_decision'] = None
if 'project_name' not in st.session_state: st.session_state['project_name'] = "Proyecto"
if 'simulacion_activa' not in st.session_state: st.session_state['simulacion_activa'] = False
if 'resultados_finales' not in st.session_state: st.session_state['resultados_finales'] = None

# ==============================================================================
# ENCABEZADO MINIMALISTA (Logo pequeño + Banner CSS)
# ==============================================================================
col_izq, col_centro, col_der = st.columns([2, 1, 2])
with col_centro:
    try: st.image("logo_chronoflux.png", use_container_width=True)
    except: st.empty()

st.markdown("""
    <div class="modern-banner">
        <h1>CHRONOFLUX AI</h1>
        <p>Motor de Simulación Climática y Optimización Topológica CPM</p>
    </div>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. MANUAL DETALLADO DE USUARIO
# ==============================================================================
with st.expander("📘 VER MANUAL OPERATIVO DEL SISTEMA"):
    st.markdown("""
    <div class="manual-section">
        <h4>1. Configuración de Entorno</h4>
        <ul><li>Defina el horario, días laborables y observe el cálculo de feriados en el panel lateral.</li></ul>
    </div>
    <div class="manual-section">
        <h4>2. Geolocalización (Caché Optimizado)</h4>
        <ul><li>Haga clic en el mapa. El sistema memoriza zonas para cálculos inmediatos.</li></ul>
    </div>
    <div class="manual-section">
        <h4>3. Carga y Simulación Avanzada</h4>
        <ul><li>Suba su XML. El motor <i>Expected Value Buffer</i> recalculará la red y mutará la ruta crítica automáticamente.</li></ul>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 3. BASE DE DATOS GEOGRÁFICA
# ==============================================================================
COORDENADAS_RD = {
    "Azua - Azua de Compostela (Cabecera)": (18.4532, -70.7349), "Azua - Padre Las Casas": (18.7339, -70.9328), "Azua - Peralta": (18.5786, -70.7714),
    "Baoruco - Neiba (Cabecera)": (18.4833, -71.4167), "Baoruco - Tamayo": (18.3942, -71.2025), "Baoruco - Los Ríos": (18.5194, -71.5878),
    "Barahona - Santa Cruz de Barahona (Cabecera)": (18.2085, -71.1008), "Barahona - Vicente Noble": (18.3814, -71.1764), "Barahona - Paraíso": (17.9917, -71.1653), "Barahona - Enriquillo": (17.9031, -71.2294),
    "Dajabón - Dajabón (Cabecera)": (19.5488, -71.7083), "Dajabón - Loma de Cabrera": (19.4217, -71.6053), "Dajabón - Restauración": (19.3139, -71.6961),
    "Distrito Nacional - Santo Domingo (Centro)": (18.4861, -69.9312), "Distrito Nacional - Zona Colonial": (18.4722, -69.8844), "Distrito Nacional - Los Cacicazgos": (18.4452, -69.9575),
    "Duarte - San Francisco de Macorís (Cabecera)": (19.3009, -70.2525), "Duarte - Castillo": (19.2133, -70.0272), "Duarte - Villa Riva": (19.1825, -69.9128), "Duarte - Arenoso": (19.1914, -69.8592),
    "El Seibo - Santa Cruz de El Seibo (Cabecera)": (18.7656, -69.0389), "El Seibo - Miches": (18.9839, -69.0475), "El Seibo - Pedro Sánchez": (18.8631, -69.1125),
    "Elías Piña - Comendador (Cabecera)": (18.8767, -71.7029), "Elías Piña - Hondo Valle": (18.7125, -71.7022), "Elías Piña - Bánica": (19.0803, -71.7036),
    "Espaillat - Moca (Cabecera)": (19.6267, -70.2764), "Espaillat - Gaspar Hernández": (19.6261, -70.2794), "Espaillat - Jamao al Norte": (19.6369, -70.4464),
    "Hato Mayor - Hato Mayor del Rey (Cabecera)": (18.7622, -69.2565), "Hato Mayor - Sabana de la Mar": (19.0556, -69.3886), "Hato Mayor - El Valle": (18.9667, -69.3667),
    "Hermanas Mirabal - Salcedo (Cabecera)": (19.3735, -70.4188), "Hermanas Mirabal - Tenares": (19.3744, -70.3508), "Hermanas Mirabal - Villa Tapia": (19.2978, -70.4350),
    "Independencia - Jimaní (Cabecera)": (18.4877, -71.8515), "Independencia - Duvergé": (18.3778, -71.5244), "Independencia - La Descubierta": (18.5700, -71.7289),
    "La Altagracia - Higüey (Cabecera)": (18.6147, -68.7171), "La Altagracia - Punta Cana / Bávaro": (18.5601, -68.3725), "La Altagracia - San Rafael del Yuma": (18.4333, -68.6667), "La Altagracia - Bayahíbe": (18.3750, -68.8361),
    "La Romana - La Romana (Cabecera)": (18.4273, -68.9728), "La Romana - Guaymate": (18.5889, -68.9469), "La Romana - Villa Hermosa": (18.4417, -69.0028),
    "La Vega - Concepción de La Vega (Cabecera)": (19.2208, -70.5292), "La Vega - Constanza": (18.9089, -70.7444), "La Vega - Jarabacoa": (19.1217, -70.6411), "La Vega - Jima Abajo": (19.1361, -70.3756),
    "María Trinidad Sánchez - Nagua (Cabecera)": (19.3667, -69.8511), "María Trinidad Sánchez - Cabrera": (19.6417, -69.9022), "María Trinidad Sánchez - Río San Juan": (19.6381, -70.0767),
    "Monseñor Nouel - Bonao (Cabecera)": (18.9272, -70.3973), "Monseñor Nouel - Maimón": (18.9083, -70.2667), "Monseñor Nouel - Piedra Blanca": (18.8433, -70.3164),
    "Monte Cristi - San Fernando (Cabecera)": (19.8483, -71.6450), "Monte Cristi - Villa Vásquez": (19.7431, -71.4489), "Monte Cristi - Guayubín": (19.6389, -71.3250), "Monte Cristi - Pepillo Salcedo (Manzanillo)": (19.7042, -71.7375),
    "Monte Plata - Monte Plata (Cabecera)": (18.8078, -69.7848), "Monte Plata - Bayaguana": (18.7572, -69.6353), "Monte Plata - Yamasá": (18.7733, -70.0258), "Monte Plata - Sabana Grande de Boyá": (18.9444, -69.7936),
    "Pedernales - Pedernales (Cabecera)": (18.0333, -71.7431), "Pedernales - Oviedo": (17.8056, -71.4014),
    "Peravia - Baní (Cabecera)": (18.2796, -70.3319), "Peravia - Nizao": (18.2464, -70.2111), "Peravia - Matanzas": (18.2567, -70.4214),
    "Puerto Plata - San Felipe (Cabecera)": (19.7934, -70.6884), "Puerto Plata - Sosúa": (19.7667, -70.5167), "Puerto Plata - Cabarete": (19.7486, -70.4075), "Puerto Plata - Altamira": (19.6833, -70.8333), "Puerto Plata - Luperón": (19.8967, -70.9633),
    "Samaná - Santa Bárbara (Cabecera)": (19.2056, -69.3262), "Samaná - Las Terrenas": (19.3217, -69.5331), "Samaná - Sánchez": (19.2278, -69.6139),
    "San Cristóbal - San Cristóbal (Cabecera)": (18.4162, -70.1112), "San Cristóbal - Bajos de Haina": (18.4150, -70.0333), "San Cristóbal - Villa Altagracia": (18.6750, -70.1708), "San Cristóbal - Yaguate": (18.3333, -70.1833),
    "San José de Ocoa - Ocoa (Cabecera)": (18.5438, -70.5070), "San José de Ocoa - Sabana Larga": (18.5750, -70.5167), "San José de Ocoa - Rancho Arriba": (18.7333, -70.4667),
    "San Juan - San Juan de la Maguana (Cabecera)": (18.8059, -71.2299), "San Juan - Las Matas de Farfán": (18.8731, -71.5164), "San Juan - El Cercado": (18.7333, -71.5167),
    "San Pedro de Macorís - SPM (Cabecera)": (18.4637, -69.3041), "San Pedro de Macorís - Juan Dolio": (18.4239, -69.4161), "San Pedro de Macorís - Consuelo": (18.5333, -69.2833),
    "Sánchez Ramírez - Cotuí (Cabecera)": (19.0512, -70.1468), "Sánchez Ramírez - Fantino": (19.1167, -70.2167), "Sánchez Ramírez - Cevicos": (19.0333, -69.9833),
    "Santiago - Santiago de los Caballeros (Cabecera)": (19.4517, -70.6970), "Santiago - Villa González": (19.5333, -70.7833), "Santiago - Licey al Medio": (19.4333, -70.6000), "Santiago - Tamboril": (19.4833, -70.6000), "Santiago - San José de las Matas": (19.3389, -70.9389),
    "Santiago Rodríguez - Sabaneta (Cabecera)": (19.4791, -71.3457), "Santiago Rodríguez - Monción": (19.4167, -71.1667),
    "Santo Domingo - Santo Domingo Este": (18.4861, -69.8500), "Santo Domingo - Santo Domingo Norte": (18.5500, -69.9000), "Santo Domingo - Santo Domingo Oeste": (18.5000, -70.0000), "Santo Domingo - Boca Chica": (18.4500, -69.6000), "Santo Domingo - Los Alcarrizos": (18.5167, -70.0333),
    "Valverde - Mao (Cabecera)": (19.5517, -71.0779), "Valverde - Esperanza": (19.5833, -71.0000), "Valverde - Laguna Salada": (19.6500, -71.0833)
}

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
    lat_r = round(lat, 2)
    lon_r = round(lon, 2)
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat_r}&longitude={lon_r}&start_date=2014-01-01&end_date=2023-12-31&hourly=precipitation&timezone=auto"
    try:
        r = requests.get(url)
        data = r.json()
        df = pd.DataFrame({'time': pd.to_datetime(data['hourly']['time']), 'mm': data['hourly']['precipitation']})
        df['hora'] = df['time'].dt.hour
        df_laboral = df[(df['hora'] >= hora_inicio) & (df['hora'] <= hora_fin)].copy()
        df_laboral['fecha_date'] = df_laboral['time'].dt.date
        df_daily_sum = df_laboral.groupby('fecha_date')['mm'].sum().reset_index()
        df_daily_sum['dia_mes'] = pd.to_datetime(df_daily_sum['fecha_date']).dt.strftime('%m-%d')
        df_daily_sum['fecha_full'] = pd.to_datetime(df_daily_sum['fecha_date'])
        
        df_daily_sum['lluvio'] = (df_daily_sum['mm'] > 0.5).astype(int)
        
        clima_map = df_daily_sum.groupby('dia_mes').agg(
            probabilidad=('mm', lambda x: (x > 0.5).mean()), 
            mm_promedio=('mm', 'mean'),
            ultima_fecha_lluvia=('fecha_full', lambda x: x[df_daily_sum.loc[x.index, 'mm'] > 0.5].max() if (df_daily_sum.loc[x.index, 'mm'] > 0.5).any() else None)
        ).to_dict('index')
        
        df_daily_sum['mes_num'] = pd.to_datetime(df_daily_sum['fecha_date']).dt.month
        mapa_meses = {1:'Ene', 2:'Feb', 3:'Mar', 4:'Abr', 5:'May', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dic'}
        df_daily_sum['Mes'] = df_daily_sum['mes_num'].map(mapa_meses)
        df_grafico = df_daily_sum.groupby(['mes_num', 'Mes']).agg(mm=('mm', 'mean'), prob_lluvia=('lluvio', 'mean')).reset_index()
        return df_grafico, clima_map, list(mapa_meses.values())
    except: return None, None, None

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

    tareas = []
    uid_to_id = {}
    valid_ids = []

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

# ==============================================================================
# ALGORITMO CPM - EXPECTED VALUE BUFFER, MATRIZ GEOTÉCNICA Y CUANTIZACIÓN V8
# ==============================================================================
def simular_cronograma(df, clima, prob_min, mm_min, dias_idx, feriados, reparar, umbral_horas, h_inicio, h_fin):
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
    jornada_horas = h_fin - h_inicio if h_fin > h_inicio else 8

    # --- MATRIZ GEOTÉCNICA DE IMPACTO CONSTRUCTIVO (Ic) ---
    def calcular_ic(nombre_tarea):
        nombre = str(nombre_tarea).lower()
        if any(palabra in nombre for palabra in ['acero', 'hormigon', 'hormigón', 'encofrado', 'vaciado', 'muro', 'alcantarilla']):
            return 1.0
        elif any(palabra in nombre for palabra in ['asfalto', 'imprimacion', 'imprimación', 'pintura', 'señalizacion', 'señalización']):
            return 1.5
        elif any(palabra in nombre for palabra in ['base', 'subbase', 'sub-base', 'granular', 'afirmado']):
            return 2.0
        elif any(palabra in nombre for palabra in ['corte', 'relleno', 'subrasante', 'tierra', 'excavacion', 'excavación']):
            return 3.0
        return 1.5 
        
    def obtener_tr_secado(ic):
        if ic >= 3.0: return 48.0
        if ic >= 2.0: return 24.0
        if ic >= 1.0: return 4.0
        return 0.0

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
        stats_prob, stats_mm, rain_total = 0, 0, 0.0
        retraso_teorico_dias = 0.0
        last_rain_date = None

        # IDENTIFICAMOS EL IMPACTO CONSTRUCTIVO REAL
        impacto_constructivo_ic = calcular_ic(row['Name'])
        tr_horas = obtener_tr_secado(impacto_constructivo_ic)
        
        if not row['IsSummary'] and not row['IsMilestone'] and new_start:
            work_needed = math.ceil(base_dur_float) if base_dur_float > 0 else 1
            work_done = 0
            cursor = new_start
            
            while work_done < work_needed:
                if es_habil(cursor, dias_idx, feriados):
                    k = cursor.strftime('%m-%d')
                    if k in clima:
                        h = clima[k]
                        rain_total += h['mm_promedio']
                        stats_prob = max(stats_prob, h['probabilidad'])
                        if h['probabilidad'] >= prob_min and h['mm_promedio'] >= mm_min:
                            stats_mm = max(stats_mm, h['mm_promedio'])
                            # EVB PURO
                            retraso_teorico_dias += (h['probabilidad'] * impacto_constructivo_ic)
                            if h['ultima_fecha_lluvia']: last_rain_date = h['ultima_fecha_lluvia'].date()
                    work_done += 1 
                cursor += timedelta(days=1)
                
            # --- INCORPORACIÓN FUNCIÓN Q ---
            nota_cuantizacion = ""
            if retraso_teorico_dias > 0:
                # 1. Redondeo a media jornada
                retraso_cuantizado = math.ceil(retraso_teorico_dias * 2) / 2
                
                # 2. Verificamos horas restantes contra el Ut
                horas_restantes = 8 - ((retraso_cuantizado % 1) * 8)
                if 0 < horas_restantes < umbral_horas:
                    retraso_cuantizado = math.ceil(retraso_cuantizado)
                
                if retraso_cuantizado != retraso_teorico_dias:
                    nota_cuantizacion = f" (Q={retraso_cuantizado}d)"
            else:
                retraso_cuantizado = 0.0
            
            if note == "OK" and retraso_cuantizado > 0:
                note = f"Impacto Clima{nota_cuantizacion} [Ic={impacto_constructivo_ic}]"
            elif note != "OK" and retraso_cuantizado > 0:
                note += f" | Impacto Clima{nota_cuantizacion} [Ic={impacto_constructivo_ic}]"
            
            buffer_restante = math.ceil(retraso_cuantizado)
            while buffer_restante > 0:
                if es_habil(cursor, dias_idx, feriados): buffer_restante -= 1
                cursor += timedelta(days=1)
                
            new_finish = cursor - timedelta(days=1)
            new_dur_float = base_dur_float + retraso_cuantizado
            
        elif row['IsMilestone']:
            new_dur_float = 0
            if new_start: new_finish = new_start
                
        fecha_fin_calculada[tid] = new_finish
        G.nodes[tid]['ES'] = new_start
        G.nodes[tid]['EF'] = new_finish
        G.nodes[tid]['dur_ajustada'] = new_dur_float

        res_temp[tid] = {
            'ID': tid, 'WBS': row['WBS'], 'Actividad': row['Name'], 'IsSummary': row['IsSummary'], 'IsMilestone': row['IsMilestone'],
            'Duración Base': redondear_duracion(base_dur_float), 'Inicio Base': start_dt, 'Fin Base': finish_dt,
            'Duración Nueva': redondear_duracion(new_dur_float), 'Inicio Nuevo': new_start, 'Fin Nuevo': new_finish,
            'Tr (Secado/Horas)': tr_horas,  # Columna Tr agregada aquí
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
        if not succs:
            node['LF'] = max_project_ef
        else:
            valid_ls = [G.nodes[s].get('LS') for s in succs if G.nodes[s].get('LS') is not None]
            if valid_ls:
                min_succ_ls = min(valid_ls)
                cursor = min_succ_ls - timedelta(days=1)
                while not es_habil(cursor, dias_idx, feriados):
                    cursor -= timedelta(days=1)
                node['LF'] = cursor
            else:
                node['LF'] = max_project_ef

        dur = math.ceil(node.get('dur_ajustada', 0))
        cursor = node['LF']
        if dur > 1:
            days_stepped = 1
            while days_stepped < dur:
                cursor -= timedelta(days=1)
                if es_habil(cursor, dias_idx, feriados): days_stepped += 1
        node['LS'] = cursor

        ef = node['EF']
        lf = node['LF']
        tf_days = 0
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

        node['TF'] = tf_days
        node['is_critical'] = (tf_days <= 0)
        
        res_temp[tid]['Holgura (Días)'] = tf_days
        res_temp[tid]['Ruta Crítica'] = "Sí" if tf_days <= 0 else "No"
        
        # Eliminada Nivel de Riesgo subjetivo, mantenemos Nivel de impacto si se quiere
        impact = res_temp[tid]['Días Impacto']
        res_temp[tid]['Nivel Riesgo'] = "Crítico (Mutada)" if (tf_days <= 0 and impact > 0) else ("Alto" if impact > 2 else "Normal")

    df_res = pd.DataFrame(list(res_temp.values())).sort_values('ID')
    df_res['Holgura (Días)'] = df_res['Holgura (Días)'].astype(object)

    for i in df_res[df_res['IsSummary'] == True].index:
        wbs_val = str(df_res.at[i, 'WBS'])
        wbs_prefix = wbs_val + '.'
        
        children = df_res[(df_res['WBS'].astype(str).str.startswith(wbs_prefix)) & (df_res['IsSummary'] == False)]
        if children.empty and (df_res.at[i, 'ID'] == 0 or wbs_val == '0' or wbs_val == 'None'):
            children = df_res[df_res['IsSummary'] == False]
            
        if not children.empty:
            min_start = children['Inicio Nuevo'].dropna().min()
            max_finish = children['Fin Nuevo'].dropna().max()
            
            if pd.notna(min_start): df_res.at[i, 'Inicio Nuevo'] = min_start
            if pd.notna(max_finish): df_res.at[i, 'Fin Nuevo'] = max_finish
            
            if pd.notna(min_start) and pd.notna(max_finish) and max_finish >= min_start:
                c_dias = 0
                cursor = min_start
                while cursor <= max_finish:
                    if es_habil(cursor, dias_idx, feriados):
                        c_dias += 1
                    cursor += timedelta(days=1)
                
                df_res.at[i, 'Duración Nueva'] = c_dias
                impacto_resumen = c_dias - df_res.at[i, 'Duración Base']
                df_res.at[i, 'Días Impacto'] = impacto_resumen
                df_res.at[i, 'Nivel Riesgo'] = "Alto" if impacto_resumen > 0 else "Normal"
            else:
                df_res.at[i, 'Días Impacto'] = 0
                df_res.at[i, 'Nivel Riesgo'] = "N/A"
                
            df_res.at[i, 'Prob. Lluvia'] = "-"
            df_res.at[i, 'mm Lluvia Max'] = "-"
            df_res.at[i, 'Holgura (Días)'] = "-"
            df_res.at[i, 'Ruta Crítica'] = "-"
            df_res.at[i, 'Tr (Secado/Horas)'] = "-"
            
    # REQUISITO 2: ORDENAR POR ID DE MANERA ESTRICTA ANTES DE DEVOLVER
    return df_res.sort_values('ID')

# ==============================================================================
# 7. INTERFAZ PRINCIPAL (SIDEBAR ACTUALIZADO)
# ==============================================================================
with st.sidebar:
    st.header("⚙️ Configuración")
    st.subheader("1. Horario de Obra")
    h_inicio, h_fin = st.slider("Jornada", 0, 23, (8, 17))
    st.subheader("2. Días Laborables")
    dias_sel = st.multiselect("Seleccionar:", ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"], default=["Lun","Mar","Mié","Jue","Vie","Sáb"])
    mapa_d = {"Lun":0,"Mar":1,"Mié":2,"Jue":3,"Vie":4,"Sáb":5,"Dom":6}
    dias_idx = [mapa_d[d] for d in dias_sel]
    
    st.markdown("---")
    st.subheader("3. Feriados Nacionales")
    anio_ver = st.selectbox("Año a visualizar:", [anio_actual, anio_actual + 1, anio_actual + 2])
    f_show = {k:v for k,v in feriados_dict.items() if k.year == anio_ver}
    df_f = pd.DataFrame(list(f_show.items()), columns=['Fecha', 'Celebración']).sort_values('Fecha')
    df_f['Fecha'] = pd.to_datetime(df_f['Fecha']).dt.strftime('%d-%b')
    st.dataframe(df_f, hide_index=True, use_container_width=True, height=250)

# ==============================================================================
# SECCIÓN PRINCIPAL: UBICACIÓN Y MAPA PANORÁMICO
# ==============================================================================
def actualizar_desde_dropdown():
    coords = COORDENADAS_RD.get(st.session_state.combo_ubicacion, (18.4861, -69.9312))
    st.session_state['lat_actual'] = coords[0]; st.session_state['lon_actual'] = coords[1]
    st.session_state['ubicacion_nombre'] = st.session_state.combo_ubicacion

st.selectbox("📍 Buscar Ubicación de Proyecto:", sorted(list(COORDENADAS_RD.keys())), key='combo_ubicacion', on_change=actualizar_desde_dropdown)
st.markdown(f"**Coordenadas de Análisis:** `Latitud: {st.session_state['lat_actual']:.4f}, Longitud: {st.session_state['lon_actual']:.4f}`")

m = folium.Map(location=[st.session_state['lat_actual'], st.session_state['lon_actual']], zoom_start=12)
m.add_child(folium.LatLngPopup()) 
folium.Marker([st.session_state['lat_actual'], st.session_state['lon_actual']], popup=st.session_state['ubicacion_nombre'], icon=folium.Icon(color='red', icon='info-sign')).add_to(m)
map_data = st_folium(m, height=450, use_container_width=True, key="mapa_folium")

if map_data and map_data.get("last_clicked"):
    lat_c = map_data["last_clicked"]["lat"]
    lon_c = map_data["last_clicked"]["lng"]
    if round(lat_c, 4) != round(st.session_state['lat_actual'], 4) or round(lon_c, 4) != round(st.session_state['lon_actual'], 4):
        st.session_state['lat_actual'] = lat_c
        st.session_state['lon_actual'] = lon_c
        st.session_state['ubicacion_nombre'] = f"Pin Manual: {lat_c:.4f}, {lon_c:.4f}"
        st.rerun()

st.markdown("---")

# ==============================================================================
# GRÁFICA CLIMÁTICA Y RADAR
# ==============================================================================
st.subheader(f"🌦️ Comportamiento Climático Histórico ({st.session_state['ubicacion_nombre']})")
with st.spinner("Accediendo al caché geoespacial o descargando micro-clima..."):
    df_g, clima, orden = obtener_clima_horario_laboral(st.session_state['lat_actual'], st.session_state['lon_actual'], h_inicio, h_fin)
    if df_g is not None:
        fig_clima = px.bar(df_g, x='Mes', y='mm', text='mm', 
                           color_discrete_sequence=['#AF1E2D'],
                           hover_data={'prob_lluvia': ':.1%'},
                           labels={'mm': 'Lluvia Promedio (mm/día)', 'prob_lluvia': 'Probabilidad de Lluvia'})
        
        fig_clima.update_traces(texttemplate='%{text:.1f}', textposition='outside', marker_line_color='rgba(0,0,0,0)', opacity=0.9)
        fig_clima.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', yaxis=dict(showgrid=True, gridcolor='#E2E8F0'), xaxis_title=None, height=400)
        st.plotly_chart(fig_clima, use_container_width=True)

st.markdown("---")
st.subheader(f"📡 Radar Satelital en Tiempo Real ({st.session_state['ubicacion_nombre']})")
windy_html = f"""
<iframe width="100%" height="450" 
    src="https://embed.windy.com/embed.html?type=map&location=coordinates&metricRain=mm&metricTemp=°C&metricWind=km/h&zoom=9&overlay=rain&product=ecmwf&level=surface&lat={st.session_state['lat_actual']}&lon={st.session_state['lon_actual']}" 
    frameborder="0" style="border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
</iframe>
"""
components.html(windy_html, height=450)
st.markdown("---")

# ==============================================================================
# CARGA DE XML Y SIMULACIÓN
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
        st.warning(f"⚠️ {len(errores)} Tareas con problemas lógicos.")
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
        st.markdown("### 🚀 Simulación de Ruta Crítica (CHRONOFLUX V8)")
        
        c_p, c_m, c_u = st.columns(3)
        # REQUISITO 4: Nomenclatura ajustada en la UI
        prob = c_p.slider("Probabilidad de Lluvia (%) - Pr", 0, 100, 65, help="Días con esta probabilidad o mayor serán evaluados.") / 100.0
        mm = c_m.slider("Intensidad (mm/día) - Ur", 0.0, 50.0, 5.0, 0.5, help="Umbral de Riesgo (Ur). Nivel de lluvia necesario para paralizar la actividad.")
        umbral_horas = c_u.slider("Umbral Mínimo (Horas) - Ut", 1.0, 8.0, 3.0, 0.5, help="Umbral Operativo (Ut). Si la fracción de horas operables es menor a este umbral, se pierde la jornada completa.")
        
        if st.button("Ejecutar Cálculo y Optimizar Planificación", type="primary", use_container_width=True):
            st.toast('Iniciando simulación topológica...', icon='🚀')
            
            with st.spinner("Procesando motor estocástico..."):
                final = simular_cronograma(df_aud, clima, prob, mm, dias_idx, feriados_dict, st.session_state['audit_decision'], umbral_horas, h_inicio, h_fin)
                st.session_state['resultados_finales'] = final
                st.session_state['simulacion_activa'] = True
                st.toast('¡Simulación completada con éxito!', icon='✅')
                
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
            
            # --- PANEL DE KPIs ---
            st.markdown("### 📊 Panel de Resultados Gerenciales")
            st.markdown(f"""
            <div class="kpi-container">
                <div class="kpi-box">
                    <div class="kpi-title">Actividades Afectadas</div>
                    <div class="kpi-value">{count_impact} <span>/ {len(tareas_evaluables)} totales</span></div>
                    <div class="kpi-subtitle">Tareas de campo que sufrieron inyección de EVB.</div>
                </div>
                <div class="kpi-box">
                    <div class="kpi-title">Retraso del Proyecto</div>
                    <div class="kpi-value {'danger' if retraso_total_proyecto > 0 else ''}">+{max(0, retraso_total_proyecto)} <span>Días Calendario</span></div>
                    <div class="kpi-subtitle">Desplazamiento final tras recalcular Ruta Crítica.</div>
                </div>
                <div class="kpi-box">
                    <div class="kpi-title">Fecha Final Proyectada</div>
                    <div class="kpi-value" style="font-size: 2rem;">{fin_nuevo_max.strftime("%d %b %Y") if pd.notna(fin_nuevo_max) else 'N/A'}</div>
                    <div class="kpi-subtitle">Línea Base original: {fin_base_max.strftime('%d %b %Y') if pd.notna(fin_base_max) else 'N/A'}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            act_reales = final[(final['IsSummary'] == False) & (final['IsMilestone'] == False)]
            
            # PESTAÑAS
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Gantt Comparativo", "📈 Curva S (Interactiva)", "📅 Riesgo Mensual", "⚠️ Tabla de Impactos"])
            
            with tab1:
                st.markdown("#### Diagrama de Gantt Ajustado")
                df_gantt = act_reales.copy()
                df_gantt['Inicio Nuevo'] = pd.to_datetime(df_gantt['Inicio Nuevo'])
                df_gantt['Fin Nuevo'] = pd.to_datetime(df_gantt['Fin Nuevo'])
                df_gantt = df_gantt.sort_values('Inicio Nuevo')
                
                if not df_gantt.empty:
                    fig_gantt = px.timeline(df_gantt, x_start="Inicio Nuevo", x_end="Fin Nuevo", y="Actividad",
                                            color="Días Impacto", color_continuous_scale=px.colors.sequential.Reds,
                                            hover_data=["Duración Nueva", "Holgura (Días)", "Ruta Crítica"])
                    fig_gantt.update_yaxes(autorange="reversed")
                    fig_gantt.update_layout(height=600, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_gantt, use_container_width=True)
                else:
                    st.info("No hay datos para generar el Gantt.")
            
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
                
                fig_s = px.line(df_s, x='Fecha', y='Acumulado', color='Tipo', 
                                color_discrete_map={'Base': '#94A3B8', 'Sugerido': '#AF1E2D'},
                                markers=True, line_shape='spline')
                fig_s.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', hovermode='x unified', xaxis_title="Fechas de Finalización", yaxis_title="Tareas Completadas",
                                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                fig_s.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#E2E8F0')
                fig_s.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#E2E8F0')
                st.plotly_chart(fig_s, use_container_width=True)
                
            with tab3:
                df_hist = final[final['IsRain']==True].copy()
                if not df_hist.empty:
                    df_hist['Mes'] = pd.to_datetime(df_hist['Inicio Nuevo']).dt.month_name()
                    counts_mes = df_hist['Mes'].value_counts().reset_index()
                    counts_mes.columns = ['Mes', 'Qty']
                    
                    fig_riesgo = px.bar(counts_mes, x='Mes', y='Qty', text='Qty', color_discrete_sequence=['#3B82F6'])
                    
                    fig_riesgo.update_traces(textposition='outside')
                    fig_riesgo.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title=None, yaxis_title="Cantidad de Tareas Afectadas")
                    fig_riesgo.update_yaxes(showgrid=True, gridcolor='#E2E8F0')
                    st.plotly_chart(fig_riesgo, use_container_width=True)
                else: st.info("Ninguna actividad superó los umbrales de lluvia seleccionados.")
                
            with tab4:
                df_pareto = final[final['IsSummary'] == False].sort_values('Días Impacto', ascending=False)
                gb = GridOptionsBuilder.from_dataframe(df_pareto[['ID', 'WBS', 'Actividad', 'Días Impacto', 'Tr (Secado/Horas)', 'Holgura (Días)', 'Ruta Crítica', 'Estado']])
                gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
                gb.configure_default_column(resizable=True, filterable=True, sortable=True)
                gb.configure_column("Actividad", width=400)
                gb.configure_column("Estado", width=350)
                gridOptions = gb.build()
                
                st.markdown("*(Puedes dar clic en los encabezados para filtrar o mover las columnas)*")
                AgGrid(df_pareto[['ID', 'WBS', 'Actividad', 'Días Impacto', 'Tr (Secado/Horas)', 'Holgura (Días)', 'Ruta Crítica', 'Estado']], 
                       gridOptions=gridOptions, 
                       theme='alpine',
                       columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
                       update_mode=GridUpdateMode.NO_UPDATE)

            # --- EXPORTAR EXCEL ---
            b_out = io.BytesIO()
            p_name = st.session_state.get('project_name', 'Proyecto')
            safe_name = "".join([c for c in p_name if c.isalnum() or c in (' ', '_')]).strip()
            
            # REQUISITO 3: Ajustamos columnas a exportar (agregamos Tr y quitamos Nivel Riesgo subjetivo)
            columnas_exportar = ['ID', 'WBS', 'Actividad', 'Duración Base', 'Inicio Base', 'Fin Base', 
                                 'Duración Nueva', 'Inicio Nuevo', 'Fin Nuevo', 'Tr (Secado/Horas)', 'Pred. Orig', 'Pred. Nueva', 
                                 'Prob. Lluvia', 'mm Lluvia Max', 'Lluvia Total Acum (mm)', 'Fecha Última Lluvia', 
                                 'Días Impacto', 'Estado', 'Holgura (Días)', 'Ruta Crítica']
            
            with pd.ExcelWriter(b_out, engine='xlsxwriter') as w:
                final[columnas_exportar].to_excel(w, index=False, sheet_name="Sugerencias", startrow=1)
                wb = w.book
                ws = w.sheets['Sugerencias']
                
                fmt_title = wb.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#1E293B', 'font_color': 'white', 'font_size': 14})
                fmt_norm = wb.add_format({'border':1})
                fmt_date = wb.add_format({'num_format': 'mm-dd-yyyy', 'border':1})
                fmt_med = wb.add_format({'bg_color': '#DBEAFE', 'border':1, 'font_color': 'black'}) 
                fmt_med_date = wb.add_format({'bg_color': '#DBEAFE', 'num_format': 'mm-dd-yyyy', 'border':1, 'font_color': 'black'})
                fmt_high = wb.add_format({'bg_color': '#0F172A', 'border':1, 'font_color': 'white'}) 
                fmt_high_date = wb.add_format({'bg_color': '#0F172A', 'num_format': 'mm-dd-yyyy', 'border':1, 'font_color': 'white'})
                fmt_logic = wb.add_format({'bg_color': '#FEF08A', 'border':1}) 
                fmt_logic_date = wb.add_format({'bg_color': '#FEF08A', 'num_format': 'mm-dd-yyyy', 'border':1})
                fmt_summary = wb.add_format({'bold': True, 'bg_color': '#F1F5F9', 'border':1})
                fmt_summary_date = wb.add_format({'bold': True, 'bg_color': '#F1F5F9', 'num_format': 'mm-dd-yyyy', 'border':1})

                last_col_idx = len(columnas_exportar) - 1 
                ws.merge_range(0, 0, 0, last_col_idx, f"REPORTE: {safe_name} | {st.session_state['ubicacion_nombre']}", fmt_title)
                
                date_cols = [4, 5, 7, 8]
                rain_date_col = 15
                
                for r, row in final.iterrows():
                    impacto = row['Días Impacto']
                    is_logic = row['IsLogic']
                    is_summary = row['IsSummary']
                    
                    row_fmt = fmt_norm
                    row_date_fmt = fmt_date
                    
                    if is_summary:
                        row_fmt = fmt_summary
                        row_date_fmt = fmt_summary_date
                    elif impacto > 2:
                        row_fmt = fmt_high
                        row_date_fmt = fmt_high_date
                    elif impacto > 0:
                        row_fmt = fmt_med
                        row_date_fmt = fmt_med_date
                    elif is_logic: 
                        row_fmt = fmt_logic
                        row_date_fmt = fmt_logic_date
                        
                    for c, col_name in enumerate(columnas_exportar):
                        val = row.get(col_name, "")
                        if pd.isna(val): val = ""
                        cell_fmt = row_date_fmt if (c in date_cols or c == rain_date_col) else row_fmt
                        ws.write(r+2, c, val, cell_fmt)
                
                ws.set_column('C:C', 40); ws.set_column('R:R', 35)

                ws_data = wb.add_worksheet('Datos_Graficos')
                ws_data.write('A1', 'Fecha')
                ws_data.write('B1', 'Acumulado Base')
                ws_data.write('C1', 'Acumulado Sugerido')
                
                df_s_excel = df_s.pivot_table(index='Fecha', columns='Tipo', values='Acumulado', aggfunc='max').ffill().fillna(0).reset_index()
                if 'Base' not in df_s_excel.columns: df_s_excel['Base'] = 0
                if 'Sugerido' not in df_s_excel.columns: df_s_excel['Sugerido'] = 0
                
                if not df_s_excel.empty:
                    for i, r in df_s_excel.iterrows():
                        date_val = r['Fecha']
                        if isinstance(date_val, pd.Timestamp): date_val = date_val.date()
                        ws_data.write(i+1, 0, date_val.strftime('%Y-%m-%d'))
                        ws_data.write(i+1, 1, r['Base'])
                        ws_data.write(i+1, 2, r['Sugerido'])
                
                ws_data.write('E1', 'Mes')
                ws_data.write('F1', 'Cantidad')
                if not df_hist.empty:
                    counts = df_hist['Mes'].value_counts().reset_index()
                    counts.columns = ['Mes', 'Qty']
                    for i, r in counts.iterrows():
                        ws_data.write(i+1, 4, r['Mes'])
                        ws_data.write(i+1, 5, r['Qty'])

                chart_sheet1 = wb.add_chartsheet('Grafico_Curva_S')
                chart1 = wb.add_chart({'type': 'line'})
                max_row = len(df_s_excel)
                if max_row > 0:
                    chart1.add_series({
                        'name': 'Plan Base',
                        'categories': ['Datos_Graficos', 1, 0, max_row, 0],
                        'values':     ['Datos_Graficos', 1, 1, max_row, 1],
                        'line':       {'color': 'gray'}
                    })
                    chart1.add_series({
                        'name': 'Con Lluvia',
                        'categories': ['Datos_Graficos', 1, 0, max_row, 0],
                        'values':     ['Datos_Graficos', 1, 2, max_row, 2],
                        'line':       {'color': 'blue'}
                    })
                chart1.set_title({'name': 'Curva S de Avance (Solo Tareas de Trabajo)'})
                chart_sheet1.set_chart(chart1)

                if not df_hist.empty:
                    chart_sheet2 = wb.add_chartsheet('Grafico_Barras')
                    chart2 = wb.add_chart({'type': 'column'})
                    max_row_h = len(counts)
                    chart2.add_series({
                        'name': 'Actividades Afectadas',
                        'categories': ['Datos_Graficos', 1, 4, max_row_h, 4],
                        'values':     ['Datos_Graficos', 1, 5, max_row_h, 5],
                        'fill':       {'color': '#AF1E2D'}
                    })
                    chart2.set_title({'name': 'Riesgo por Mes'})
                    chart_sheet2.set_chart(chart2)

            st.download_button("📥 Descargar Reporte Gerencial Completo (Excel)", b_out.getvalue(), f"Reporte_Climatico_{safe_name}.xlsx", "application/vnd.ms-excel", type="primary", use_container_width=True)
