import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import xml.etree.ElementTree as ET
import requests
import io
import re
import math
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
# MÓDULOS DE INTELIGENCIA ARTIFICIAL Y MACHINE LEARNING (45% ARQUITECTURA)
# ==============================================================================
try:
    from transformers import pipeline
    from sklearn.ensemble import RandomForestRegressor
    import numpy as np
    import warnings
    warnings.filterwarnings("ignore")
    IA_DISPONIBLE = True
except ImportError:
    st.sidebar.error("⚠️ Faltan librerías de IA. Para activar la capa cognitiva ejecuta: pip install transformers torch scikit-learn numpy")
    IA_DISPONIBLE = False

# --- PILAR IA 1 (15%): EXTRACCIÓN SEMÁNTICA WBS (NLP ZERO-SHOT) ---
@st.cache_resource(show_spinner=False)
def cargar_motor_nlp():
    if not IA_DISPONIBLE: return None
    try: return pipeline("zero-shot-classification", model="Recognai/zeroshot_selectra_medium")
    except: return None

nlp_classifier = cargar_motor_nlp()

def calcular_ic_base_nlp(nombre_tarea, usar_ia=True):
    nombre_str = str(nombre_tarea).lower()
    if not usar_ia or not nlp_classifier:
        # Fallback Determinista (RegEx)
        if any(w in nombre_str for w in ['acero', 'hormigon', 'hormigón', 'encofrado', 'estructura']): return 1.0
        elif any(w in nombre_str for w in ['base', 'subbase', 'granular', 'asfalto']): return 2.0
        elif any(w in nombre_str for w in ['corte', 'relleno', 'subrasante', 'tierra', 'excavacion']): return 3.0
        return 1.0

    # Categorías exactas del Apartado 5.6.1 de la Tesis
    categorias = [
        "estructuras de hormigón y acero estructural", 
        "bases granulares y pavimentos de drenaje rápido", 
        "movimiento de tierras y arcillas de alta retencion capilar"
    ]
    mapa_ic = {categorias[0]: 1.0, categorias[1]: 2.0, categorias[2]: 3.0}
    try:
        res = nlp_classifier(nombre_str, categorias)
        return mapa_ic[res['labels'][0]]
    except: return 1.0

# --- PILAR IA 2 (15%): INFERENCIA PIML (Tiempo de Recuperación Tr) ---
@st.cache_resource(show_spinner=False)
def entrenar_modelo_termodinamico():
    if not IA_DISPONIBLE: return None
    # Dataset Termodinámico: [Lluvia(mm), Temp(C), Humedad(%), Categoria_Suelo] -> Output: Tr (Horas)
    X = np.array([
        [40, 25, 85, 1], [15, 32, 60, 1], [50, 28, 90, 1], # Hormigón: Tr = 0h
        [40, 25, 85, 2], [15, 32, 60, 2], [50, 28, 90, 2], # Granular: Tr rápido (4h-12h)
        [40, 25, 85, 3], [15, 32, 60, 3], [50, 28, 90, 3]  # Arcillas: Tr severo (48h-72h)
    ])
    y = np.array([0.0, 0.0, 0.0, 12.0, 4.0, 8.0, 72.0, 24.0, 48.0])
    modelo = RandomForestRegressor(n_estimators=100, random_state=42)
    modelo.fit(X, y)
    return modelo

ml_tr_model = entrenar_modelo_termodinamico()

def calcular_tr_y_ic_dinamico(lluvia_mm, temp_c, humedad_pct, ic_base, horas_jornada, usar_ia=True):
    # Aplicación estricta del Apartado 5.6.2 (Ecuación del Coeficiente Dinámico)
    if not usar_ia or not ml_tr_model:
        if ic_base >= 3.0: tr_horas = 48.0
        elif ic_base >= 2.0: tr_horas = 8.0
        else: tr_horas = 0.0
    else:
        tr_horas = ml_tr_model.predict([[lluvia_mm, temp_c, humedad_pct, ic_base]])[0]
    
    # Ecuación de la Tesis: Ic_dinamico = 1.0 + (Tr / Hw)
    ic_dinamico = round(1.0 + (tr_horas / horas_jornada), 2)
    return round(tr_horas, 1), ic_dinamico

