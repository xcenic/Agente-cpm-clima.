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
    st.sidebar.error("⚠️ Faltan librerías de IA. Para activar la capa cognitiva ejecuta: pip install transformers torch scikit-learn numpy")
    IA_DISPONIBLE = False

# --- MOTOR IA 1: NLP ---
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

# --- MOTOR IA 2: ML Tr ---
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

# --- MOTOR IA 3: AGENTE PRESCRIPTIVO ---
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
# FUNCIONES DE SOPORTE Y DATOS
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
    # API Actualizada: Ahora extrae precipitation, temperature_2m y relative_humidity_2m
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
        
        # Agrupación diaria: sumamos lluvia, promediamos temperatura y humedad
        df_daily = df_laboral.groupby('fecha_date').agg(
            mm=('mm', 'sum'),
            temp=('temp', 'mean'),
            hum=('hum', 'mean')
        ).reset_index()
        
        df_daily['dia_mes'] = pd.to_datetime(df_daily['fecha_date']).dt.strftime('%m-%d')
        df_daily['fecha_full'] = pd.to_datetime(df_daily['fecha_date'])
        df_daily['lluvio'] = (df_daily['mm'] > 0.5).astype(int)
        
        # Mapa para simulación CPM
        clima_map = df_daily.groupby('dia_mes').agg(
            probabilidad=('lluvio', 'mean'), 
            mm_promedio=('mm', 'mean'),
            ultima_fecha_lluvia=('fecha_full', lambda x: x[df_daily.loc[x.index, 'mm'] > 0.5].max() if (df_daily.loc[x.index, 'mm'] > 0.5).any() else None)
        ).to_dict('index')
        
        # Agrupación Mensual para los Gráficos de Interfaz
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
        
        /* Estilos generales de botones */
        .stButton>button { background-color: #AF1E2D; color: white !important; border-radius: 8px; border: none; transition: all 0.3s ease; font-weight: 600; padding: 0.5rem 1rem; box-shadow: 0 4px 6px -1px rgba(175, 30, 45, 0.2); }
        .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(175, 30, 45, 0.3); background-color: #901924; }
        
        /* Estilo minimalista para el botón de descarga del manual en el sidebar */
        [data-testid="stSidebar"] .stDownloadButton > button {
            background-color: #64748B !important;
            color: #FFFFFF !important;
            border: 1px solid #475569 !important;
            border-radius: 6px !important;
            font-weight: 500 !important;
            font-size: 0.9rem !important;
            width: 100% !important;
            box-shadow: none !important;
            transition: background-color 0.2s ease !important;
            margin-top: 20px;
        }
        [data-testid="stSidebar"] .stDownloadButton > button:hover {
            background-color: #475569 !important;
            border-color: #334155 !important;
        }

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

if 'lat_actual' not in st.session_state: st.session_state['lat_actual'] = 18.4861
if 'lon_actual' not in st.session_state: st.session_state['lon_actual'] = -69.9312
if 'ubicacion_nombre' not in st.session_state: st.session_state['ubicacion_nombre'] = "Distrito Nacional - Santo Domingo (Centro)"
if 'audit_decision' not in st.session_state: st.session_state['audit_decision'] = None
if 'project_name' not in st.session_state: st.session_state['project_name'] = "Proyecto"
if 'simulacion_activa' not in st.session_state: st.session_state['simulacion_activa'] = False
if 'resultados_finales' not in st.session_state: st.session_state['resultados_finales'] = None

# ==============================================================================
# INTERFAZ PRINCIPAL Y BARRA LATERAL
# ==============================================================================
with st.sidebar:
    st.header("⚙️ Configuración Logística")
    st.subheader("1. Horario de Obra")
    h_inicio, h_fin = st.slider("Jornada", 0, 23, (8, 17))
    st.subheader("2. Días Laborables")
    dias_sel = st.multiselect("Seleccionar:", ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"], default=["Lun","Mar","Mié","Jue","Vie"])
    mapa_d = {"Lun":0,"Mar":1,"Mié":2,"Jue":3,"Vie":4,"Sáb":5,"Dom":6}
    dias_idx = [mapa_d[d] for d in dias_sel]
    
    st.markdown("---")
    st.header("🧠 Capa Cognitiva e Inteligencia Artificial")
    activar_nlp = st.toggle("Procesamiento de Lenguaje Natural (Clasificación Semántica)", value=True)
    activar_ml = st.toggle("Motor Random Forest (Tiempo de Recuperación Tr)", value=True)
    activar_ag = st.toggle("Agente Prescriptivo (Mitigación Topológica)", value=True)
    
    st.markdown("---")
    st.subheader("🌡️ Termodinámica (Variables de Inferencia Continua)")
    temp_global = st.slider("Temperatura Ambiente (°C)", 15.0, 45.0, 30.0, 0.5, help="Variable predictora para el cálculo de evaporación en el Random Forest.")
    hum_global = st.slider("Humedad Relativa (%)", 30.0, 100.0, 85.0, 1.0, help="Déficit de presión de vapor para modelar el secado del estrato geotécnico.")

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
            help="Descarga el manual operativo y de blindaje forense en formato PDF."
        )
    except FileNotFoundError:
        st.download_button(
            label="📄 Descargar Manual de usuario",
            data=b"Archivo no encontrado",
            file_name="error.txt",
            use_container_width=True,
            disabled=True,
            help="Coloque el archivo CHRONOFLUX_USER_MANUAL.pdf en la raíz de la aplicación."
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
        "shape": {"type": "circle"},
        "opacity": {"value": 0.3, "random": false},
        "size": {"value": 3, "random": true},
        "line_linked": {"enable": true, "distance": 150, "color": "#38BDF8", "opacity": 0.4, "width": 1.5},
        "move": {"enable": true, "speed": 1.5, "direction": "none", "random": false, "straight": false, "out_mode": "out", "bounce": false}
      },
      "interactivity": {
        "detect_on": "canvas",
        "events": {
          "onhover": {"enable": true, "mode": "grab"},
          "onclick": {"enable": true, "mode": "push"},
          "resize": true
        },
        "modes": {
          "grab": {"distance": 140, "line_linked": {"opacity": 1}},
          "push": {"particles_nb": 3}
        }
      },
      "retina_detect": true
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

st.selectbox("📍 Buscar Ubicación de Proyecto:", sorted(list(COORDENADAS_RD.keys())), key='combo_ubicacion', on_change=actualizar_desde_dropdown)
st.markdown(f"**Coordenadas de Análisis:** `Latitud: {st.session_state['lat_actual']:.4f}, Longitud: {st.session_state['lon_actual']:.4f}`")

m = folium.Map(location=[st.session_state['lat_actual'], st.session_state['lon_actual']], zoom_start=12)
m.add_child(folium.LatLngPopup()) 
folium.Marker([st.session_state['lat_actual'], st.session_state['lon_actual']], popup=st.session_state['ubicacion_nombre'], icon=folium.Icon(color='red', icon='info-sign')).add_to(m)
map_data = st_folium(m, height=450, use_container_width=True, key="mapa_folium")

if map_data and map_data.get("last_clicked"):
    lat_c = map_data["last_clicked"]["lat"]; lon_c = map_data["last_clicked"]["lng"]
    if round(lat_c, 4) != round(st.session_state['lat_actual'], 4) or round(lon_c, 4) != round(st.session_state['lon_actual'], 4):
        st.session_state['lat_actual'] = lat_c; st.session_state['lon_actual'] = lon_c
        st.session_state['ubicacion_nombre'] = f"Pin Manual: {lat_c:.4f}, {lon_c:.4f}"
        st.rerun()

st.markdown("---")

# ==============================================================================
# GRÁFICA CLIMÁTICA Y RADAR
# ==============================================================================
st.subheader(f"🌦️ Comportamiento Climático Histórico ({st.session_state['ubicacion_nombre']})")
with st.spinner("Accediendo al caché geoespacial o descargando micro-clima (Lluvia, Temp, Humedad)..."):
    df_g, clima, orden = obtener_clima_horario_laboral(st.session_state['lat_actual'], st.session_state['lon_actual'], h_inicio, h_fin)
    if df_g is not None:
        tab_precip, tab_temp, tab_hum = st.tabs(["🌧️ Lluvia (mm)", "🌡️ Temperatura (°C)", "💧 Humedad (%)"])
        
        with tab_precip:
            fig_clima = px.bar(df_g, x='Mes', y='mm', text='mm', 
                               color='mm', color_continuous_scale=px.colors.sequential.Blues,
                               hover_data={'prob_lluvia': ':.1%'},
                               labels={'mm': 'Lluvia Promedio (mm/día)', 'prob_lluvia': 'Probabilidad de Lluvia'})
            fig_clima.update_traces(texttemplate='%{text:.1f}', textposition='outside', marker_line_color='rgba(0,0,0,0)', opacity=0.9)
            fig_clima.update_layout(coloraxis_showscale=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', yaxis=dict(showgrid=True, gridcolor='#E2E8F0'), xaxis_title=None, height=400)
            st.plotly_chart(fig_clima, use_container_width=True)
            
        with tab_temp:
            fig_temp = px.bar(df_g, x='Mes', y='temp', text='temp',
                              color='temp', color_continuous_scale=px.colors.sequential.Oranges,
                              labels={'temp': 'Temp Promedio (°C)'})
            fig_temp.update_traces(texttemplate='%{text:.1f}°', textposition='outside', marker_line_color='rgba(0,0,0,0)', opacity=0.9)
            fig_temp.update_layout(coloraxis_showscale=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', yaxis=dict(showgrid=True, gridcolor='#E2E8F0'), xaxis_title=None, height=400)
            st.plotly_chart(fig_temp, use_container_width=True)
            
        with tab_hum:
            fig_hum = px.bar(df_g, x='Mes', y='hum', text='hum',
                             color='hum', color_continuous_scale=px.colors.sequential.Teal,
                             labels={'hum': 'Humedad Relativa Promedio (%)'})
            fig_hum.update_traces(texttemplate='%{text:.1f}%', textposition='outside', marker_line_color='rgba(0,0,0,0)', opacity=0.9)
            fig_hum.update_layout(coloraxis_showscale=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', yaxis=dict(showgrid=True, gridcolor='#E2E8F0', range=[0, 100]), xaxis_title=None, height=400)
            st.plotly_chart(fig_hum, use_container_width=True)

st.markdown("---")
st.subheader(f"📡 Radar Satelital en Tiempo Real ({st.session_state['ubicacion_nombre']})")
windy_html = f"""
<iframe width="100%" height="450" 
    src="https://embed.windy.com/embed.html?type=map&location=coordinates&metricRain=mm&metricTemp=°C&metricWind=km/h&zoom=9&overlay=rain&product=ecmwf&level=surface&lat={st.session_state['lat_actual']}&lon={st.session_state['lon_actual']}" 
    frameborder="0" style="border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
</iframe>
"""
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
        
        c_p, c_m, c_u = st.columns(3)
        prob = c_p.slider("Probabilidad de Lluvia (%) - Pr", 0, 100, 65, help="Días con esta probabilidad o mayor serán evaluados.") / 100.0
        mm = c_m.slider("Intensidad (mm/día) - Ur", 0.0, 50.0, 5.0, 0.5, help="Umbral de Riesgo (Ur). Nivel de lluvia necesario para paralizar la actividad.")
        umbral_horas = c_u.slider("Umbral Mínimo (Horas) - Ut", 1.0, 8.0, 3.0, 0.5, help="Umbral Operativo (Ut). Si la fracción de horas operables es menor a este umbral, se pierde la jornada completa protegiendo el OPEX.")
        
        if st.button("Ejecutar Cálculo Topológico e Inferencia IA", type="primary", use_container_width=True):
            st.toast('Iniciando simulación topológica...', icon='🚀')
            
            with st.spinner("Procesando motor estocástico y modelos cognitivos termodinámicos..."):
                final = simular_cronograma(df_aud, clima, prob, mm, dias_idx, feriados_dict, st.session_state['audit_decision'], umbral_horas, h_inicio, h_fin, activar_nlp, activar_ml, temp_global, hum_global)
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
            
            # --- AGENTE PRESCRIPTIVO ---
            if activar_ag:
                st.markdown("### 🤖 Agente Prescriptivo de Mitigación (IA)")
                consejos = agente_prescriptivo_mitigacion(final, retraso_total_proyecto)
                for consejo in consejos:
                    st.markdown(f'<div class="ia-card">{consejo}</div>', unsafe_allow_html=True)
            
            act_reales = final[(final['IsSummary'] == False) & (final['IsMilestone'] == False)]
            
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Gantt Comparativo", "📈 Curva S (Interactiva)", "📅 Riesgo Mensual", "⚠️ Tabla de Impactos"])
            
            with tab1:
                st.markdown("#### Diagrama de Gantt Ajustado")
                df_gantt = act_reales.copy()
                df_gantt['Inicio Nuevo'] = pd.to_datetime(df_gantt['Inicio Nuevo'])
                df_gantt['Fin Nuevo'] = pd.to_datetime(df_gantt['Fin Nuevo'])
                df_gantt = df_gantt.sort_values('Inicio Nuevo')
                
                if not df_gantt.empty:
                    fig_gantt = px.timeline(df_gantt, x_start="Inicio Nuevo", x_end="Fin Nuevo", y="Actividad",
                                            color="Días Impacto", color_continuous_scale=px.colors.sequential.Tealgrn,
                                            hover_data=["Duración Nueva", "Holgura (Días)", "Ruta Crítica"])
                    fig_gantt.update_yaxes(autorange="reversed")
                    fig_gantt.update_layout(height=600, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', template='plotly_white')
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
                                markers=True, line_shape='spline', template='plotly_white')
                fig_s.update_traces(fill='tozeroy', fillcolor='rgba(175, 30, 45, 0.05)', selector=dict(name='Sugerido'))
                fig_s.update_traces(fill='tozeroy', fillcolor='rgba(148, 163, 184, 0.05)', selector=dict(name='Base'))
                fig_s.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', hovermode='x unified', xaxis_title="Fechas de Finalización", yaxis_title="Tareas Completadas",
                                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                fig_s.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#F1F5F9')
                fig_s.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#F1F5F9')
                st.plotly_chart(fig_s, use_container_width=True)
                
            with tab3:
                df_hist = final[final['IsRain']==True].copy()
                if not df_hist.empty:
                    df_hist['Mes'] = pd.to_datetime(df_hist['Inicio Nuevo']).dt.month_name()
                    counts_mes = df_hist['Mes'].value_counts().reset_index()
                    counts_mes.columns = ['Mes', 'Qty']
                    
                    fig_riesgo = px.bar(counts_mes, x='Mes', y='Qty', text='Qty', color_discrete_sequence=['#0EA5E9'], template='plotly_white')
                    fig_riesgo.update_traces(textposition='outside', marker_line_color='rgba(0,0,0,0)', opacity=0.9, width=0.6)
                    fig_riesgo.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title=None, yaxis_title="Cantidad de Tareas Afectadas")
                    fig_riesgo.update_yaxes(showgrid=True, gridcolor='#F1F5F9')
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

            b_out = io.BytesIO()
            p_name = st.session_state.get('project_name', 'Proyecto')
            safe_name = "".join([c for c in p_name if c.isalnum() or c in (' ', '_')]).strip()
            
            columnas_exportar = ['ID', 'WBS', 'Actividad', 'Duración Base', 'Inicio Base', 'Fin Base', 
                                 'Duración Nueva', 'Inicio Nuevo', 'Fin Nuevo', 'Tr (Secado/Horas)', 'Pred. Orig', 'Pred. Nueva', 
                                 'Prob. Lluvia', 'mm Lluvia Max', 'Lluvia Total Acum (mm)', 'Fecha Última Lluvia', 
                                 'Días Impacto', 'Estado', 'Holgura (Días)', 'Ruta Crítica']
            
            with pd.ExcelWriter(b_out, engine='xlsxwriter') as w:
                final[columnas_exportar].to_excel(w, index=False, sheet_name="Sugerencias", startrow=1)
                wb = w.book
                ws = w.sheets['Sugerencias']
                
                formato_project = 'dd/mm/yyyy'
                fmt_title = wb.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#1E293B', 'font_color': 'white', 'font_size': 14})
                fmt_norm = wb.add_format({'border':1})
                fmt_date = wb.add_format({'num_format': formato_project, 'border':1})
                fmt_med = wb.add_format({'bg_color': '#DBEAFE', 'border':1, 'font_color': 'black'}) 
                fmt_med_date = wb.add_format({'bg_color': '#DBEAFE', 'num_format': formato_project, 'border':1, 'font_color': 'black'})
                fmt_high = wb.add_format({'bg_color': '#0F172A', 'border':1, 'font_color': 'white'}) 
                fmt_high_date = wb.add_format({'bg_color': '#0F172A', 'num_format': formato_project, 'border':1, 'font_color': 'white'})
                fmt_logic = wb.add_format({'bg_color': '#FEF08A', 'border':1}) 
                fmt_logic_date = wb.add_format({'bg_color': '#FEF08A', 'num_format': formato_project, 'border':1})
                fmt_summary = wb.add_format({'bold': True, 'bg_color': '#F1F5F9', 'border':1})
                fmt_summary_date = wb.add_format({'bold': True, 'bg_color': '#F1F5F9', 'num_format': formato_project, 'border':1})

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
                    
                    if is_summary: row_fmt = fmt_summary; row_date_fmt = fmt_summary_date
                    elif impacto > 2: row_fmt = fmt_high; row_date_fmt = fmt_high_date
                    elif impacto > 0: row_fmt = fmt_med; row_date_fmt = fmt_med_date
                    elif is_logic: row_fmt = fmt_logic; row_date_fmt = fmt_logic_date
                        
                    for c, col_name in enumerate(columnas_exportar):
                        val = row.get(col_name, "")
                        if pd.isna(val): val = ""
                        
                        cell_fmt = row_date_fmt if (c in date_cols or c == rain_date_col) else row_fmt
                        
                        if (c in date_cols or c == rain_date_col) and isinstance(val, (datetime, date, pd.Timestamp)):
                            ws.write_datetime(r+2, c, val, cell_fmt)
                        else:
                            ws.write(r+2, c, val, cell_fmt)
                
                ws.set_column('C:C', 40); ws.set_column('R:R', 35)

                ws_data = wb.add_worksheet('Datos_Graficos')
                ws_data.write('A1', 'Fecha'); ws_data.write('B1', 'Acumulado Base'); ws_data.write('C1', 'Acumulado Sugerido')
                
                df_s_excel = df_s.pivot_table(index='Fecha', columns='Tipo', values='Acumulado', aggfunc='max').ffill().fillna(0).reset_index()
                if 'Base' not in df_s_excel.columns: df_s_excel['Base'] = 0
                if 'Sugerido' not in df_s_excel.columns: df_s_excel['Sugerido'] = 0
                
                if not df_s_excel.empty:
                    for i, r in df_s_excel.iterrows():
                        date_val = r['Fecha']
                        if isinstance(date_val, pd.Timestamp): date_val = date_val.date()
                        ws_data.write(i+1, 0, date_val.strftime('%d/%m/%Y'))
                        ws_data.write(i+1, 1, r['Base'])
                        ws_data.write(i+1, 2, r['Sugerido'])
                
                ws_data.write('E1', 'Mes'); ws_data.write('F1', 'Cantidad')
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
                    chart1.add_series({'name': 'Plan Base', 'categories': ['Datos_Graficos', 1, 0, max_row, 0], 'values': ['Datos_Graficos', 1, 1, max_row, 1], 'line': {'color': 'gray'}})
                    chart1.add_series({'name': 'Con Lluvia', 'categories': ['Datos_Graficos', 1, 0, max_row, 0], 'values': ['Datos_Graficos', 1, 2, max_row, 2], 'line': {'color': 'blue'}})
                chart1.set_title({'name': 'Curva S de Avance (Solo Tareas de Trabajo)'})
                chart_sheet1.set_chart(chart1)

                if not df_hist.empty:
                    chart_sheet2 = wb.add_chartsheet('Grafico_Barras')
                    chart2 = wb.add_chart({'type': 'column'})
                    max_row_h = len(counts)
                    chart2.add_series({'name': 'Actividades Afectadas', 'categories': ['Datos_Graficos', 1, 4, max_row_h, 4], 'values': ['Datos_Graficos', 1, 5, max_row_h, 5], 'fill': {'color': '#AF1E2D'}})
                    chart2.set_title({'name': 'Riesgo por Mes'})
                    chart_sheet2.set_chart(chart2)

            st.download_button("📥 Descargar Reporte Gerencial Completo (Excel)", b_out.getvalue(), f"Reporte_Climatico_{safe_name}.xlsx", "application/vnd.ms-excel", type="primary", use_container_width=True)
