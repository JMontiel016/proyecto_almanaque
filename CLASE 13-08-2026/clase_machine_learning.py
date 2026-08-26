"""
CASO PRÁCTICO: MACHINE LEARNING DESDE UN EXCEL
Objetivo: predecir qué clientes tienen mayor riesgo de abandonar un negocio.

Instalar dependencias:
    pip install pandas scikit-learn openpyxl

Colocar este archivo en la misma carpeta que:
    clientes_negocio_machine_learning.xlsx
"""

import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

# ============================================================
# PASO 1. CARGAR EL EXCEL
# ============================================================

ARCHIVO = "clientes_negocio_machine_learning.xlsx"

df = pd.read_excel(ARCHIVO, sheet_name="Datos_clientes")

print("\n=== 1. PRIMERAS FILAS ===")
print(df.head())

print("\n=== 2. DIMENSIONES ===")
print("Filas:", df.shape[0])
print("Columnas:", df.shape[1])

print("\n=== 3. TIPOS DE DATOS ===")
print(df.dtypes)

print("\n=== 4. VALORES FALTANTES ===")
print(df.isna().sum())

print("\n=== 5. DUPLICADOS ===")
print("Duplicados:", df.duplicated().sum())


# ============================================================
# PASO 2. LIMPIEZA
# ============================================================

# Eliminar filas duplicadas
df = df.drop_duplicates().copy()

# Normalizar textos
columnas_texto = ["genero", "ciudad", "canal_preferido", "segmento"]

for columna in columnas_texto:
    # Mantenemos dtype object y usamos np.nan para que scikit-learn
    # pueda imputar correctamente los valores categóricos faltantes.
    df[columna] = df[columna].apply(
        lambda valor: valor.strip().upper()
        if isinstance(valor, str)
        else np.nan
    )

# Convertir valores imposibles en NaN
df.loc[(df["edad"] < 18) | (df["edad"] > 100), "edad"] = np.nan
df.loc[df["gasto_total_6m"] < 0, "gasto_total_6m"] = np.nan
df.loc[df["dias_desde_ultima_compra"] < 0, "dias_desde_ultima_compra"] = np.nan

print("\n=== 6. FALTANTES DESPUÉS DE LIMPIAR ===")
print(df.isna().sum())


# ============================================================
# PASO 3. DEFINIR X E y
# ============================================================

# y = variable que queremos predecir
y = df["abandono"]

# cliente_id es solo un identificador, por eso no entra al modelo
X = df.drop(columns=["abandono", "cliente_id"])


# ============================================================
# PASO 4. SEPARAR TRAIN Y TEST
# ============================================================

# IMPORTANTE:
# Separamos ANTES de normalizar.
# Si normalizamos todo el dataset primero, usamos información del test
# para preparar el entrenamiento. Eso se llama DATA LEAKAGE.

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.30,
    random_state=42,
    stratify=y
)

print("\n=== 7. PARTICIÓN ===")
print("Train:", X_train.shape)
print("Test :", X_test.shape)


# ============================================================
# PASO 5. VARIABLES NUMÉRICAS Y CATEGÓRICAS
# ============================================================

columnas_numericas = [
    "edad",
    "antiguedad_meses",
    "compras_ultimos_6m",
    "gasto_total_6m",
    "dias_desde_ultima_compra",
    "reclamos_ultimos_6m",
    "descuento_promedio",
]

columnas_categoricas = [
    "genero",
    "ciudad",
    "canal_preferido",
    "segmento",
]


# ============================================================
# PASO 6. PREPROCESAMIENTO
# ============================================================

# Numéricas:
# - faltantes -> mediana
# - normalización -> StandardScaler
pipeline_numerico = Pipeline(
    steps=[
        ("imputacion", SimpleImputer(strategy="median")),
        ("normalizacion", StandardScaler()),
    ]
)

# Categóricas:
# - faltantes -> valor más frecuente
# - categorías -> One-Hot Encoding
pipeline_categorico = Pipeline(
    steps=[
        ("imputacion", SimpleImputer(strategy="most_frequent")),
        ("one_hot", OneHotEncoder(handle_unknown="ignore")),
    ]
)

preprocesador = ColumnTransformer(
    transformers=[
        ("numericas", pipeline_numerico, columnas_numericas),
        ("categoricas", pipeline_categorico, columnas_categoricas),
    ]
)


# ============================================================
# PASO 7. MODELO
# ============================================================

modelo = LogisticRegression(
    max_iter=1000,
    random_state=42
)

pipeline_ml = Pipeline(
    steps=[
        ("preprocesamiento", preprocesador),
        ("modelo", modelo),
    ]
)


# ============================================================
# PASO 8. ENTRENAR
# ============================================================

print("\n=== 8. ENTRENANDO MODELO ===")
pipeline_ml.fit(X_train, y_train)
print("Modelo entrenado correctamente.")


# ============================================================
# PASO 9. EVALUAR
# ============================================================

predicciones = pipeline_ml.predict(X_test)

accuracy = accuracy_score(y_test, predicciones)
precision = precision_score(y_test, predicciones, zero_division=0)
recall = recall_score(y_test, predicciones, zero_division=0)
f1 = f1_score(y_test, predicciones, zero_division=0)