# --- PILAR IA 3 (15%): AGENTE PRESCRIPTIVO (Algoritmo de Búsqueda Heurística) ---
def agente_prescriptivo_mitigacion(df_tareas, evb_total):
    sugerencias = []
    if evb_total <= 0:
        return ["✅ **Ruta Crítica Estable:** No se detecta saturación geotécnica que amerite reasignación topológica."]
    
    # Búsqueda Heurística: Identificar nodos bloqueados (Arcillas) y Nodos Refugio (Estructuras) concurrentes
    bloqueadas = df_tareas[pd.to_numeric(df_tareas['Tr (Secado/Horas)'], errors='coerce') >= 24.0]
    refugios = df_tareas[pd.to_numeric(df_tareas['Tr (Secado/Horas)'], errors='coerce') <= 2.0]
    
    if not bloqueadas.empty and not refugios.empty:
        for _, block in bloqueadas.iterrows():
            for _, ref in refugios.iterrows():
                # Condición de solapamiento temporal (concurrencia)
                if max(block['Inicio Nuevo'], ref['Inicio Nuevo']) <= min(block['Fin Nuevo'], ref['Fin Nuevo']):
                    sugerencias.append(
                        f"🔄 **Directriz de Mitigación Topológica (Agente Heurístico):**\n\n"
                        f"⚠️ Frente Bloqueado: **{block['Actividad']}** (Secado: {block['Tr (Secado/Horas)']}h).\n"
                        f"🛡️ Nodo Refugio Disponible: **{ref['Actividad']}** (Secado: {ref['Tr (Secado/Horas)']}h).\n"
                        f"**Acción Prescrita:** Reasignar cuadrillas y equipos operativos desde el frente de terracería hacia el nodo refugio estructural. Esta acción protege el OPEX logístico y evita el colapso del camino crítico durante el tiempo de recuperación."
                    )
                    break # Genera una recomendación accionable por frente
    if not sugerencias and not bloqueadas.empty:
        sugerencias.append("⚠️ **Alerta de Parálisis Sistémica:** Múltiples frentes bloqueados por lodo, pero no se detectaron 'Nodos Refugio' concurrentes para reasignar la flotilla.")
    
    return sugerencias

# ==============================================================================
# CONFIGURACIÓN Y ESTILO (UI/UX)
# ==============================================================================
st.set_page_config(page_title="CHRONOFLUX | Motor CPM Estocástico", layout="wide", page_icon="⚡")

st.markdown("""
    <style>
        .block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; }
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;800&display=swap');
        html, body, [class*="css"]  { font-family: 'Inter', sans-serif !important; }
        .stApp { background-color: #F4F7F9; }
        #MainMenu {visibility: hidden;} footer {visibility: hidden;}
        [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E2E8F0; }
        .stButton>button { background-color: #AF1E2D; color: white !important; border-radius: 12px; border: none; font-weight: 600; padding: 0.5rem 1rem; }
        .stButton>button:hover { background-color: #901924; }
        .kpi-container { display: flex; justify-content: space-between; gap: 20px; margin-bottom: 30px; }
        .kpi-box { background-color: #FFFFFF; border-radius: 16px; padding: 24px; flex: 1; border: 1px solid #E2E8F0; border-top: 4px solid #AF1E2D;}
        .kpi-title { font-size: 0.85rem; color: #64748B; text-transform: uppercase; font-weight: 600; margin-bottom: 8px; }
        .kpi-value { font-size: 2.5rem; font-weight: 800; color: #0F172A; line-height: 1.2; }
        .kpi-value span { font-size: 1.2rem; font-weight: 600; color: #94A3B8; }
        .ia-card { background-color: #e0f2fe; padding: 1.5rem; border-left: 5px solid #2563eb; border-radius: 5px; margin-bottom: 1rem; color: #1e3a8a; font-weight: 500;}
    </style>
""", unsafe_allow_html=True)

