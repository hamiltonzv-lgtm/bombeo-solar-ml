import pandas as pd
import math
import requests
from geopy.geocoders import Nominatim
from typing import Tuple, Dict, Any

# ==============================================================================
# 1. BASES DE DATOS DETERMINISTAS
# ==============================================================================
paneles_db = pd.DataFrame([
    {"marca": "Jinko Solar", "referencia": "Tiger Pro 72HC", "potencia_w": 540, "vmp": 40.7, "imp": 13.27, "voc": 49.5, "isc": 13.89},
    {"marca": "Trina Solar", "referencia": "Vertex TSM-DE19", "potencia_w": 550, "vmp": 31.6, "imp": 17.40, "voc": 37.9, "isc": 18.52},
    {"marca": "Canadian Solar", "referencia": "HiKu6 CS6W", "potencia_w": 590, "vmp": 45.0, "imp": 13.12, "voc": 53.7, "isc": 13.93}
])

bombas_db = pd.DataFrame([
    {"marca": "Lorentz", "modelo": "PS2-600 C-SJ8-5", "potencia_w": 700, "voltaje_max_v": 150, "caudal_max_m3h": 9.0, "altura_max_m": 30},
    {"marca": "Lorentz", "modelo": "PS2-1800 C-SJ5-12", "potencia_w": 1800, "voltaje_max_v": 200, "caudal_max_m3h": 7.0, "altura_max_m": 70},
    {"marca": "Lorentz", "modelo": "PS2-4000 C-SJ8-15", "potencia_w": 4000, "voltaje_max_v": 375, "caudal_max_m3h": 12.0, "altura_max_m": 100},
    {"marca": "Grundfos", "modelo": "11 SQF-2", "potencia_w": 1400, "voltaje_max_v": 300, "caudal_max_m3h": 11.0, "altura_max_m": 40}
])

tuberias_db = pd.DataFrame([
    {"diametro_nom_pulg": "1", "diametro_int_mm": 29.54, "rugosidad_c": 150},
    {"diametro_nom_pulg": "1 1/4", "diametro_int_mm": 37.46, "rugosidad_c": 150},
    {"diametro_nom_pulg": "1 1/2", "diametro_int_mm": 43.16, "rugosidad_c": 150},
    {"diametro_nom_pulg": "2", "diametro_int_mm": 54.38, "rugosidad_c": 150}
])

# ==============================================================================
# 2. CONEXIÓN API Y GEOCODIFICACIÓN 
# ==============================================================================
def obtener_hsp_nasa(lat: float, lon: float) -> dict:
    url = "https://power.larc.nasa.gov/api/temporal/climatology/point"
    params = {"parameters": "ALLSKY_SFC_SW_DWN", "community": "RE", "longitude": lon, "latitude": lat, "format": "JSON"}
    try:
        response = requests.get(url, params=params, timeout=8)
        data = response.json()['properties']['parameter']['ALLSKY_SFC_SW_DWN']
        return {k: round(v, 2) for k, v in data.items()}
    except:
        return {'JAN': 5.2, 'FEB': 5.5, 'MAR': 5.8, 'APR': 5.4, 'MAY': 5.1, 'JUN': 5.0, 
                'JUL': 5.3, 'AUG': 5.6, 'SEP': 5.5, 'OCT': 5.2, 'NOV': 5.1, 'DEC': 5.0, 'ANN': 5.5}

def obtener_nombre_ubicacion(lat: float, lon: float) -> str:
    try:
        geolocator = Nominatim(user_agent="app_bombeo_sena")
        location = geolocator.reverse(f"{lat}, {lon}", timeout=5)
        return location.address if location else "Ubicación específica no encontrada"
    except:
        return "Coordenadas registradas (Sin conexión al servidor de mapas)"

