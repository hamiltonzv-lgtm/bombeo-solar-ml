import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from typing import Tuple, Dict, Any

# ==============================================================================
# 1. GENERACIÓN DEL DATASET SINTÉTICO JUSTIFICADO
# ==============================================================================
def generar_dataset_historico(dias: int = 1095) -> pd.DataFrame:
    np.random.seed(42)
    ghi_diario = np.random.normal(loc=5.5, scale=0.8, size=dias)
    ghi_diario = np.clip(ghi_diario, 2.0, 7.5)
    temp_max = np.random.normal(loc=34.0, scale=3.0, size=dias)
    demanda_m3 = 10.0 + (temp_max - 34.0) * 0.5 + np.random.normal(0, 0.5, dias)
    bombeo_real = np.where(ghi_diario >= 5.0, demanda_m3, demanda_m3 * (ghi_diario / 5.0))
    deficit_m3 = demanda_m3 - bombeo_real
    
    df = pd.DataFrame({
        'dia': range(dias), 'ghi_kwh_m2': ghi_diario, 'temp_max_c': temp_max,
        'demanda_m3': demanda_m3, 'deficit_m3': deficit_m3
    })
    return df

# ==============================================================================
# 2. ENTRENAMIENTO, EVALUACIÓN E IMPORTANCIA DE VARIABLES
# ==============================================================================
def entrenar_modelo_predictivo(df: pd.DataFrame) -> Tuple[RandomForestRegressor, Dict[str, float], pd.DataFrame, pd.DataFrame]:
    n_total = len(df)
    train_end = int(n_total * 0.6)
    val_end = int(n_total * 0.8)
    
    train, val, test = df.iloc[:train_end], df.iloc[train_end:val_end], df.iloc[val_end:]
    features = ['ghi_kwh_m2', 'temp_max_c', 'demanda_m3']
    target = 'deficit_m3'
    
    X_train, y_train = train[features], train[target]
    X_test, y_test = test[features], test[target]
    
    y_pred_base = test[target].shift(1).fillna(0)
    
    modelo_rf = RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42)
    modelo_rf.fit(X_train, y_train)
    
    y_pred_rf = modelo_rf.predict(X_test)
    
    # Métricas requeridas por la rúbrica
    mae_base = mean_absolute_error(y_test, y_pred_base)
    mae_rf = mean_absolute_error(y_test, y_pred_rf)
    r2 = r2_score(y_test, y_pred_rf)
    
    metricas = {
        "mae_linea_base_m3": round(mae_base, 2),
        "mae_modelo_rf_m3": round(mae_rf, 2),
        "mejora_porcentual": round((mae_base - mae_rf) / mae_base * 100, 1),
        "r2_score": round(r2, 3)
    }
    
    df_grafica = pd.DataFrame({
        'Día de Prueba': range(1, 31),
        'Déficit Real (m³)': y_test.values[:30],
        'Predicción IA (m³)': y_pred_rf[:30],
        'Línea Base (m³)': y_pred_base.values[:30]
    })
    
    # Extraer pesos de las variables (Feature Importance)
    importancias = modelo_rf.feature_importances_
    df_importancias = pd.DataFrame({
        'Variable': ['Radiación Solar (GHI)', 'Temperatura Máxima', 'Demanda Comunitaria'],
        'Peso': importancias
    }).sort_values(by='Peso', ascending=True)
    
    return modelo_rf, metricas, df_grafica, df_importancias

# ==============================================================================
# 3. MOTOR DE TOMA DE DECISIONES OPERATIVAS
# ==============================================================================
def generar_decision_operativa(modelo: RandomForestRegressor, pronostico_ghi: float, pronostico_temp: float, demanda_est: float) -> str:
    X_nuevo = pd.DataFrame({'ghi_kwh_m2': [pronostico_ghi], 'temp_max_c': [pronostico_temp], 'demanda_m3': [demanda_est]})
    deficit_predicho = modelo.predict(X_nuevo)[0]
    
    if deficit_predicho <= 0.5:
        return "OPERACIÓN NORMAL: El recurso solar será suficiente. Despachar el 100% del caudal a la comunidad y enviar excedentes al tanque de reserva."
    elif 0.5 < deficit_predicho <= 2.5:
        return f"ALERTA MODERADA (Déficit est. {round(deficit_predicho, 1)} m³): Restringir la válvula de entrega comunitaria al 80% para conservar carga en baterías."
    else:
        return f"ACCIÓN CRÍTICA (Déficit est. {round(deficit_predicho, 1)} m³): Activar banco de baterías a profundidad máxima de descarga y racionar entrega de agua en horarios no pico."