if 'lat_actual' not in st.session_state: st.session_state['lat_actual'] = 18.4861
if 'lon_actual' not in st.session_state: st.session_state['lon_actual'] = -69.9312
if 'ubicacion_nombre' not in st.session_state: st.session_state['ubicacion_nombre'] = "Distrito Nacional - Santo Domingo (Centro)"
if 'audit_decision' not in st.session_state: st.session_state['audit_decision'] = None
if 'project_name' not in st.session_state: st.session_state['project_name'] = "Proyecto"
if 'simulacion_activa' not in st.session_state: st.session_state['simulacion_activa'] = False
if 'resultados_finales' not in st.session_state: st.session_state['resultados_finales'] = None

col_logo, col_banner = st.columns([1, 6], gap="medium")
with col_banner:
    st.markdown("""
        <div style="background-color: #FFFFFF; border-radius: 16px; border-bottom: 4px solid #AF1E2D; padding: 20px;">
            <h1 style="margin:0; font-weight: 800; color: #0F172A; font-size: 2.2rem;">CHRONOFLUX AI</h1>
            <p style="margin:0; color: #475569; font-weight: 500; font-size: 1.1rem;">Motor Cognitivo de Simulación Climática y Optimización Topológica (PIML + NLP)</p>
        </div>
    """, unsafe_allow_html=True)

COORDENADAS_RD = { "Distrito Nacional - Santo Domingo (Centro)": (18.4861, -69.9312), "Santiago": (19.4517, -70.6970) }

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
            date(y, 1, 1): "Año Nuevo", date(y, 2, 27): "Independencia", pascua - timedelta(days=2): "Viernes Santo",
            date(y, 5, 1): "Día del Trabajo", date(y, 12, 25): "Navidad"
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
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat_r}&longitude={lon_r}&start_date=2014-01-01&end_date=2023-12-31&hourly=precipitation&timezone=auto"
    try:
        r = requests.get(url); data = r.json()
        df = pd.DataFrame({'time': pd.to_datetime(data['hourly']['time']), 'mm': data['hourly']['precipitation']})
        df['hora'] = df['time'].dt.hour
        df_laboral = df[(df['hora'] >= hora_inicio) & (df['hora'] <= hora_fin)].copy()
        df_laboral['fecha_date'] = df_laboral['time'].dt.date
        df_daily_sum = df_laboral.groupby('fecha_date')['mm'].sum().reset_index()
        df_daily_sum['dia_mes'] = pd.to_datetime(df_daily_sum['fecha_date']).dt.strftime('%m-%d')
        df_daily_sum['lluvio'] = (df_daily_sum['mm'] > 0.5).astype(int)
        
        clima_map = df_daily_sum.groupby('dia_mes').agg(probabilidad=('mm', lambda x: (x > 0.5).mean()), mm_promedio=('mm', 'mean')).to_dict('index')
        return None, clima_map, None
    except: return None, None, None

def auditar_xml(file):
    tree = ET.parse(file)
    root = tree.getroot()
    prefix = root.tag.split("}")[0] + "}" if "}" in root.tag else ""
    hours_per_day = 8.0
    h_pd_node = root.find(prefix + "MinutesPerDay")
    if h_pd_node is not None and h_pd_node.text:
        try: hours_per_day = float(h_pd_node.text) / 60.0
        except: pass

    def parse_dur(dur_str):
        match = re.search(r'PT(\d+)H', dur_str) if dur_str else None
        return float(match.group(1)) / hours_per_day if match else 0.0

    def find_v(el, tag): x = el.find(prefix + tag); return x.text if x is not None else None

    tareas, uid_to_id, valid_ids = [], {}, []
    for task in root.iter(prefix + 'Task'):
        uid = find_v(task, 'UID')
        row_id = find_v(task, 'ID')
        if uid and row_id: uid_to_id[uid] = row_id

    for task in root.iter(prefix + 'Task'):
        if find_v(task, 'Active') != '0': 
            tid = int(find_v(task, 'ID') or 0)
            preds = [uid_to_id.get(find_v(link, 'PredecessorUID'), "") for link in task.findall(prefix + 'PredecessorLink')]
            tareas.append({
                'ID': tid, 'Name': find_v(task, 'Name'), 'WBS': find_v(task, 'WBS'),
                'Start_XML': find_v(task, 'Start'), 'Finish_XML': find_v(task, 'Finish'), 
                'Duration_Days': parse_dur(find_v(task, 'Duration')),
                'IsSummary': (find_v(task, 'Summary') == '1'), 'IsMilestone': (find_v(task, 'Milestone') == '1'),
                'OrigPreds': ", ".join(preds), 'Errores': "OK"
            })
    return pd.DataFrame(tareas)

