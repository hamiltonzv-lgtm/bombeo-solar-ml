# bombeo-solar-ml
sistema de bombeo solar para comunidades no interconectadas al sistema eléctrico nacional
Descripción General
Esta plataforma es una herramienta de ingeniería avanzada diseñada para dimensionar, evaluar y operar sistemas de bombeo de agua impulsados por energía solar fotovoltaica. Creada específicamente para mitigar el estrés hídrico en Zonas No Interconectadas (ZNI), la aplicación fusiona el rigor del cálculo determinista (Normatividad NTC 2050 y lineamientos RETIE) con la capacidad predictiva de la Inteligencia Artificial (Machine Learning y LLMs).
A diferencia de los calculadores tradicionales, este sistema no solo diseña la infraestructura física, sino que proyecta financieramente su viabilidad y proporciona directrices operativas dinámicas basadas en el pronóstico climatológico.
🛠️ Guía de Uso Paso a Paso
El flujo de trabajo de la aplicación está diseñado para ser secuencial. Comienza configurando el proyecto en el panel lateral y avanza a través de las pestañas principales.
Paso 1: Configuración de Parámetros (Panel Lateral)
Antes de procesar cualquier dato, define las condiciones de frontera de tu proyecto en el menú izquierdo:
•	1. Ubicación (GPS): Ingresa la Latitud y Longitud exactas. El sistema utilizará estas coordenadas para conectarse a la API satelital de la NASA (NASA POWER) y extraer la irradiación solar (HSP) promedio del sitio.
•	2. Requerimiento Hídrico:
o	Uso del Agua: Selecciona si es para consumo humano, riego agrícola o pecuario. (Esto ajustará las directrices de potabilización y las normativas aplicables de la OMS/FAO en el asistente experto).
o	Volumen Diario: Los metros cúbicos ($m^3$) necesarios por día.
o	Autonomía: Días de reserva que debe soportar el tanque de almacenamiento (batería hidráulica).
•	3. Topografía: Ingresa la profundidad del pozo, la altura de elevación hasta el tanque y la longitud total de la tubería para calcular automáticamente las pérdidas por fricción y la Carga Dinámica Total (CDT).
•	4. Respaldo (ZNI): Elige entre un sistema de "Bombeo Directo" (solo opera de día, máxima rentabilidad) o "Con Banco de Baterías" (operación 24/7, mayor inversión inicial).
Paso 2: ⚙️ Diseño NTC 2050 (Ingeniería de Detalle)
Una vez configurado el panel lateral, dirígete a la primera pestaña y haz clic en el botón azul "Procesar Diseño Completo".
•	¿Qué hace el sistema? Dimensiona los paneles solares, la bomba sumergible, el calibre de los conductores eléctricos (AWG), las protecciones termomagnéticas, el Variador de Frecuencia (VFD) y el sistema de potabilización (si aplica).
•	Resultados visuales: Observarás un mapa topográfico, un gráfico de barras con el recurso solar mensual de la NASA, la curva de campana solar que estima el caudal por hora, y un Dashboard Financiero comparando el Costo Total de Propiedad (TCO) a 10 años entre tu diseño solar y un generador diésel.
Paso 3: 📈 Analítica Exploratoria y Machine Learning
Esta pestaña transforma los datos climáticos en decisiones operativas.
•	Exploración (EDA): Analiza la matriz de correlaciones y el gráfico de dispersión 3D para entender cómo la radiación y la temperatura afectan el déficit de agua en tu zona.
•	Motor Predictivo: Utiliza los controles deslizantes para ingresar un pronóstico del clima del día siguiente (GHI y Temperatura) y haz clic en "Ejecutar Modelo de Machine Learning".
•	Veredicto: Un algoritmo Random Forest Regressor entrenado con 3 años de datos históricos emitirá una alerta semaforizada indicando si el operador debe restringir la válvula o activar las baterías para evitar un desabastecimiento.
Paso 4: 📄 Exportar Reporte Ejecutivo (PDF)
Con el diseño procesado y el modelo predictivo ejecutado, dirígete a esta pestaña para materializar tu trabajo.
•	Haz clic en "Descargar Proyecto Visual (PDF)".
•	Obtendrás una Memoria de Cálculo profesional (5 páginas) en formato revista. Incluye la portada, gráficas vectoriales del análisis financiero y predictivo, tablas técnicas de conductores y protecciones bajo norma, el diagrama de instalación y un análisis técnico integral justificando la inversión. Este documento está listo para ser entregado a instaladores o juntas de evaluación.
Paso 5: 💬 Asistente Normativo Experto
¿Tienes dudas técnicas sobre la instalación? Esta pestaña contiene un chat impulsado por Inteligencia Artificial (DeepSeek V4) con conocimiento integral del RETIE y la NTC 2050.
•	El asistente tiene "memoria de contexto": sabe exactamente qué bomba, paneles y cables calculaste en la Pestaña 1.
•	Puedes preguntarle: "¿Por qué la tubería debe ir enterrada?", "¿El calibre de cable DC calculado soporta la intemperie?" o "¿Cuántos litros necesito si son 15 familias?". El chat responderá de forma técnica basándose en las normas de la OMS, FAO y reglamentos colombianos aplicados a tu diseño específico.
💻 Stack Tecnológico
•	Frontend: Streamlit (Framework UI interactivo).
•	Backend & Matemáticas: Pandas, NumPy, Math (Ecuaciones de fluidos Hazen-Williams).
•	Visualización: Plotly Express (Gráficos interactivos 2D y 3D), Matplotlib y Seaborn (Gráficas vectoriales para PDF).
•	Machine Learning: Scikit-learn (Random Forest Regressor).
•	Integración de APIs: NASA POWER (Climatología) y DeepSeek API (Asistente LLM).
•	Exportación: FPDF2 (Generación dinámica de reportes).

