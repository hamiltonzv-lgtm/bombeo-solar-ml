from fpdf import FPDF
import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import requests
import os

def descargar_img_segura(url, ruta):
    try:
        if not os.path.exists(ruta) and url:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                with open(ruta, 'wb') as f:
                    f.write(res.content)
    except Exception:
        pass

def generar_graficas_temporales(datos: dict):
    df_hist = datos['df_historico']
    fig1, ax1 = plt.subplots(figsize=(6, 4))
    sns.heatmap(df_hist[['ghi_kwh_m2', 'temp_max_c', 'demanda_m3', 'deficit_m3']].corr(), annot=True, cmap="YlOrRd", fmt=".2f", ax=ax1)
    ax1.set_title("Matriz de Correlacion (EDA)", fontsize=10)
    plt.tight_layout()
    fig1.savefig("temp_heatmap.png", dpi=200)
    plt.close(fig1)

    df_graf = datos['df_grafica']
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.plot(df_graf['Día de Prueba'], df_graf['Déficit Real (m³)'], label='Déficit Real', color='#e74c3c')
    ax2.plot(df_graf['Día de Prueba'], df_graf['Predicción IA (m³)'], label='Predicción RF', color='#3498db', linestyle='--')
    ax2.plot(df_graf['Día de Prueba'], df_graf.get('Línea Base (m³)', [0]*30), label='Línea Base', color='gray', linestyle=':')
    ax2.set_title("Evaluacion del Modelo (Prueba)", fontsize=10)
    ax2.set_xlabel("Dias")
    ax2.set_ylabel("Volumen (m3)")
    ax2.legend()
    plt.tight_layout()
    fig2.savefig("temp_ml_eval.png", dpi=200)
    plt.close(fig2)
    
    campana = datos['campana']
    fig3, ax3 = plt.subplots(figsize=(6, 4))
    ax3.fill_between(campana['horas'], campana['caudales'], color='#f1c40f', alpha=0.5)
    ax3.plot(campana['horas'], campana['caudales'], color='#f39c12', linewidth=2)
    ax3.set_title("Curva Estimada de Bombeo Diario", fontsize=10)
    ax3.set_xlabel("Hora del dia")
    ax3.set_ylabel("Caudal (m3/h)")
    plt.tight_layout()
    fig3.savefig("temp_campana.png", dpi=200)
    plt.close(fig3)

    finanzas = datos['finanzas']
    fig4, ax4 = plt.subplots(figsize=(6, 4))
    ax4.bar(['Solar (CAPEX+OPEX)', 'Diesel (Combustible)'], [finanzas['Solar'], finanzas['Diesel']], color=['#2ecc71', '#e74c3c'])
    ax4.set_title("Proyeccion de Costos a 10 Años (COP)", fontsize=10)
    ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
    plt.tight_layout()
    fig4.savefig("temp_finanzas.png", dpi=200)
    plt.close(fig4)