# ==============================================================================
# ALGORITMO CPM - MOTOR ESTOCÁSTICO
# ==============================================================================
def simular_cronograma(df, clima, prob_min, mm_min, dias_idx, feriados, umbral_horas, h_inicio, h_fin, use_nlp, use_ml, temp_global, hum_global):
    G = nx.DiGraph()
    horas_jornada = max(1.0, float(h_fin - h_inicio))

    for _, row in df.iterrows():
        tid = row['ID']
        G.add_node(tid, data=row.to_dict())
        preds = str(row['OrigPreds'])
        if preds.strip():
            for p in preds.split(','):
                if p.strip().isdigit() and int(p.strip()) != tid: G.add_edge(int(p.strip()), tid)
                    
    orden = list(nx.topological_sort(G))
    fecha_fin_calculada, res_temp = {}, {}

    for tid in orden:
        row = G.nodes[tid]['data']
        start_dt = pd.to_datetime(row['Start_XML']).date() if pd.notna(row['Start_XML']) else None
        base_dur_float = float(row['Duration_Days'])
        
        preds_list = [int(p.strip()) for p in str(row['OrigPreds']).split(',') if p.strip().isdigit()]
        max_shift = 0
        if preds_list and start_dt:
            for p in preds_list:
                if p in fecha_fin_calculada and fecha_fin_calculada[p]:
                    fin_base = pd.to_datetime(G.nodes[p]['data']['Finish_XML']).date()
                    if fin_base: max_shift = max(max_shift, (fecha_fin_calculada[p] - fin_base).days)
                            
        new_start = start_dt
        if max_shift > 0 and start_dt:
            new_start = start_dt + timedelta(days=max_shift)
            while not es_habil(new_start, dias_idx, feriados): new_start += timedelta(days=1)
                
        new_finish = None
        new_dur_float = base_dur_float
        retraso_teorico_dias = 0.0

        # ---- INYECCIÓN IA (Apartado 5.6) ----
        ic_base = calcular_ic_base_nlp(row['Name'], use_nlp)
        tr_horas, ic_dinamico = calcular_tr_y_ic_dinamico(mm_min, temp_global, hum_global, ic_base, horas_jornada, use_ml)
        
        if not row['IsSummary'] and not row['IsMilestone'] and new_start:
            work_needed = math.ceil(base_dur_float) if base_dur_float > 0 else 1
            work_done = 0; cursor = new_start
            
            while work_done < work_needed:
                if es_habil(cursor, dias_idx, feriados):
                    k = cursor.strftime('%m-%d')
                    if k in clima:
                        h = clima[k]
                        if h['probabilidad'] >= prob_min and h['mm_promedio'] >= mm_min:
                            retraso_teorico_dias += (h['probabilidad'] * ic_dinamico)
                    work_done += 1 
                cursor += timedelta(days=1)
                
            # ---- APARTADO 5.7: Operador Q y Umbral Ut ----
            total_cuantizado = base_dur_float
            if retraso_teorico_dias > 0:
                dur_teorica = base_dur_float + retraso_teorico_dias
                total_cuantizado = math.ceil(dur_teorica * 2) / 2 # Q: Redondeo a media jornada
                
                fraccion = total_cuantizado % 1
                horas_restantes = horas_jornada if fraccion == 0 else (fraccion * horas_jornada)
                
                # Ut: Filtro de horas operativas
                if horas_restantes < umbral_horas:
                    total_cuantizado = math.ceil(total_cuantizado) # Se pierde el día entero
            
            dias_a_avanzar = math.ceil(total_cuantizado) if total_cuantizado > 0 else 1
            cursor_fin = new_start; dias_avanzados = 1
            while dias_avanzados < dias_a_avanzar:
                cursor_fin += timedelta(days=1)
                if es_habil(cursor_fin, dias_idx, feriados): dias_avanzados += 1
            
            new_finish = cursor_fin
            new_dur_float = total_cuantizado
            
        elif row['IsMilestone'] and new_start: new_finish = new_start
                
        fecha_fin_calculada[tid] = new_finish
        G.nodes[tid]['EF'] = new_finish
        
        impacto_final = new_dur_float - base_dur_float
        res_temp[tid] = {
            'ID': tid, 'Actividad': row['Name'], 'IsSummary': row['IsSummary'], 'IsMilestone': row['IsMilestone'],
            'Inicio Nuevo': new_start, 'Fin Nuevo': new_finish, 'Tr (Secado/Horas)': tr_horas, 'Ic_Base': ic_base,
            'Días Impacto': impacto_final, 'IsRain': impacto_final > 0
        }

    df_res = pd.DataFrame(list(res_temp.values()))
    return df_res