print("\n=== 9. MÉTRICAS ===")
print(f"Accuracy : {accuracy:.3f}")
print(f"Precision: {precision:.3f}")
print(f"Recall   : {recall:.3f}")
print(f"F1 Score : {f1:.3f}")

print("\n=== 10. MATRIZ DE CONFUSIÓN ===")
print(confusion_matrix(y_test, predicciones))

print("\n=== 11. REPORTE DE CLASIFICACIÓN ===")
print(classification_report(y_test, predicciones, zero_division=0))


# ============================================================
# PASO 10. PROBABILIDAD DE ABANDONO
# ============================================================

probabilidades = pipeline_ml.predict_proba(X)[:, 1]

resultado = df[["cliente_id"]].copy()
resultado["probabilidad_abandono"] = probabilidades

resultado["riesgo_predicho"] = np.select(
    [
        resultado["probabilidad_abandono"] >= 0.70,
        resultado["probabilidad_abandono"] >= 0.40,
    ],
    [
        "ALTO",
        "MEDIO",
    ],
    default="BAJO"
)

resultado = resultado.sort_values(
    "probabilidad_abandono",
    ascending=False
)

print("\n=== 12. CLIENTES CON MAYOR RIESGO ===")
print(resultado.head(10))


# ============================================================
# PASO 11. GUARDAR RESULTADOS
# ============================================================

resultado.to_excel(
    "clientes_con_prediccion.xlsx",
    index=False
)

print("\nArchivo generado: clientes_con_prediccion.xlsx")


# ============================================================
# PASO 12. PROBAR UN CLIENTE NUEVO
# ============================================================

cliente_nuevo = pd.DataFrame(
    [{
        "edad": 35,
        "genero": "M",
        "ciudad": "ÑEMBY",
        "antiguedad_meses": 18,
        "compras_ultimos_6m": 2,
        "gasto_total_6m": 280000,
        "dias_desde_ultima_compra": 95,
        "canal_preferido": "WHATSAPP",
        "reclamos_ultimos_6m": 2,
        "descuento_promedio": 0.05,
        "segmento": "BASICO",
    }]
)

prob_cliente = pipeline_ml.predict_proba(cliente_nuevo)[0, 1]
pred_cliente = pipeline_ml.predict(cliente_nuevo)[0]

print("\n=== 13. CLIENTE NUEVO ===")
print(f"Probabilidad de abandono: {prob_cliente:.2%}")
print("Predicción:", "ABANDONA" if pred_cliente == 1 else "CONTINÚA")


# ============================================================
# EJERCICIOS PARA LOS ALUMNOS
# ============================================================
#
# 1...... ¿Qué pasaría si no eliminamos los duplicados?
# Los datos no serian precisos...
# 2...... ¿Por qué cliente_id no debe utilizarse como variable predictora?
# Por que puede repetirse en registros del mismo cliente
# 3...... ¿Por qué separamos train/test antes de normalizar?
# Separamos ANTES de normalizar.
# Si normalizamos todo el dataset primero, usamos información del test
# para preparar el entrenamiento. Eso se llama DATA LEAKAGE.
# 4...... Si queremos detectar la mayor cantidad posible de clientes que abandonarán, ¿qué métrica sería especialmente importante?
# sumar la cantidad de clientes cuyo 'riesgo_predicho' sea alto
# 
# 5...... Cambiá test_size de 0.20 a 0.30 y compará las métricas.
# con 0.20 es======
# === 12. CLIENTES CON MAYOR RIESGO ===
#     cliente_id  probabilidad_abandono riesgo_predicho
# 230      C0231               0.889774            ALTO
# 168      C0169               0.886694            ALTO
# 196      C0197               0.769163            ALTO
# 48       C0049               0.717091            ALTO
# 101      C0102               0.706114            ALTO
# 242      C0243               0.696171           MEDIO
# 63       C0064               0.689923           MEDIO
# 56       C0057               0.678558           MEDIO
# 78       C0079               0.646011           MEDIO
# 244      C0245               0.626043           MEDIO

# Archivo generado: clientes_con_prediccion.xlsx

# === 13. CLIENTE NUEVO ===
# Probabilidad de abandono: 63.57%
# Predicción: ABANDONA
# =====================================
# con 0.30 es======
# === 12. CLIENTES CON MAYOR RIESGO ===
#     cliente_id  probabilidad_abandono riesgo_predicho
# 168      C0169               0.949498            ALTO
# 230      C0231               0.904761            ALTO
# 196      C0197               0.784324            ALTO
# 63       C0064               0.772138            ALTO
# 242      C0243               0.742826            ALTO
# 78       C0079               0.716961            ALTO
# 56       C0057               0.716150            ALTO
# 48       C0049               0.705033            ALTO
# 147      C0148               0.689901           MEDIO
# 244      C0245               0.688440           MEDIO

# Archivo generado: clientes_con_prediccion.xlsx

# === 13. CLIENTE NUEVO ===
# Probabilidad de abandono: 56.86%
# Predicción: ABANDONA
# # 
# # 6...... Probá RandomForestClassifier y compará el resultado.
# # 
# # 
