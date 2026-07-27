# G9-LATAM-Team-51
⚡ EnergiAI – Inteligencia para el Consumo Energético. Una solución inteligente capaz de analizar patrones de consumo de energía eléctrica y generar información que ayude en la toma de decisiones relacionadas con la eficiencia energética.

## Estructura

```
G9-LATAM-Team-51/
├── docs/
│   ├── category_definition.md       # especificación metodológica ideal-relative-v1
│   └── model_training.md            # entrenamiento, evaluación y resultados
├── data/processed/
│   ├── ideal_monthly_features.csv               # 555×13, hogar-mes elegibles sin etiquetar (sin auditoría)
│   ├── ideal_monthly_features_labeled.csv       # 555×22, canónico (CSV)
│   ├── ideal_monthly_features_labeled.parquet   # 555×22, canónico (parquet)
│   ├── ideal_monthly_audit.parquet              # 555×11, sidecar de auditoría
│   ├── label_metadata.json                      # referencias congeladas, terciles, diagnósticos
│   └── ideal_127_viviendas_diario_PRE_PARITY_DEPRECATED.parquet  # anexo legado (análisis previo)
└── notebooks/
    ├── 01_limpieza_ideal.py                # fuente del notebook 01 (Jupytext percent)
    ├── 01_limpieza_ideal.ipynb              # notebook 01: limpieza, variables, categorías
    ├── 02_eda_ideal.py                     # fuente del notebook 02 (Jupytext percent)
    ├── 02_eda_ideal.ipynb                  # notebook 02: EDA y análisis de patrones
    ├── 01_limpieza_ideal_previo.ipynb      # anexo legado (análisis previo)
    ├── 02_eda_ideal_previo.ipynb            # anexo legado (análisis previo)
    ├── 03_entrenamiento_evaluacion.py       # fuente reproducible del entrenamiento
    └── 03_entrenamiento_evaluacion.ipynb    # notebook de entrenamiento y evaluación
├── reports/                                 # métricas, matrices y gráficos del modelo
├── models/                                  # ONNX, joblib, contrato y checksums
├── scripts/
│   └── export_model_artifacts.py            # exportación y prueba Python↔ONNX
└── requirements-model.txt                   # dependencias del entrenamiento
```

## Cómo reproducir

### Opción A — Auditar la lógica (rápido, ~10 min)

Ejecutar `notebooks/01_limpieza_ideal.ipynb` en Google Colab o localmente. Por
defecto procesa solo 8 hogares (`IDEAL_MAX_HOMES=8`) como muestra didáctica.
Los inputs se buscan en `/content/drive/MyDrive/IDEAL/` (Colab) o
`../data/raw/` (local). Ver `notebooks/01_limpieza_ideal.py` para más detalles
de resolución de rutas.

### Opción B — Regenerar el dataset canónico (~2 h)

El script paralelo `de_zip_a_category_local.py` (mantenido fuera del repo,
en el entorno local de generación) procesa los 254 hogares con 12 workers
y produce los 4 artefactos canónicos en `data/processed/`. No es necesario
ejecutarlo para esta entrega; los artefactos ya están en el repo.

## Entorno validado

```
Python          3.10.0
numpy           2.2.6
pandas          2.3.3
scipy           1.15.3
scikit-learn    1.7.2
jupytext        1.19.4
pyarrow         (para parquet)
matplotlib      (para EDA)
```

## Advertencia metodológica

Las categorías `Eficiente`, `Moderado`, `Ineficiente` son **pseudoetiquetas
relativas** construidas a partir de patrones del dataset IDEAL (Edimburgo,
2016–2018). No son certificaciones energéticas oficiales, no son comparables
con ratings A–G, **no son aptas para facturación**, y no son directamente
generalizables a viviendas latinoamericanas sin validación externa previa.

Ver `docs/category_definition.md` para la advertencia completa.

## Contribución de cada integrante

| Artefacto | Autoría | Estado |
| --- | --- | --- |
| `01_limpieza_ideal_previo.ipynb`, `02_eda_ideal_previo.ipynb`, `..._DIARIO_PRE_PARITY_DEPRECATED.parquet` | Análisis previo | Antecedente exploratorio conservado |
| `01_limpieza_ideal.*`, `02_eda_ideal.*`, `docs/category_definition.md`, `data/processed/ideal_monthly_features*`, `ideal_monthly_audit.parquet`, `label_metadata.json` | Esta entrega | Continuación metodológica |
| `03_entrenamiento_evaluacion.*`, `scripts/export_model_artifacts.py`, `models/*`, `docs/model_training.md`, `reports/*`, `requirements-model.txt` | Tomás Maldonado (TM) | Entrenamiento, evaluación y serialización completados |

## Entrenamiento, API y OCI

- **Entrenamiento y evaluación:** completados. Ver `docs/model_training.md`.
- **Serialización joblib/ONNX y prueba de paridad:** completadas por Datos.
- **Consumo del ONNX desde Java:** responsabilidad del equipo de Backend.
- **API REST** y **backend Java/Spring Boot** son responsabilidad del equipo de Backend.
- **OCI** es responsabilidad del equipo de DevOps.
- Ver `docs/category_definition.md` sección 14 para el contrato del dataset que recibe el equipo de entrenamiento.