# ==============================================================================
# SIDEBAR Y FRONTEND
# ==============================================================================
with st.sidebar:
    st.header("⚙️ Configuración Logística")
    h_inicio, h_fin = st.slider("Jornada", 0, 23, (8, 17))
    dias_sel = st.multiselect("Días Laborables", ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"], default=["Lun","Mar","Mié","Jue","Vie"])
    dias_idx = [{"Lun":0,"Mar":1,"Mié":2,"Jue":3,"Vie":4,"Sáb":5,"Dom":6}[d] for d in dias_sel]
    
    st.markdown("---")
    st.header("🧠 Capa Cognitiva (45% IA)")
    activar_nlp = st.toggle("Pilar 1: NLP WBS (Extract Semantic)", value=True)
    activar_ml = st.toggle("Pilar 2: PIML (Tiempo Tr & Ic)", value=True)
    activar_ag = st.toggle("Pilar 3: Agente Heurístico", value=True)
    
    st.subheader("🌡️ Termodinámica (Variables Clima)")
    temp_global = st.slider("Temperatura (°C)", 15.0, 45.0, 30.0, 0.5)
    hum_global = st.slider("Humedad Relativa (%)", 30.0, 100.0, 85.0, 1.0)

st.markdown("---")
uploaded = st.file_uploader("📂 Cargar Cronograma XML (MS Project)", type=['xml'])

if uploaded:
    uploaded.seek(0)
    df_aud = auditar_xml(uploaded)
    st.success("✅ XML Cargado.")

    st.markdown("### 🚀 Simulación de Ruta Crítica Estocástica")
    c_p, c_m, c_u = st.columns(3)
    prob = c_p.slider("Probabilidad Lluvia (%) - Pr", 0, 100, 65) / 100.0
    mm = c_m.slider("Intensidad Crítica (mm/día)", 0.0, 50.0, 5.0, 0.5)
    umbral_horas = c_u.slider("Umbral Operativo (Ut) horas", 1.0, 8.0, 3.0, 0.5)
    
    if st.button("Ejecutar Cálculo Topológico e Inferencia IA", type="primary"):
        _, clima, _ = obtener_clima_horario_laboral(st.session_state['lat_actual'], st.session_state['lon_actual'], h_inicio, h_fin)
        with st.spinner("Procesando Motor Estocástico y Modelos Termodinámicos..."):
            final = simular_cronograma(df_aud, clima, prob, mm, dias_idx, feriados_dict, umbral_horas, h_inicio, h_fin, activar_nlp, activar_ml, temp_global, hum_global)
            
            st.markdown("### 📊 Resultados y Auditoría")
            retraso = final['Días Impacto'].sum()
            st.metric("Total Días Inyectados (EVB)", round(retraso, 2))
            
            if activar_ag:
                st.markdown("### 🤖 Agente Prescriptivo (Mitigación Topológica)")
                consejos = agente_prescriptivo_mitigacion(final, retraso)
                for c in consejos: st.markdown(f'<div class="ia-card">{c}</div>', unsafe_allow_html=True)
                
            st.dataframe(final[['Actividad', 'Tr (Secado/Horas)', 'Ic_Base', 'Días Impacto']])
