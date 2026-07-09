# CHRONOFLUX AI

Predicción de retrasos climáticos en cronogramas de construcción mediante un motor
**CPM estocástico** que aplica la fórmula `D′ᵢ = Dᵢ + EVBᵢ` (días ajustados = días base
+ buffer de valor climático). Lee un cronograma de MS Project (XML MSPDI), descarga el
clima histórico real de la ubicación de obra (ERA5 / Open-Meteo), simula el impacto de la
lluvia sobre cada partida y devuelve un cronograma ajustado con fechas, ruta crítica
mutada y un reporte gerencial.

Esta versión **separa el motor de cálculo de la interfaz**. La matemática se quedó
intacta; solo se reemplazó la capa de presentación (antes Streamlit, ahora NiceGUI).

---

## Arquitectura

```
chronoflux/
├── core/                 ← NÚCLEO de cálculo (sin dependencias de interfaz)
│   ├── __init__.py       · API pública estable (importa SOLO desde aquí)
│   ├── constants.py      · presets de validación (CFX-*), coordenadas RD, banderas
│   ├── models.py         · IA de carga perezosa: NLP zero-shot + Random Forest (Tr)
│   ├── climate.py        · feriados RD, días hábiles, descarga ERA5 (Open-Meteo)
│   ├── msproject.py      · auditoría del XML (→ AuditResult), calendario, XML ajustado
│   ├── engine.py         · motor CPM estocástico V6 (forward/backward pass, deuda de secado)
│   └── orchestrator.py   · run_simulation(): entrada única → df + KPIs + agente
│
├── web/                  ← PRESENTACIÓN (NiceGUI; intercambiable)
│   ├── theme.py          · tokens de color de marca + plantilla Plotly única
│   ├── charts.py         · Gantt (ruta crítica roja), curva S ponderada, clima, riesgo
│   ├── exporters.py      · Reporte gerencial en Excel (2 hojas)
│   └── main.py           · la aplicación web completa
│
├── tests/
│   └── test_golden.py    · prueba que valida que el núcleo calcula correctamente
├── sample_data/
│   └── proyecto_demo.xml · cronograma vial de ejemplo (lo genera el test)
└── requirements.txt
```

**Regla de oro:** las interfaces importan únicamente desde `core`:

```python
from core import auditar_xml, run_simulation, SimulationParams

audit  = auditar_xml(xml_bytes)                       # parsea el MSPDI
clima  = obtener_clima_horario_laboral(lat, lon, 8, 17)[1]
params = SimulationParams(pr=0.22, ur=2.0, hw_min=5.0, h_inicio=8, h_fin=17)
result = run_simulation(audit, clima, params)         # corre el motor
result.df          # cronograma ajustado (DataFrame)
result.kpis        # KPIs gerenciales
result.mitigacion  # informe del agente prescriptivo
```

Así, cambiar de NiceGUI a FastAPI+React, a un script batch o a un notebook **no toca una
sola línea de cálculo**.

---

## Cómo ejecutar la interfaz web

```bash
cd chronoflux
pip install -r requirements.txt
python -m web.main
```

Abre `http://localhost:8080`. El flujo en pantalla:

1. **Ubicación** — busca la cabecera del proyecto o haz clic en el mapa para fijar coordenadas.
2. **Clima** — pulsa *Consultar clima* para descargar la serie ERA5 (2014–2023).
3. **Cronograma** — sube el `.xml` exportado de MS Project. Hay uno de ejemplo en `sample_data/`.
4. **Umbrales** — ajusta Pr / Ur / Hw (o elige un preset CFX en el panel izquierdo) y pulsa *Ejecutar cálculo*.
5. **Resultados** — KPIs, agente prescriptivo, Gantt/Curva S/Riesgo, y descarga del XML ajustado + Excel.

---

## Pruebas

```bash
cd chronoflux
python -m tests.test_golden
```

La prueba es **100% offline** (clima inyectado, IA desactivada) y verifica que la
separación motor/interfaz no alteró los cálculos:

- **Punto cero** — el preset de control (umbrales inalcanzables) produce EVB = 0.
- **Reactividad** — un escenario de estrés con clima húmedo genera impacto > 0.
- **Determinismo** — dos corridas idénticas producen resultados idénticos.
- **Blindaje DAG** — una red con ciclo lanza `CicloLogicoError` (no se degrada).
- **Round-trip XML** — el XML ajustado es válido y se vuelve a parsear sin pérdidas.

---

## Notas de despliegue

- **Internet** — la interfaz necesita salida HTTPS a `archive-api.open-meteo.com` para el clima.
- **IA opcional** — el clasificador NLP (`transformers` + `torch`) está comentado en
  `requirements.txt`. Solo se carga la primera vez que se usa (carga perezosa) y el modelo
  pesa cientos de MB. Sin él, el sistema corre en **modo determinista** con los fallbacks
  por RegEx/valores estáticos descritos en la tesis. Para producción con IA, usa un host con
  RAM suficiente (Render/Railway/Fly de pago, o una VM) y un volumen para cachear el modelo.
- **Random Forest** — `scikit-learn` se entrena al vuelo (sintético, ~2000 muestras) en
  segundos; no requiere descargas externas.
- **Estado** — NiceGUI crea estado por cliente; cada pestaña del navegador es una sesión
  independiente. Para multiusuario concurrente, dimensiona el proceso o usa varios workers.

---

## Qué cambió respecto a la versión Streamlit

- El motor `simular_cronograma` y toda su aritmética se conservan **byte a byte**; la única
  cirugía fue sustituir `st.error()/st.stop()` (detección de ciclos) por la excepción
  `CicloLogicoError`, y los cachés `@st.cache_*` por `functools.lru_cache` / singletons perezosos.
- `auditar_xml` ya no escribe en `st.session_state`: devuelve un `AuditResult` autocontenido.
- Los modelos de IA dejaron de cargarse al importar; ahora son perezosos.
- Gráficos: la ruta crítica se pinta en **rojo** (no un degradado por impacto), el Gantt
  superpone los hitos de **línea base**, y la curva S muestra **avance físico ponderado por
  duración** (estilo EVM) en lugar de un conteo de tareas.
- Colores y estilos de figura centralizados en una **plantilla Plotly única** (`web/theme.py`).