def crear_informe_pdf(datos: dict) -> bytes:
    generar_graficas_temporales(datos)
    descargar_img_segura(datos.get('img_hero'), "temp_hero.jpg")
    descargar_img_segura(datos.get('img_panel'), "temp_panel.jpg")
    descargar_img_segura(datos.get('img_bomba'), "temp_bomba.jpg")
    
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- PÁGINA 1: PORTADA IMPACTANTE ---
    pdf.add_page()
    pdf.set_fill_color(0, 68, 129)
    pdf.rect(0, 0, 210, 297, 'F')
    
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("helvetica", "B", 24)
    pdf.set_y(40)
    pdf.cell(0, 10, "DISENO DE SISTEMA DE BOMBEO SOLAR", ln=True, align="C")
    pdf.set_font("helvetica", "", 16)
    pdf.cell(0, 10, "Zonas No Interconectadas (ZNI)", ln=True, align="C")
    
    if os.path.exists("temp_hero.jpg"):
        pdf.image("temp_hero.jpg", x=20, y=80, w=170)
        
    pdf.set_y(220)
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, f"Ubicacion: {datos.get('direccion')}", ln=True, align="C")
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 10, f"Fecha: {datetime.datetime.now().strftime('%d de %B de %Y')}", ln=True, align="C")
    
    # --- PÁGINA 2: EXPLORACIÓN DE DATOS (Mismos gráficos) ---
    pdf.add_page()
    pdf.set_fill_color(0, 68, 129)
    pdf.rect(0, 0, 210, 20, 'F')
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(255, 255, 255)
    pdf.set_y(6)
    pdf.cell(0, 10, "1. EXPLORACION DE DATOS Y FINANZAS", ln=True, align="L")
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("helvetica", "", 11)
    pdf.ln(10)
    pdf.multi_cell(0, 6, f"El presente proyecto dimensiona una solucion hidrica operada con energia solar fotovoltaica para {datos.get('uso', 'uso general')}. La arquitectura garantiza un abastecimiento de {datos.get('volumen_diario')} m3/dia basandose en la prediccion meteorologica generada por algoritmos de Machine Learning.")
    
    pdf.image("temp_heatmap.png", x=15, y=pdf.get_y()+5, w=85)
    pdf.image("temp_finanzas.png", x=110, y=pdf.get_y()+5, w=85)
    pdf.ln(65)
    
    pdf.image("temp_ml_eval.png", x=15, y=pdf.get_y()+5, w=85)
    pdf.image("temp_campana.png", x=110, y=pdf.get_y()+5, w=85)
    pdf.ln(65)
    
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 8, " DIRECTRIZ OPERATIVA AUTOMATIZADA (MACHINE LEARNING)", ln=True, fill=True)
    pdf.set_font("helvetica", "", 11)
    pdf.multi_cell(0, 7, f"{datos.get('decision_ml')}")

    # --- PÁGINA 3: INGENIERÍA DE DETALLE Y TRATAMIENTO ---
    pdf.add_page()
    pdf.set_fill_color(0, 68, 129)
    pdf.rect(0, 0, 210, 20, 'F')
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(255, 255, 255)
    pdf.set_y(6)
    pdf.cell(0, 10, "2. INGENIERIA DE DETALLE Y COMPONENTES (NTC 2050)", ln=True, align="L")
    
    pdf.ln(10)
    pdf.set_text_color(0, 0, 0)
    
    def dibujar_encabezado_tabla(titulo1, titulo2):
        pdf.set_fill_color(0, 68, 129)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(95, 8, titulo1, border=1, fill=True)
        pdf.cell(95, 8, titulo2, border=1, fill=True, ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("helvetica", "", 10)

    def dibujar_fila(col1, col2, fill):
        pdf.set_fill_color(240, 245, 250) if fill else pdf.set_fill_color(255, 255, 255)
        pdf.cell(95, 8, str(col1), border=1, fill=True)
        pdf.cell(95, 8, str(col2), border=1, fill=True, ln=True)

    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "Parametros Hidraulicos y Tratamiento", ln=True)
    dibujar_encabezado_tabla("Parametro", "Especificacion / Diseno")
    caudal_m3 = float(datos.get('caudal', 0))
    dibujar_fila("Caudal Solicitado", f"{caudal_m3} m3/h ({round(caudal_m3/3.6, 2)} L/s)", False)
    dibujar_fila("Carga Dinamica Total (CDT)", f"{datos.get('cdt')} m", True)
    dibujar_fila("Tuberia de Impulsion", f"PVC {datos.get('tuberia')}\"", False)
    
    trat = datos.get('tratamiento', {})
    if trat and trat.get('requerido'):
        dibujar_fila("Sistema de Filtracion", f"{trat.get('filtros')}", True)
        dibujar_fila("Potabilizacion y Desinfeccion", f"{trat.get('desinfeccion')}", False)
    
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "Subsistema Electromecanico y Control", ln=True)
    dibujar_encabezado_tabla("Componente", "Seleccion NTC 2050")
    dibujar_fila("Arreglo Solar", f"{datos.get('total_paneles')}x {datos.get('panel')} ({datos.get('potencia_instalada')} Wp)", False)
    dibujar_fila("Configuracion Electrica", f"{datos.get('configuracion')}", True)
    dibujar_fila("Bomba Sumergible", f"{datos.get('bomba')} ({datos.get('potencia_bomba')}W)", False)
    dibujar_fila("Conductor Lado DC", f"{datos.get('cal_paneles')}", True)
    dibujar_fila("Conductor Lado AC (Pozo)", f"{datos.get('cal_bomba')}", False)
    dibujar_fila("Proteccion Paneles / Motor", f"{datos.get('prot_paneles')} / {datos.get('prot_bomba')}", True)
    dibujar_fila("Inversor / Variador VFD", f"{datos.get('vfd')}", False)
    dibujar_fila("Proteccion contra Sobretension", f"{datos.get('dps')}", True)
    
    t_data = datos.get('tanque', {})
    pdf.ln(5)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "Almacenamiento del Sistema", ln=True)
    dibujar_encabezado_tabla("Tipo de Reserva", "Dimensionamiento")
    dibujar_fila("Bateria Hidraulica (Tanque)", f"Volumen: {t_data.get('volumen_m3')} m3 | {t_data.get('dias')} dias", False)
    if datos.get('con_bateria') and datos.get('baterias'):
        bat = datos.get('baterias')
        dibujar_fila("Bateria Electroquimica (GEL/LITIO)", f"{bat.get('capacidad_ah')} Ah a {bat.get('voltaje_v')}V DC", True)
    else:
        dibujar_fila("Bateria Electroquimica", "No aplica (Bombeo Directo)", True)

    # --- PÁGINA 4: ARQUITECTURA VISUAL ---
    pdf.add_page()
    pdf.set_fill_color(0, 68, 129)
    pdf.rect(0, 0, 210, 20, 'F')
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(255, 255, 255)
    pdf.set_y(6)
    pdf.cell(0, 10, "3. ARQUITECTURA VISUAL DEL PROYECTO", ln=True, align="L")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)

    y_pos = pdf.get_y()
    if os.path.exists("temp_panel.jpg"):
        pdf.image("temp_panel.jpg", x=15, y=y_pos, w=50)
    pdf.set_xy(70, y_pos + 10)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 6, "Generador Solar Fotovoltaico", ln=True)
    pdf.set_x(70)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 6, "Paneles Tier 1 monocristalinos interconectados mediante string.", ln=True)
    
    pdf.ln(35)
    y_pos = pdf.get_y()
    if os.path.exists("temp_bomba.jpg"):
        pdf.image("temp_bomba.jpg", x=15, y=y_pos, w=50)
    pdf.set_xy(70, y_pos + 10)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 6, "Sistema de Bombeo y Tuberias", ln=True)
    pdf.set_x(70)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 6, "Bomba sumergible de acero inoxidable de alta eficiencia.", ln=True)

    pdf.ln(35)
    try:
        y_actual = pdf.get_y() + 5
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 10, "Esquema Grafico de Conexion", ln=True, align="C")
        if datos.get('con_bateria'):
            pdf.image("sistema de bombeo solar con baterias.png.png", x=15, y=y_actual+10, w=180) 
        else:
            pdf.image("sistema de bombeo solar.png.jpeg", x=25, y=y_actual+10, w=160)
    except:
        pdf.set_y(pdf.get_y() + 10)
        pdf.cell(0, 6, "(Diagrama de esquema no disponible en ruta local)")

    # --- PÁGINA 5: ANÁLISIS TÉCNICO Y FINANCIERO INTEGRAL ---
    pdf.add_page()
    pdf.set_fill_color(0, 68, 129)
    pdf.rect(0, 0, 210, 20, 'F')
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(255, 255, 255)
    pdf.set_y(6)
    pdf.cell(0, 10, "4. ANALISIS TECNICO INTEGRAL DEL SISTEMA", ln=True, align="L")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 6, "4.1. Evaluacion del Recurso y Ubicacion", ln=True)
    pdf.set_font("helvetica", "", 10)
    texto_ubicacion = f"El proyecto se ubica en las coordenadas {datos.get('lat')}, {datos.get('lon')} ({datos.get('direccion')}). Esta zona presenta una irradiacion solar promedio anual de {datos.get('hsp')} kWh/m2/dia, un recurso energetico optimo para la implementacion de sistemas fotovoltaicos en Zonas No Interconectadas (ZNI). Este alto indice garantiza que el generador solar trabaje a su capacidad nominal y logre suplir la demanda hidrica proyectada durante las horas de radiacion efectiva."
    pdf.multi_cell(0, 5, texto_ubicacion)
    pdf.ln(4)

    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 6, "4.2. Dimensionamiento Electromecanico y Sanitario", ln=True)
    pdf.set_font("helvetica", "", 10)
    texto_bombeo = f"Para satisfacer la necesidad hidrica de {datos.get('volumen_diario')} m3/dia a traves de una carga dinamica de {datos.get('cdt')} m, se selecciono el equipo sumergible {datos.get('bomba')}. El campo generador fotovoltaico exige la instalacion de {datos.get('total_paneles')} modulos en configuracion {datos.get('configuracion')}, empleando conductores solares certificados {datos.get('cal_paneles')} para evitar caidas de tension por debajo de los limites permitidos por la NTC 2050."
    
    if trat and trat.get('requerido'):
        texto_bombeo += f" Debido a que la tipologia del proyecto fue categorizada para Consumo Humano, se incorporo en la matriz de diseno un sistema de potabilizacion con {trat.get('filtros')} y equipo de {trat.get('desinfeccion')}, garantizando la neutralizacion biologica e inocuidad fisicoquimica exigida por la normatividad nacional de agua potable (Resolucion 2115 de 2007)."
    pdf.multi_cell(0, 5, texto_bombeo)
    pdf.ln(4)

    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 6, "4.3. Viabilidad Tecnico-Financiera: Sistema Solar vs. Generador Diesel", ln=True)
    pdf.set_font("helvetica", "", 10)
    finanzas_dic = datos.get('finanzas', {})
    
    texto_adicional = " Al incluir un banco de baterias electroquimicas, la inversion inicial (CAPEX) se incrementa, pero permite independizar la curva de bombeo de la radiacion, logrando operacion ininterrumpida sin combustibles fosiles." if datos.get('con_bateria') else " La configuracion de bombeo directo (sin baterias) minimiza la inversion inicial y elimina los costos de recambio de acumuladores, siendo la opcion mas eficiente financieramente."
    
    texto_finanzas = f"El modelo de Costo Total de Propiedad (TCO) proyectado a 10 años evidencia una viabilidad absoluta.{texto_adicional} El OPEX operativo de una solucion basada en motor de combustion (Diesel) arroja un valor estimado de COP ${finanzas_dic.get('Diesel', 0):,.0f}. En contraste, el sistema de bombeo solar proyecta un costo de inversion y mantenimiento de COP ${finanzas_dic.get('Solar', 0):,.0f}.\nTecnicamente, la tecnologia fotovoltaica supera al diesel en el contexto ZNI al anular la logistica de transporte de combustible fosil, suprimir el ruido operativo, y eliminar mantenimientos costosos (cambios de aceite y filtros de motor), prolongando la vida util de la generacion de energia a mas de 25 anos."
    pdf.multi_cell(0, 5, texto_finanzas.replace(',', '.'))

    return bytes(pdf.output())