# ==============================================================================
# 3. MOTORES DE CÁLCULO FÍSICO Y ELÉCTRICO (NTC 2050 / RETIE)
# ==============================================================================
def calcular_caudal_requerido(volumen_diario_m3: float, hsp: float) -> float:
    if hsp <= 0: raise ValueError("Las horas de sol pico deben ser mayores a cero.")
    return round(volumen_diario_m3 / hsp, 2)

def dimensionar_tanque(volumen_diario_m3: float, dias_autonomia: int) -> dict:
    volumen_tanque = volumen_diario_m3 * dias_autonomia
    return {"volumen_m3": round(volumen_tanque, 1), "dias": dias_autonomia}

def seleccionar_tuberia(caudal_m3_h: float) -> Tuple[Dict[str, Any], float, bool]:
    caudal_m3_s = caudal_m3_h / 3600
    for _, row in tuberias_db.iterrows():
        area_m2 = math.pi * ((row['diametro_int_mm'] / 1000) / 2) ** 2
        velocidad = caudal_m3_s / area_m2
        if velocidad <= 2.5: return row.to_dict(), round(velocidad, 2), False
    return tuberias_db.iloc[-1].to_dict(), round(velocidad, 2), True 

def calcular_cdt(h_estatica: float, h_abatimiento: float, longitud_tuberia: float, caudal_m3_h: float, diametro_int_mm: float) -> Tuple[float, float]:
    caudal_m3_s = caudal_m3_h / 3600
    d_m = diametro_int_mm / 1000
    hf = 10.67 * longitud_tuberia * ((caudal_m3_s ** 1.852) / ((150 ** 1.852) * (d_m ** 4.87)))
    hf_total = hf * 1.10
    cdt = h_estatica + h_abatimiento + hf_total
    return round(cdt, 2), round(hf_total, 2)

def seleccionar_bomba(cdt: float, caudal_m3_h: float) -> Dict[str, Any]:
    bombas_viables = bombas_db[(bombas_db['altura_max_m'] >= cdt * 1.1) & (bombas_db['caudal_max_m3h'] >= caudal_m3_h)]
    if bombas_viables.empty: raise ValueError(f"CDT ({cdt}m) y Caudal ({caudal_m3_h} m3/h) superan el catálogo.")
    return bombas_viables.sort_values(by='potencia_w').iloc[0].to_dict()

def dimensionar_generador_solar(bomba: Dict[str, Any], hsp: float, panel_idx: int = 0) -> Dict[str, Any]:
    panel = paneles_db.iloc[panel_idx]
    total_paneles = math.ceil((bomba['potencia_w'] / 0.75) / panel['potencia_w'])
    max_paneles_serie = math.floor(bomba['voltaje_max_v'] / (panel['voc'] * 1.05)) 
    num_strings = math.ceil(total_paneles / max_paneles_serie)
    paneles_por_string = math.ceil(total_paneles / num_strings)
    
    return {
        "panel_marca": panel['marca'], "panel_referencia": panel['referencia'],
        "potencia_unitaria_w": panel['potencia_w'], "total_paneles": num_strings * paneles_por_string,
        "configuracion": f"{num_strings} paralelo(s) x {paneles_por_string} serie(s)",
        "potencia_instalada_w": (num_strings * paneles_por_string) * panel['potencia_w'],
        "voltaje_vmp": round(paneles_por_string * panel['vmp'], 1), "corriente_imp": round(num_strings * panel['imp'], 1),
        "voltaje_voc": round(paneles_por_string * panel['voc'], 1), "corriente_isc": round(num_strings * panel['isc'], 1)
    }

def dimensionar_baterias(potencia_bomba_w: float) -> dict:
    energia_util_wh = potencia_bomba_w * 4.0
    prof_descarga = 0.6 
    energia_bruta_wh = energia_util_wh / prof_descarga
    voltaje_banco = 48.0
    return {"voltaje_v": voltaje_banco, "capacidad_ah": round(energia_bruta_wh / voltaje_banco, 2), "energia_kwh": round(energia_bruta_wh / 1000, 2)}

