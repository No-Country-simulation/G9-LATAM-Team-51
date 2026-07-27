# Artefactos en `data/processed/`

## Tabla de artefactos

| Archivo | Estado | Filas × Cols | Uso |
| --- | --- | --- | --- |
| `ideal_monthly_features.csv` | Canónico | 555 × 13 | Filas hogar-mes elegibles, sin etiquetar (las 8 columnas de auditoría viven solo en el sidecar) |
| `ideal_monthly_features_labeled.csv` | Canónico | 555 × 22 | Dataset etiquetado (CSV, auditable) |
| `ideal_monthly_features_labeled.parquet` | Canónico | 555 × 22 | Dataset etiquetado (parquet, eficiente) |
| `ideal_monthly_audit.parquet` | Sidecar | 555 × 11 | Variables descriptivas (potencia promedio, máxima, consumo nocturno) |
| `label_metadata.json` | Canónico | — | Referencias congeladas, terciles, diagnósticos, audit_schema |
| `ideal_127_viviendas_diario_PRE_PARITY_DEPRECATED.parquet` | Legado | 30.732 × 7 | Anexo exploratorio diario del análisis previo; no alimentar al modelo |

## Reglas de uso

- **Backend y Data Science:** deben cargar `ideal_monthly_features_labeled.parquet` (555 × 22). Ese es el único dataset canónico.
- **Las 5 features del endpoint son:** `consumo_kwh`, `uso_horario_pico`, `cantidad_equipos`, `tipo_inmueble`, `horas_alto_consumo`.
- **No usar como predictores:** `homeid`, `year_month`, `month_coverage`, `peak_coverage`, `peak_energy_share`, `complete_day_ratio`, `observed_kwh`, `source_member`, columnas del sidecar audit.
- **`homeid`** debe usarse como grupo en CV (`GroupKFold` o `StratifiedGroupKFold`).
- **Sidecar audit:** únicamente para EDA, no entra al modelo.
- **Anexo legado:** únicamente para evolución diaria descriptiva (gráfico de líneas por hogar); no utilizar para entrenar ni para reconstruir las variables del endpoint.