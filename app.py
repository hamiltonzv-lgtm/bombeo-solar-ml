import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import motor_fisico as bc
import backend_ml as bml
import generador_pdf as gpdf

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Bombeo Solar IA", page_icon="☀️", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #f4f6f9; }
    .hero-banner { background-image: url('https://images.unsplash.com/photo-1509391366360-2e959784a276?auto=format&fit=crop&w=1600&q=80'); background-size: cover; background-position: center; padding: 50px; border-radius: 10px; text-align: center; color: white; text-shadow: 2px 2px 4px #000; margin-bottom: 20px;}
    .metric-card { background-color: white; padding: 15px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; }
    h1, h2, h3 { color: #004481; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='hero-banner'><h1 style='color: white;'>Sistema Inteligente de Bombeo Solar</h1><p>Diseño Paramétrico NTC 2050 + Machine Learning Predictivo</p></div>", unsafe_allow_html=True)

# --- PANEL LATERAL ---
st.sidebar.header("📍 1. Ubicación (GPS)")
latitud = st.sidebar.number_input("Latitud", value=11.544) 
longitud = st.sidebar.number_input("Longitud", value=-72.907)

st.sidebar.header("🚰 2. Requerimiento Hídrico")
uso_previsto = st.sidebar.selectbox("Uso del Agua", ["Consumo Humano", "Riego Agrícola", "Consumo Pecuario"])
volumen_diario = st.sidebar.number_input("Volumen de agua (m³/día)", value=30.0, step=1.0)
dias_autonomia = st.sidebar.slider("Autonomía Tanque (Días)", 1, 5, 3)

st.sidebar.header("📐 3. Topografía")
h_estatica = st.sidebar.number_input("Prof. Pozo (m)", value=40.0)
h_abatimiento = st.sidebar.number_input("Altura Tanque (m)", value=5.0)
long_tuberias = st.sidebar.number_input("Long. Tubería (m)", value=60.0)

st.sidebar.header("🔋 4. Respaldo (ZNI)")
tipo_sistema = st.sidebar.radio("Selecciona Topología:", ["Bombeo Directo", "Con Banco de Baterías"])
con_bateria = "Baterías" in tipo_sistema

tab_ing, tab_ml, tab_informe, tab_chat = st.tabs(["⚙️ Diseño NTC 2050", "📈 Analítica Exploratoria y ML", "📄 Exportar Reporte (PDF)", "💬 Asistente Experto"])
if 'datos_proyecto' not in st.session_state: st.session_state.datos_proyecto = {}

# --- PESTAÑA 1: INGENIERÍA VISUAL ---
with tab_ing:
    
    # ALERTA DE SEGURIDAD UX: Evita que el usuario descargue el PDF viejo
    if st.session_state.datos_proyecto and st.session_state.datos_proyecto.get('con_bateria') != con_bateria:
        st.warning(f"⚠️ Has cambiado la topología a **{tipo_sistema}**. Debes hacer clic en 'Procesar Diseño Completo' para actualizar los cálculos antes de ir al PDF.")

    if st.button("🚀 Procesar Diseño Completo", use_container_width=True):
        with st.spinner("Geocodificando y calculando bajo estándares..."):
            direccion_real = bc.obtener_nombre_ubicacion(latitud, longitud)
            hsp_data = bc.obtener_hsp_nasa(latitud, longitud)
            hsp_sitio = hsp_data['ANN']
            
            try:
                caudal_req = bc.calcular_caudal_requerido(volumen_diario, hsp_sitio)
                tuberia, vel, alerta_vel = bc.seleccionar_tuberia(caudal_req)
                cdt, perdidas = bc.calcular_cdt(h_estatica, h_abatimiento, long_tuberias, caudal_req, tuberia['diametro_int_mm'])
                bomba = bc.seleccionar_bomba(cdt, caudal_req)
                sistema_pv = bc.dimensionar_generador_solar(bomba, hsp_sitio, panel_idx=0)
                datos_electricos = bc.calcular_electricidad_normativa(sistema_pv['corriente_isc'], bomba['potencia_w'], bomba['voltaje_max_v'])
                tanque = bc.dimensionar_tanque(volumen_diario, dias_autonomia)
                tratamiento = bc.dimensionar_tratamiento_agua(caudal_req, uso_previsto)
                campana = bc.generar_curva_campana(caudal_req)
                finanzas = bc.proyeccion_financiera(bomba['potencia_w'], con_bateria)
                
                col_m1, col_m2 = st.columns([1, 2])
                with col_m1:
                    st.subheader(f"📍 Zona: {direccion_real}")
                    st.map(pd.DataFrame({'lat': [latitud], 'lon': [longitud]}), zoom=12, use_container_width=True)
                with col_m2:
                    st.subheader(f"☀️ Operación: {'24h (Con Baterías)' if con_bateria else 'Diurna (Bombeo Directo)'}")
                    fig_campana = px.area(x=campana['horas'], y=campana['caudales'], labels={'x':'Hora del día', 'y':'Caudal (m³/h)'}, title="Curva Estimada de Bombeo Solar Diario", color_discrete_sequence=['#f1c40f'])
                    fig_campana.update_layout(height=300, margin=dict(l=20, r=20, t=30, b=20))
                    st.plotly_chart(fig_campana, use_container_width=True)

                st.subheader("Especificaciones Electromecánicas (NTC 2050)")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    img_panel = "https://images.unsplash.com/photo-1592833159155-c62df1b65634?auto=format&fit=crop&w=400&q=80"
                    st.image(img_panel, caption="Generador Fotovoltaico")
                    st.success(f"**Paneles:** {sistema_pv['total_paneles']} Und.\n**Config:** {sistema_pv['configuracion']}\n**Cable DC:** {datos_electricos['calibre_paneles']}")
                with col2:
                    img_bomba = "https://images.unsplash.com/photo-1585694315264-18c66e289eb5?auto=format&fit=crop&w=400&q=80"
                    st.image(img_bomba, caption="Bomba Sumergible")
                    st.info(f"**Motor:** {bomba['modelo']} ({bomba['potencia_w']}W)\n**Cable AC/DC:** {datos_electricos['calibre_bomba']}\n**Control:** {datos_electricos['vfd']}")
                with col3:
                    img_tuberia = "https://images.unsplash.com/photo-1608612502693-0105307b22bd?auto=format&fit=crop&w=400&q=80"
                    st.image(img_tuberia, caption="Hidráulica y Potabilización")
                    st.warning(f"**Tubería:** PVC {tuberia['diametro_nom_pulg']}\"\n**Tanque Requerido:** {tanque['volumen_m3']} m³")
                    if tratamiento['requerido']:
                        st.info(f"**Tratamiento:** {tratamiento['filtros']}")
                with col4:
                    img_bateria = "https://images.unsplash.com/photo-1620288627228-56961472e399?auto=format&fit=crop&w=400&q=80" if con_bateria else None
                    if con_bateria:
                        st.image(img_bateria, caption="Banco Baterías")
                        datos_bateria = bc.dimensionar_baterias(bomba['potencia_w'])
                        st.error(f"**Capacidad:** {datos_bateria['capacidad_ah']} Ah a {datos_bateria['voltaje_v']}V\n**Energía:** {datos_bateria['energia_kwh']} kWh")
                    else:
                        st.image("https://images.unsplash.com/photo-1574676580918-028d08560126?auto=format&fit=crop&w=400&q=80", caption="Bombeo Directo")
                        datos_bateria = None
                        st.write("Sin acumulación (Ahorro en OPEX).")

                st.subheader("Dashboard Financiero: Costo Operativo a 10 Años (COP)")
                fig_fin = px.bar(x=['Sistema Solar', 'Generador Diésel'], y=[finanzas['Solar'], finanzas['Diesel']], text_auto='.2s', color=['Sistema Solar', 'Generador Diésel'], color_discrete_map={'Sistema Solar':'#2ecc71', 'Generador Diésel':'#e74c3c'})
                st.plotly_chart(fig_fin, use_container_width=True)

                st.session_state.datos_proyecto.update({
                    'uso': uso_previsto, 'direccion': direccion_real, 'lat': latitud, 'lon': longitud, 
                    'volumen_diario': volumen_diario, 'caudal': caudal_req, 'hsp': hsp_sitio, 'hsp_meses': hsp_data,
                    'cdt': cdt, 'perdidas': perdidas, 'tuberia': tuberia['diametro_nom_pulg'], 'd_interno': tuberia['diametro_int_mm'], 'velocidad': vel,
                    'h_estatica': h_estatica, 'h_tanque': h_abatimiento, 'bomba': f"{bomba['marca']} {bomba['modelo']}", 'potencia_bomba': bomba['potencia_w'],
                    'panel': f"{sistema_pv['panel_marca']} {sistema_pv['panel_referencia']}", 'potencia_panel_w': sistema_pv['potencia_unitaria_w'],
                    'total_paneles': sistema_pv['total_paneles'], 'configuracion': sistema_pv['configuracion'], 'potencia_instalada': sistema_pv['potencia_instalada_w'], 
                    'voc': sistema_pv['voltaje_voc'], 'vmp': sistema_pv['voltaje_vmp'], 'isc': sistema_pv['corriente_isc'],
                    'cal_paneles': datos_electricos['calibre_paneles'], 'prot_paneles': datos_electricos['proteccion_paneles'], 'i_dc': datos_electricos['corriente_diseno_dc'],
                    'cal_bomba': datos_electricos['calibre_bomba'], 'prot_bomba': datos_electricos['proteccion_bomba'], 'i_ac': datos_electricos['corriente_diseno_bomba'],
                    'vfd': datos_electricos['vfd'], 'dps': datos_electricos['dps'], 'tanque': tanque, 'tratamiento': tratamiento, 'campana': campana, 'finanzas': finanzas,
                    'con_bateria': con_bateria, 'baterias': datos_bateria,
                    'img_hero': "https://images.unsplash.com/photo-1509391366360-2e959784a276?auto=format&fit=crop&w=800&q=80",
                    'img_panel': img_panel, 'img_bomba': img_bomba, 'img_tuberia': img_tuberia, 'img_bateria': img_bateria
                })
            except ValueError as e:
                st.error(f"❌ Error: {e}")

# --- PESTAÑA 2: MACHINE LEARNING Y EDA ---
with tab_ml:
    st.header("Análisis Exploratorio y Machine Learning")
    df_historico = bml.generar_dataset_historico()
    
    st.subheader("1. Exploración de Datos (EDA)")
    col_eda1, col_eda2 = st.columns(2)
    with col_eda1:
        fig_corr = px.imshow(df_historico[['ghi_kwh_m2', 'temp_max_c', 'demanda_m3', 'deficit_m3']].corr(), text_auto=True, title="Mapa de Correlaciones")
        st.plotly_chart(fig_corr, use_container_width=True)
    with col_eda2:
        fig_3d = px.scatter_3d(df_historico, x='ghi_kwh_m2', y='temp_max_c', z='demanda_m3', color='deficit_m3', title="Dispersión 3D")
        st.plotly_chart(fig_3d, use_container_width=True)

    st.subheader("2. Motor de Decisión Predictiva")
    colA, colB = st.columns(2)
    pronostico_ghi = colA.slider("GHI Previsto (kWh/m²)", 1.0, 8.0, 5.5)
    temp_max = colB.slider("Temp Max (°C)", 20.0, 45.0, 34.0)
    
    if st.button("Ejecutar Modelo de Machine Learning", use_container_width=True):
        caudal_estimado = st.session_state.datos_proyecto.get('caudal', 6.0) 
        modelo_rf, metricas, df_grafica, df_importancias = bml.entrenar_modelo_predictivo(df_historico)
        
        col_ml1, col_ml2 = st.columns(2)
        with col_ml1:
            fig_ml = px.line(df_grafica, x='Día de Prueba', y=['Déficit Real (m³)', 'Predicción IA (m³)', 'Línea Base (m³)'], color_discrete_map={'Déficit Real (m³)': 'red', 'Predicción IA (m³)': 'blue', 'Línea Base (m³)': 'gray'})
            st.plotly_chart(fig_ml, use_container_width=True)
        with col_ml2:
            fig_imp = px.bar(df_importancias, x='Peso', y='Variable', orientation='h', title="Importancia de Variables")
            st.plotly_chart(fig_imp, use_container_width=True)
        
        st.info(f"**Varianza explicada (R²): {metricas['r2_score']}**. Reducción de error MAE: {metricas['mejora_porcentual']}% frente a persistencia.")
        decision = bml.generar_decision_operativa(modelo_rf, pronostico_ghi, temp_max, caudal_estimado * 3)
        st.success(f"🤖 **DIRECTRIZ OPERATIVA:**\n\n{decision}")
        
        # --- Nota de Transparencia Obligatoria ---
        with st.expander("🔍 Nota de Transparencia y Limitaciones del Modelo"):
            st.markdown("""
            * **Datos Utilizados:** El algoritmo fue entrenado con un *dataset* sintético de 1095 registros (3 años), generado a partir de cruzar la climatología de la NASA con la demanda hídrica estocástica y la temperatura máxima.
            * **Confiabilidad:** El modelo fue evaluado bajo una partición estricta de 60/20/20 (Entrenamiento/Validación/Prueba). Explica el 86% de la varianza del comportamiento del pozo y reduce el margen de error a menos de la mitad comparado con la persistencia estacional.
            * **Límites Conocidos:** El modelo asume un mantenimiento óptimo de la bomba y no prevé anomalías mecánicas, fugas en tuberías o nubosidad extrema no cíclica. Esta directriz es un soporte a la toma de decisiones, no reemplaza el criterio del operador en sitio.
            """)
        
        st.session_state.datos_proyecto.update({'decision_ml': decision, 'metricas_ml': metricas, 'df_historico': df_historico, 'df_grafica': df_grafica})

# --- PESTAÑA 3: PDF ---
with tab_informe:
    st.header("Exportar Reporte Ejecutivo de Ingeniería")
    st.markdown("Descarga la memoria de cálculo de ingeniería de detalle (PDF) lista para entrega a instaladores y clientes en campo.")
    if st.session_state.datos_proyecto and 'decision_ml' in st.session_state.datos_proyecto:
        with st.spinner("Renderizando gráficas, descargando componentes y compilando el reporte..."):
            pdf_bytes = gpdf.crear_informe_pdf(st.session_state.datos_proyecto)
            st.download_button("⬇ Descargar Proyecto Visual (PDF)", data=pdf_bytes, file_name="Proyecto_Ejecutivo_ZNI.pdf", mime="application/pdf", use_container_width=True)
    else:
        st.warning("⚠️ Procesa el diseño y ejecuta el modelo ML para habilitar el reporte visual.")

# --- PESTAÑA 4: ASISTENTE EXPERTO ---
with tab_chat:
    st.header("💬 Asistente Inteligente (Diseño y Normatividad)")
    if "mensajes_chat" not in st.session_state:
        st.session_state.mensajes_chat = [{"role": "assistant", "content": "¡Hola! Conozco tu diseño. Pregúntame sobre requerimientos de agua (aplico OMS/FAO) o normatividad RETIE/NTC 2050."}]

    for msg in st.session_state.mensajes_chat:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input("Ej: ¿Cuánta agua necesito para 15 familias?"):
        st.session_state.mensajes_chat.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        contexto_actual = str(st.session_state.datos_proyecto) if st.session_state.datos_proyecto else "Datos no calculados."
        
        prompt_sistema = f"""Eres un ingeniero consultor experto en RETIE, NTC 2050 y sistemas de bombeo solar. 
        Este es el proyecto del usuario: {contexto_actual}. 
        Si el usuario pregunta por cálculos de volumen de agua, asume el rol de guía basándote en que seleccionó '{uso_previsto}':
        - Para 'Consumo Humano', usa la OMS (100 a 150 Litros/persona/día).
        - Para 'Consumo Pecuario', usa promedios estándar (ej. 40 L/día por bovino).
        - Para 'Riego Agrícola', usa promedios FAO según hectáreas.
        Calcula la respuesta paso a paso y sé directo."""

        with st.spinner("Analizando con DeepSeek V4..."):
            headers = {"Authorization": "Bearer sk-8438533856ea4e1886c77b9d01e6b18f", "Content-Type": "application/json"}
            payload = {"model": "deepseek-chat", "messages": [{"role": "system", "content": prompt_sistema}, {"role": "user", "content": prompt}]}
            try:
                respuesta = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=payload)
                texto_ia = respuesta.json()['choices'][0]['message']['content'] if respuesta.status_code == 200 else f"Error API: {respuesta.status_code}"
            except Exception as e:
                texto_ia = f"Error de conexión local: {e}"

        st.session_state.mensajes_chat.append({"role": "assistant", "content": texto_ia})
        st.chat_message("assistant").write(texto_ia)