def calcular_electricidad_normativa(isc_total: float, potencia_bomba: float, voltaje_bomba: float) -> dict:
    corriente_diseno_dc = isc_total * 1.56
    if corriente_diseno_dc <= 15: cal_dc, prot_dc = "14 AWG Solar", "Breaker DC 15A"
    elif corriente_diseno_dc <= 20: cal_dc, prot_dc = "12 AWG Solar", "Breaker DC 20A"
    elif corriente_diseno_dc <= 30: cal_dc, prot_dc = "10 AWG Solar", "Breaker DC 30A"
    else: cal_dc, prot_dc = "8 AWG Solar", "Breaker DC 40A"
    
    corriente_diseno_bomba = (potencia_bomba / voltaje_bomba) * 1.25
    if corriente_diseno_bomba <= 15: cal_bomba, prot_bomba = "14 AWG Plano", "Guardamotor 15A"
    elif corriente_diseno_bomba <= 20: cal_bomba, prot_bomba = "12 AWG Plano", "Guardamotor 20A"
    else: cal_bomba, prot_bomba = "10 AWG Plano", "Guardamotor 30A"
    
    return {
        "calibre_paneles": cal_dc, "proteccion_paneles": prot_dc, "corriente_diseno_dc": round(corriente_diseno_dc, 2),
        "calibre_bomba": cal_bomba, "proteccion_bomba": prot_bomba, "corriente_diseno_bomba": round(corriente_diseno_bomba, 2),
        "vfd": f"VFD Solar {math.ceil((potencia_bomba/1000)*1.2)}kW MPPT",
        "dps": "DPS Tipo 2 (600V DC) + Puesta a Tierra < 10 Ohms (RETIE)"
    }

def dimensionar_tratamiento_agua(caudal_m3_h: float, uso_previsto: str) -> dict:
    if uso_previsto == "Consumo Humano":
        if caudal_m3_h <= 5:
            filtros = "Filtro Multimedia 10x54 + Filtro Carbon Activado 10x54"
            desinfeccion = "Lampara UV 30W (Acero Inoxidable 304)"
        elif caudal_m3_h <= 10:
            filtros = "Filtro Multimedia 13x54 + Filtro Carbon Activado 13x54"
            desinfeccion = "Lampara UV 55W (Acero Inoxidable 304)"
        else:
            filtros = "Sistema de Filtracion Comercial (>16x65)"
            desinfeccion = "Sistema de Cloracion Automatico / UV Industrial"

        return {
            "requerido": True, "filtros": filtros, "desinfeccion": desinfeccion,
            "nota": "Cumplimiento Resolucion 2115 (Agua Potable)"
        }
    elif uso_previsto == "Riego Agrícola":
        return {"requerido": False, "nota": "Sistema directo. Se recomienda instalar filtro de anillas para proteccion de goteros."}
    else:
        return {"requerido": False, "nota": "Tratamiento no requerido para consumo pecuario estandar."}

# ==============================================================================
# 4. MODELAMIENTO VISUAL Y FINANCIERO (CON IMPACTO DE BATERÍAS)
# ==============================================================================
def generar_curva_campana(caudal_max: float) -> dict:
    horas = list(range(6, 19))
    caudales = [caudal_max * math.exp(-((h - 12)**2) / (2 * 2**2)) for h in horas]
    return {"horas": horas, "caudales": [round(c, 2) for c in caudales]}

def proyeccion_financiera(potencia_w: float, con_baterias: bool = False) -> dict:
    kw = potencia_w / 1000
    costo_diesel_10y = (kw * 6 * 365 * 0.3 * 3000) * 10
    
    # El CAPEX del sistema solar aumenta agresivamente si se usan baterías
    capex_por_kw = 14000000 if con_baterias else 8000000 
    costo_solar_10y = (kw * capex_por_kw) * 1.15
    return {"Solar": round(costo_solar_10y, 0), "Diesel": round(costo_diesel_10y, 0)}