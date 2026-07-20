# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     formats: py:percent,ipynb
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.4
# ---

# %% [markdown]
# # `01_limpieza_ideal.ipynb` — Limpieza, variables y categorías
#
# > **Estado:** continuación y ampliación de los notebooks `01_limpieza_ideal_previo.ipynb`
# > y `02_eda_ideal_previo.ipynb`. Conserva el trabajo de mapeo de streams y
# > selección inicial de 127 viviendas como antecedente exploratorio; añade
# > corrección horaria (UTC→Europe/London), cobertura, metadata, unidad
# > hogar-mes, variables del endpoint y pseudoetiquetas reproducibles.
#
# Este archivo usa el formato *percent* de Jupyter: cada marcador `# %%` es una
# celda de código y cada `# %% [markdown]` es una celda Markdown. Puede abrirse
# directamente como cuaderno en editores compatibles o convertirse con:
#
# ```bash
# uvx --from jupytext==1.19.4 jupytext --to ipynb notebooks/01_limpieza_ideal.py
# ```
#
# El objetivo es reproducir, paso a paso y sin archivos derivados previos, la
# construcción de un dataset hogar-mes y de sus pseudoetiquetas relativas. Las
# únicas entradas son dos archivos originales de IDEAL:
#
# 1. `household_sensors.zip`: lecturas de potencia de red a 1 Hz.
# 2. `ideal_metadata_and_surveys.zip`:
#    - `metadata/home.csv` aporta `hometype`;
#    - `metadata/appliance.csv` aporta los equipos eléctricos declarados.
#
# El procesamiento se deja deliberadamente secuencial para que la lógica sea
# fácil de seguir en un cuaderno. Se lee cada stream en *streaming*: no se
# extrae el ZIP de sensores ni se carga una vivienda completa en memoria. La
# ejecución del universo puede tardar varias horas; esto no cambia las reglas
# metodológicas ni los resultados respecto de otra estrategia de ejecución.
#
# Se generan cinco artefactos en `IDEAL_OUTPUT_DIR` o, por defecto, junto al ZIP
# de sensores:
#
# - `ideal_monthly_features.csv`;
# - `ideal_monthly_features_labeled.csv`;
# - `ideal_monthly_features_labeled.parquet`;
# - `ideal_monthly_audit.parquet` (sidecar);
# - `label_metadata.json`.
#
# **Advertencia:** IDEAL no incluye una etiqueta oficial de eficiencia. Las
# categorías construidas aquí son pseudoetiquetas relativas, no ratings A-G.
#
# Entorno con el que se validaron los resultados de referencia: Python 3.10.0,
# numpy 2.2.6, pandas 2.3.3, scipy 1.15.3, scikit-learn 1.7.2, pyarrow y matplotlib.

# %% [markdown]
# ## Mapeo a la tarjeta Trello "Creación de variables"
#
# | Solicitud Trello | Implementación | Sección `category_definition.md` |
# |---|---|---|
# | Consumo mensual | `consumo_kwh` (ajustado por cobertura mensual) | §5.1 |
# | Potencia promedio | Sidecar `potencia_promedio_w` (no feature del modelo) | §5.5 |
# | Potencia máxima | Sidecar `potencia_maxima_w` (no feature del modelo) | §5.5 |
# | Uso en horario pico | `uso_horario_pico` (booleano: `peak_energy_share > 0,25`) | §5.2 |
# | Consumo nocturno | Sidecar `consumo_nocturno_kwh` (no feature del modelo) | §5.5 |
# | Horas de alto consumo | `horas_alto_consumo` (entero 0–24) | §5.3 |
# | Variación del consumo entre períodos | Se calcula en notebook 02, solo entre meses consecutivos | — |
#
# ## Features vs. auditoría
#
# El dataset canónico `ideal_monthly_features_labeled.parquet` contiene las
# **5 features del endpoint** y el score + categoria + split + columnas de
# auditoría de calidad de medición. El sidecar `ideal_monthly_audit.parquet`
# contiene las **variables descriptivas adicionales** (potencia promedio,
# potencia máxima, consumo nocturno). La separación asegura que ninguna
# variable fuera de las 5 exigidas entre al modelo.
#
# ## Modo de ejecución
#
# - **Por defecto:** `IDEAL_MAX_HOMES=8` (muestra didáctica, ~10 min en Colab).
# - **Universo completo:** no ejecutar en Colab (12 h límite). Usar el script
#   local `de_zip_a_category_local.py` con 6 workers (~2 h). Los artefactos
#   canónicos ya están entregados en `data/processed/`.

# %% [markdown]
# ## Corrección 1 — Huso horario local
#
# Esta versión localiza los timestamps a `Europe/London` antes de evaluar la
# ventana pico y los límites de mes. La versión previa usaba timestamps naive
# y desplazaba una hora las ventanas durante BST. Ver `docs/category_definition.md`
# §4 y §5.2.

# %% [markdown]
# ## Corrección 2 — Días DST-aware
#
# Los días con cambio de horario de verano (último domingo de marzo y de
# octubre en UK) tienen 23 o 25 horas reales, no 24. Esta versión calcula
# `expected_hours_local_day` dinámicamente. Ver `docs/category_definition.md`
# §5.1 y §5.3.

# %% [markdown]
# ## Corrección 3 — Intervalo defectuoso del 17 de abril de 2018
#
# Cita literal de `ideal_documentation.zip → documentation/IDEALdata.md`
# línea 365:
#
# > All sensor data in the hour between 08:50 and 09:50 on 17th April 2018
# > should be considered unreliable. Due to a server error, too many data
# > points are recorded during this time.
#
# Se excluye el intervalo `2018-04-17 08:50:00 UTC ≤ ts < 2018-04-17 09:50:00 UTC`
# antes de acumular consumo, coberturas y horas. Ver
# `docs/category_definition.md` §4.

# %% [markdown]
# ## Corrección 4 — Unidad hogar-mes
#
# La unidad canónica es **un hogar durante un mes calendario** (`hogar-mes`),
# no un hogar durante un día. La variable `consumo_kwh` del endpoint es mensual;
# la versión previa solo producía agregados diarios que no podían reconstruirse
# a consumo mensual ajustado sin re-procesar. Ver `docs/category_definition.md`
# §1 y §5.

# %% [markdown]
# ## Corrección 5 — Potencia vs energía
#
# Las lecturas de IDEAL son **potencia instantánea en watts** a 1 Hz, no
# energía. La conversión a energía es `observed_kwh = Σ potencia_watts /
# 3.600.000`. La versión previa guardaba `potencia_promedio` (media de medias
# horarias) que no permite reconstruir `observed_kwh` ni ajustar por cobertura.
# Ver `docs/category_definition.md` §4 y §5.1.

# %% [markdown]
# ## Corrección 6 — Ajuste por cobertura
#
# Meses con menos del 90% de los segundos esperados se excluyen; los que
# pasan el umbral se ajustan explícitamente por su cobertura respectiva:
# `consumo_kwh = observed_kwh / month_coverage` y
# `adjusted_peak_kwh = observed_peak_kwh / peak_coverage`. La versión previa
# trataba días de 20 horas como completos. Ver `docs/category_definition.md`
# §5.1 y §6.

# %% [markdown]
# ## Corrección 7 — Universo por calidad, no muestreo
#
# El universo de **151 hogares elegibles** es resultado de aplicar los
# umbrales de calidad, no un muestreo aleatorio. La versión previa seleccionaba
# 127 hogares con `sample(n=127, random_state=42)` sin criterio de cobertura;
# solo 76 de esos 127 intersectan con los 151 válidos. Ver
# `docs/category_definition.md` §3.3 y §6.

# %% [markdown]
# ## Corrección 8 — Cruce con metadata oficial
#
# Este pipeline cruza `homeid` con `metadata/home.csv` (para `tipo_inmueble`)
# y `metadata/appliance.csv` (para `cantidad_equipos`). La versión previa no
# incluía estas dos variables del endpoint. Ver `docs/category_definition.md`
# §3.2–§3.3.

# %% [markdown]
# ## Corrección 9 — Horario pico y horas de alto consumo
#
# Se introducen tres variables derivadas del comportamiento horario:
# `peak_energy_share` (proporción de energía consumida en la ventana 17:00–21:00
# local ajustada por su propia cobertura), `uso_horario_pico` (booleano:
# `peak_energy_share > 0,25`) y `horas_alto_consumo` (promedio diario de horas
# con consumo ajustado superior a 0,5 kWh/h, redondeado a entero 0–24). La
# versión previa no producía ninguna de estas tres variables. Ver
# `docs/category_definition.md` §5.2–§5.4.

# %% [markdown]
# ## Corrección 10 — Split por hogar y terciles congelados
#
# El split train/test se hace por vivienda (`homeid`), estratificado por
# `tipo_inmueble`, con `random_state=42` sobre hogares ordenados por `homeid`.
# Los percentiles y los terciles `t1` y `t2` se calculan exclusivamente con
# train y se congelan para aplicar a test. La versión previa no producía split
# ni categorías. Ver `docs/category_definition.md` §7–§10.

# %% [markdown]
# ## Corrección 11 — Reproducibilidad
#
# Este notebook no requiere recargar CSV ni aplicar workarounds para errores
# tipo `ArrowKeyError`. Toda la generación del parquet etiquetado se hace de
# principio a fin desde los ZIP originales con el mismo script. Los outputs
# son reproducibles y auditables por hash. Ver `docs/category_definition.md`
# §12–§13.

# %% [markdown]
# ## Advertencia sobre el modo de ejecución
#
# > Este notebook se ejecuta por defecto con `IDEAL_MAX_HOMES=8` para que sea
# > auditable en Colab en ~10 minutos. El dataset canónico completo (555
# > filas, 151 hogares) se generó con el script paralelo
# > `de_zip_a_category_local.py` (~2 h con 6 workers) y se entrega como
# > artefacto en `data/processed/ideal_monthly_features_labeled.parquet`.
# > No es necesario ejecutar este notebook sobre el universo completo para
# > reproducir los artefactos; basta con auditar la lógica.

# %%

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import math
import os
import re
import time
import zipfile
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from sklearn.model_selection import train_test_split

try:
    from IPython.display import display as notebook_display
except ImportError:

    def notebook_display(value: Any) -> None:
        """Fallback de display cuando el archivo se ejecuta como script Python."""
        print(value)


RUN_PIPELINE = __name__ == "__main__"


# %% [markdown]
# ## 1. Configuración metodológica
#
# Todos los umbrales y pesos se concentran aquí. Los meses principales exigen
# 90% de cobertura total, 90% de cobertura en horario pico y al menos 80% de
# días utilizables. El corte de 90% conserva más viviendas que 95%, pero sigue
# exigiendo alta cobertura y registra el ajuste aplicado a la energía.

# %%

TZ_LOCAL = ZoneInfo("Europe/London")
TZ_UTC = ZoneInfo("UTC")
WATTS_TO_KWH = 1.0 / 3_600_000.0
CATEGORY_METHOD_VERSION = "ideal-relative-v1"
AUDIT_SCHEMA_VERSION = "ideal-audit-v1"
AUDIT_COLUMNS = [
    "homeid",
    "year_month",
    "potencia_promedio_w",
    "potencia_maxima_w",
    "night_valid_seconds",
    "night_expected_seconds",
    "observed_night_kwh",
    "night_coverage",
    "consumo_nocturno_kwh",
    "night_eligible",
    "audit_schema_version",
]

CONFIG = {
    "month_coverage_threshold": 0.90,
    "peak_coverage_threshold": 0.90,
    "hour_coverage_threshold": 0.90,
    "day_coverage_threshold": 0.90,
    "monthly_complete_days_threshold": 0.80,
    "peak_start_local_hour": 17,
    "peak_end_local_hour": 21,
    "peak_share_boolean_threshold": 0.25,
    "high_consumption_kwh_per_hour": 0.5,
    "maximum_plausible_watts": 30_000.0,
    "night_coverage_threshold": 0.90,
    "night_start_local_hour": 22,
    "night_end_local_hour_exclusive": 6,
    "test_size": 0.25,
    "random_state": 42,
}

WEIGHTS = {
    "percentile_consumo": 0.60,
    "peak_component": 0.20,
    "high_hours_component": 0.15,
    "percentile_equipos": 0.05,
}

EXPECTED_CLASSES = ["Eficiente", "Moderado", "Ineficiente"]
ALLOWED_HOME_TYPES = {"Casa", "Departamento"}
FEATURE_COLUMNS = [
    "consumo_kwh",
    "uso_horario_pico",
    "cantidad_equipos",
    "tipo_inmueble",
    "horas_alto_consumo",
]

# Contrato canónico del CSV no etiquetado (555×13). Las 8 columnas de
# auditoría viven únicamente en ideal_monthly_audit.parquet.
MONTHLY_COLUMNS = [
    "homeid",
    "year_month",
    *FEATURE_COLUMNS,
    "month_coverage",
    "peak_coverage",
    "peak_energy_share",
    "complete_day_ratio",
    "observed_kwh",
    "source_member",
]

HOMETYPE_MAP = {
    "flat": "Departamento",
    "house_or_bungalow": "Casa",
}

# Un match por vivienda identifica el medidor de consumo eléctrico general.
MAIN_PATTERN = re.compile(
    r"^sensordata/home(\d+)_.*_electric-mains_electric-combined\.csv\.gz$"
)

DEFECTIVE_INTERVAL_START = datetime(2018, 4, 17, 8, 50, tzinfo=TZ_UTC)
DEFECTIVE_INTERVAL_END = datetime(2018, 4, 17, 9, 50, tzinfo=TZ_UTC)


# %% [markdown]
# ### Comprobación visible de la configuración
#
# La primera salida permite revisar los umbrales y pesos antes de tocar los
# archivos. Los pesos deben sumar 1 y las coberturas principales deben ser 90%.

# %%

if RUN_PIPELINE:
    configuration_view = pd.DataFrame(
        [
            {"grupo": "configuración", "parámetro": key, "valor": value}
            for key, value in CONFIG.items()
        ]
        + [
            {"grupo": "peso", "parámetro": key, "valor": value}
            for key, value in WEIGHTS.items()
        ]
    )
    notebook_display(configuration_view)
    print(f"Suma de pesos: {sum(WEIGHTS.values()):.2f}")


# %% [markdown]
# ## 2. Localización de los dos ZIP originales
#
# Los archivos pueden colocarse en el directorio actual, junto a este archivo
# o en `/content/drive/MyDrive/IDEAL`. También pueden indicarse explícitamente:
#
# ```bash
# export IDEAL_ZIP_PATH=/ruta/household_sensors.zip
# export IDEAL_META_ZIP_PATH=/ruta/ideal_metadata_and_surveys.zip
# export IDEAL_OUTPUT_DIR=/ruta/salidas   # opcional
# ```

# %%


def resolve_original_zip(filename: str, environment_variable: str) -> Path:
    """Encuentra un ZIP original de IDEAL en Drive/Colab o local.

    Orden de búsqueda local (script en ``notebooks/``):
      1. /content/drive/MyDrive/IDEAL/ (Colab)
      2. ../data/raw/  (repo local — fixtures)
      3. ../  (repo local — alt, junto a README)
      4. ./   (junto al notebook)
    """
    explicit = os.environ.get(environment_variable)
    script_dir = (
        Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
    )
    candidates = (
        [Path(explicit).expanduser()]
        if explicit
        else [
            Path("/content/drive/MyDrive/IDEAL") / filename,
            script_dir.parent / "data" / "raw" / filename,
            script_dir.parent / filename,
            script_dir / filename,
        ]
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    attempted = "\n".join(f"  - {p}" for p in candidates)
    raise FileNotFoundError(
        f"No se encontró {filename}. Colóquelo en /content/drive/MyDrive/IDEAL/ "
        f"(Colab) o en ../data/raw/ (local), o defina {environment_variable}. "
        f"Rutas comprobadas:\n{attempted}"
    )


def resolve_sensors_zip() -> Path:
    return resolve_original_zip("household_sensors.zip", "IDEAL_ZIP_PATH")


def resolve_metadata_zip() -> Path:
    return resolve_original_zip("ideal_metadata_and_surveys.zip", "IDEAL_META_ZIP_PATH")


def output_directory(sensors_zip: Path) -> Path:
    configured = os.environ.get("IDEAL_OUTPUT_DIR")
    destination = Path(configured).expanduser() if configured else sensors_zip.parent
    destination.mkdir(parents=True, exist_ok=True)
    return destination.resolve()


# %% [markdown]
# ### Comprobación visible de las entradas
#
# Esta celda resuelve las rutas y muestra los tamaños. Si alguno de los ZIP no
# es el original esperado, el problema se detecta antes del procesamiento largo.

# %%

if RUN_PIPELINE:
    sensors_zip = resolve_sensors_zip()
    metadata_zip = resolve_metadata_zip()
    destination = output_directory(sensors_zip)
    input_view = pd.DataFrame(
        [
            {
                "entrada": "sensores",
                "archivo": sensors_zip.name,
                "ruta": str(sensors_zip),
                "tamaño": f"{sensors_zip.stat().st_size / 1e9:.2f} GB",
            },
            {
                "entrada": "metadata",
                "archivo": metadata_zip.name,
                "ruta": str(metadata_zip),
                "tamaño": f"{metadata_zip.stat().st_size / 1e6:.2f} MB",
            },
        ]
    )
    notebook_display(input_view)
    print(f"Directorio de salida: {destination}")


# %% [markdown]
# ## 3. Lectura de metadata y descubrimiento de viviendas
#
# No se mantiene un listado manual de viviendas. El procedimiento:
#
# 1. lee `hometype` desde `metadata/home.csv`;
# 2. suma `number` para appliances con `powertype == "electric"` en
#    `metadata/appliance.csv`;
# 3. descubre en el ZIP de sensores cada miembro cuyo nombre termina en
#    `electric-mains_electric-combined.csv.gz`;
# 4. cruza las tres fuentes por `homeid`.
#
# De esta forma el manifiesto queda derivado exclusivamente de los archivos
# originales y puede auditarse en cada ejecución.

# %%


def load_metadata_zip(metadata_zip: Path) -> tuple[dict[int, str], dict[int, int]]:
    """Devuelve homeid→hometype y homeid→cantidad de equipos eléctricos."""
    with zipfile.ZipFile(metadata_zip) as archive:
        with archive.open("metadata/home.csv") as raw_home:
            reader = csv.DictReader(io.TextIOWrapper(raw_home, encoding="utf-8-sig"))
            home_types: dict[int, str] = {}
            for row in reader:
                try:
                    home_types[int(row["homeid"])] = row["hometype"]
                except (KeyError, ValueError):
                    continue

        with archive.open("metadata/appliance.csv") as raw_appliance:
            reader = csv.DictReader(
                io.TextIOWrapper(raw_appliance, encoding="utf-8-sig")
            )
            equipment_counts: dict[int, int] = defaultdict(int)
            for row in reader:
                if row.get("powertype") != "electric":
                    continue
                try:
                    equipment_counts[int(row["homeid"])] += int(row.get("number") or 0)
                except (KeyError, ValueError):
                    continue

    return home_types, dict(equipment_counts)


def discover_manifest(
    sensors_zip: Path,
    home_types: dict[int, str],
    equipment_counts: dict[int, int],
    max_homes: int | None = None,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Descubre medidores generales y los cruza con la metadata oficial.

    Si ``max_homes`` no es None, limita el manifiesto a los primeros N hogares
    (ordenados por homeid). El summary se calcula sobre el universo completo
    para que los controles sigan siendo informativos.
    """
    members_by_home: dict[int, str] = {}
    with zipfile.ZipFile(sensors_zip) as archive:
        for member in archive.namelist():
            match = MAIN_PATTERN.match(member)
            if match:
                home_id = int(match.group(1))
                if home_id in members_by_home:
                    raise ValueError(
                        "Más de un medidor electric-mains_combined para "
                        f"homeid={home_id}: {members_by_home[home_id]} y {member}."
                    )
                members_by_home[home_id] = member

    sorted_items = sorted(members_by_home.items())
    if max_homes is not None:
        sorted_items = sorted_items[:max_homes]

    manifest = []
    for home_id, member in sorted_items:
        raw_home_type = home_types.get(home_id, "unknown")
        manifest.append(
            {
                "homeid": home_id,
                "tipo_inmueble": HOMETYPE_MAP.get(raw_home_type, "Desconocido"),
                "hometype_raw": raw_home_type,
                "cantidad_equipos": equipment_counts.get(home_id, 0),
                "source_member": member,
            }
        )

    summary = {
        "n_hogares_en_zip": len(members_by_home),
        "n_con_hometype": sum(home_id in home_types for home_id in members_by_home),
        "n_sin_hometype": sum(home_id not in home_types for home_id in members_by_home),
        "n_con_equipos": sum(
            home_id in equipment_counts for home_id in members_by_home
        ),
    }
    return manifest, summary


def validate_manifest(manifest: list[dict[str, Any]]) -> None:
    """Falla temprano si la metadata necesaria no cubre todos los medidores."""
    if not manifest:
        raise ValueError(
            "household_sensors.zip no contiene medidores electric-mains_combined."
        )
    missing_type = [
        row["homeid"] for row in manifest if row["tipo_inmueble"] == "Desconocido"
    ]
    missing_equipment = [
        row["homeid"] for row in manifest if row["cantidad_equipos"] < 1
    ]
    if missing_type or missing_equipment:
        raise ValueError(
            "El cruce con la metadata oficial está incompleto. "
            f"Sin tipo: {missing_type}; sin equipos eléctricos: {missing_equipment}."
        )


# %% [markdown]
# ### Resultado visible del cruce de metadata
#
# Deben aparecer 254 viviendas, todas con tipo y equipos. La tabla de muestra
# permite comprobar cómo `hometype` y `number` se convierten en las variables
# que luego consumirá el clasificador.

# %%

if RUN_PIPELINE:
    # Por defecto limita a 8 hogares para auditar la lógica en Colab (~10 min).
    # Para ejecutar el universo completo: export IDEAL_MAX_HOMES=0 (o un número grande).
    max_homes_env = int(os.environ.get("IDEAL_MAX_HOMES", "8"))
    max_homes = max_homes_env if max_homes_env > 0 else None
    home_types, equipment_counts = load_metadata_zip(metadata_zip)
    manifest, manifest_summary = discover_manifest(
        sensors_zip, home_types, equipment_counts, max_homes=max_homes
    )
    validate_manifest(manifest)
    print(f"Max-homes activo: {max_homes if max_homes is not None else 'universo completo'}")
    manifest_frame = pd.DataFrame(manifest)
    manifest_view = pd.DataFrame(
        [
            {
                "control": "hogares en ZIP",
                "valor": manifest_summary["n_hogares_en_zip"],
            },
            {"control": "con hometype", "valor": manifest_summary["n_con_hometype"]},
            {"control": "sin hometype", "valor": manifest_summary["n_sin_hometype"]},
            {"control": "con equipos", "valor": manifest_summary["n_con_equipos"]},
        ]
    )
    notebook_display(manifest_view)
    notebook_display(
        manifest_frame.groupby(["hometype_raw", "tipo_inmueble"])
        .agg(hogares=("homeid", "nunique"))
        .reset_index()
    )
    notebook_display(manifest_frame.head(10))


# %% [markdown]
# ## 4. Utilidades temporales y de serialización
#
# Los timestamps de los sensores se interpretan en UTC. La ventana pico y los
# límites de mes se evalúan en `Europe/London` para respetar los días de 23 o
# 25 horas ocasionados por el horario de verano.

# %%


def parse_timestamp(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.strip())
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(TZ_UTC).replace(tzinfo=None)
    return parsed


def month_bounds_local(year: int, month: int) -> tuple[datetime, datetime]:
    start = datetime(year, month, 1, tzinfo=TZ_LOCAL)
    end = (
        datetime(year + 1, 1, 1, tzinfo=TZ_LOCAL)
        if month == 12
        else datetime(year, month + 1, 1, tzinfo=TZ_LOCAL)
    )
    return start, end


def expected_seconds_month(year: int, month: int) -> int:
    start, end = month_bounds_local(year, month)
    return int((end.astimezone(TZ_UTC) - start.astimezone(TZ_UTC)).total_seconds())


def expected_night_seconds_month(year: int, month: int) -> int:
    """Segundos esperados en ventana nocturna [22:00, 24:00) ∪ [00:00, 06:00)
    hora local a lo largo del mes, asociados al día calendario local en que
    empieza la noche. Conversión DST-aware a UTC."""
    days = calendar_days(year, month)
    total = 0
    for d in range(1, days + 1):
        night_start = datetime(year, month, d, 22, 0, tzinfo=TZ_LOCAL)
        if d == days:
            if month == 12:
                night_end = datetime(year + 1, 1, 1, 6, 0, tzinfo=TZ_LOCAL)
            else:
                night_end = datetime(year, month + 1, 1, 6, 0, tzinfo=TZ_LOCAL)
        else:
            night_end = datetime(year, month, d + 1, 6, 0, tzinfo=TZ_LOCAL)
        total += int(
            (night_end.astimezone(TZ_UTC) - night_start.astimezone(TZ_UTC)).total_seconds()
        )
    return total


def calendar_days(year: int, month: int) -> int:
    start, end = month_bounds_local(year, month)
    return (end.date() - start.date()).days


def expected_hours_local_day(local_date: date) -> float:
    start = datetime(local_date.year, local_date.month, local_date.day, tzinfo=TZ_LOCAL)
    end = start + timedelta(days=1)
    return (end.astimezone(TZ_UTC) - start.astimezone(TZ_UTC)).total_seconds() / 3600.0


def json_ready(value: Any) -> Any:
    """Convierte escalares numpy y contenedores a tipos JSON nativos."""
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_ready(v) for v in value]
    if isinstance(value, np.ndarray):
        return [json_ready(v) for v in value.tolist()]
    if isinstance(value, np.generic):
        return value.item()
    if pd.isna(value) if not isinstance(value, (str, bool)) else False:
        return None
    return value


def sha256_of_file(path: Path) -> str:
    """SHA-256 streaming con chunks de 1 MiB."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


# %% [markdown]
# ## 5. Lecturas de 1 Hz → observaciones hogar-mes
#
# Para cada vivienda se recorren las lecturas una sola vez. En ese recorrido se
# descartan valores inválidos y se acumulan energía, segundos observados y
# estadísticas horarias. Después se calculan cobertura, consumo ajustado,
# proporción de energía pico y promedio diario de horas de alto consumo.
#
# La conversión energética es:
#
# ```text
# observed_kwh = suma(potencia_watts × 1 segundo) / 3.600.000
# consumo_kwh  = observed_kwh / month_coverage
# ```

# %%


def process_home_streaming(
    archive: zipfile.ZipFile, specification: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Procesa un stream de 1 Hz sin cargarlo completo en memoria."""
    months: dict[tuple[int, int], dict[str, float]] = defaultdict(
        lambda: {
            "valid_seconds": 0,
            "sum_watts": 0.0,
            "peak_valid_seconds": 0,
            "peak_sum_watts": 0.0,
            "maximum_watts": 0.0,
            "night_valid_seconds": 0,
            "night_sum_watts": 0.0,
        }
    )
    hours: dict[tuple[int, int, int, int], dict[str, float]] = defaultdict(
        lambda: {"valid_seconds": 0, "sum_watts": 0.0}
    )
    counters = {
        "rows_total": 0,
        "invalid_shape_or_timestamp": 0,
        "non_numeric_or_non_finite": 0,
        "negative_watts": 0,
        "over_maximum_watts": 0,
        "duplicate_timestamp": 0,
        "out_of_order_timestamp": 0,
        "defective_interval": 0,
        "rows_accepted": 0,
    }
    previous_timestamp: datetime | None = None

    member = specification["source_member"]
    with archive.open(member) as compressed:
        with gzip.open(
            compressed, mode="rt", encoding="utf-8", errors="replace"
        ) as stream:
            for raw_line in stream:
                counters["rows_total"] += 1
                parts = raw_line.rstrip("\n").split(",")
                if len(parts) < 2:
                    counters["invalid_shape_or_timestamp"] += 1
                    continue

                timestamp = parse_timestamp(parts[0])
                if timestamp is None:
                    counters["invalid_shape_or_timestamp"] += 1
                    continue

                try:
                    watts = float(parts[1])
                except ValueError:
                    counters["non_numeric_or_non_finite"] += 1
                    continue
                if not math.isfinite(watts):
                    counters["non_numeric_or_non_finite"] += 1
                    continue
                if watts < 0:
                    counters["negative_watts"] += 1
                    continue
                if watts > CONFIG["maximum_plausible_watts"]:
                    counters["over_maximum_watts"] += 1
                    continue

                if previous_timestamp is not None and timestamp <= previous_timestamp:
                    key = (
                        "duplicate_timestamp"
                        if timestamp == previous_timestamp
                        else "out_of_order_timestamp"
                    )
                    counters[key] += 1
                    continue
                previous_timestamp = timestamp

                timestamp_utc = timestamp.replace(tzinfo=TZ_UTC)
                if DEFECTIVE_INTERVAL_START <= timestamp_utc < DEFECTIVE_INTERVAL_END:
                    counters["defective_interval"] += 1
                    continue

                local_timestamp = timestamp_utc.astimezone(TZ_LOCAL)
                month_bucket = months[(local_timestamp.year, local_timestamp.month)]
                month_bucket["valid_seconds"] += 1
                month_bucket["sum_watts"] += watts
                if watts > month_bucket["maximum_watts"]:
                    month_bucket["maximum_watts"] = watts

                if (
                    CONFIG["peak_start_local_hour"]
                    <= local_timestamp.hour
                    < CONFIG["peak_end_local_hour"]
                ):
                    month_bucket["peak_valid_seconds"] += 1
                    month_bucket["peak_sum_watts"] += watts

                if (
                    local_timestamp.hour >= CONFIG["night_start_local_hour"]
                    or local_timestamp.hour < CONFIG["night_end_local_hour_exclusive"]
                ):
                    month_bucket["night_valid_seconds"] += 1
                    month_bucket["night_sum_watts"] += watts

                hour_key = (
                    timestamp_utc.year,
                    timestamp_utc.month,
                    timestamp_utc.day,
                    timestamp_utc.hour,
                )
                hours[hour_key]["valid_seconds"] += 1
                hours[hour_key]["sum_watts"] += watts
                counters["rows_accepted"] += 1

    day_stats: dict[date, dict[str, float]] = defaultdict(
        lambda: {
            "expected_hours": 0.0,
            "evaluable_hours": 0,
            "high_evaluable_hours": 0,
        }
    )
    for (year, month, day, hour), hour_bucket in hours.items():
        utc_hour = datetime(year, month, day, hour, tzinfo=TZ_UTC)
        local_date = utc_hour.astimezone(TZ_LOCAL).date()
        day_stats[local_date]["expected_hours"] = expected_hours_local_day(local_date)

        hour_coverage = hour_bucket["valid_seconds"] / 3600.0
        if hour_coverage < CONFIG["hour_coverage_threshold"]:
            continue
        day_stats[local_date]["evaluable_hours"] += 1
        observed_hour_kwh = hour_bucket["sum_watts"] * WATTS_TO_KWH
        adjusted_hour_kwh = observed_hour_kwh / hour_coverage
        if adjusted_hour_kwh > CONFIG["high_consumption_kwh_per_hour"]:
            day_stats[local_date]["high_evaluable_hours"] += 1

    month_rows: list[dict[str, Any]] = []
    for (year, month), month_bucket in sorted(months.items()):
        days_in_month = calendar_days(year, month)
        expected_seconds = expected_seconds_month(year, month)
        observed_kwh = month_bucket["sum_watts"] * WATTS_TO_KWH
        month_coverage = month_bucket["valid_seconds"] / expected_seconds
        adjusted_total_kwh = (
            observed_kwh / month_coverage if month_coverage > 0 else 0.0
        )

        peak_hours_per_day = (
            CONFIG["peak_end_local_hour"] - CONFIG["peak_start_local_hour"]
        )
        expected_peak_seconds = days_in_month * peak_hours_per_day * 3600
        peak_coverage = month_bucket["peak_valid_seconds"] / expected_peak_seconds
        observed_peak_kwh = month_bucket["peak_sum_watts"] * WATTS_TO_KWH
        adjusted_peak_kwh = (
            observed_peak_kwh / peak_coverage if peak_coverage > 0 else 0.0
        )
        peak_energy_share = (
            adjusted_peak_kwh / adjusted_total_kwh if adjusted_total_kwh > 0 else 0.0
        )

        usable_days = 0
        adjusted_high_hours: list[float] = []
        for day_number in range(1, days_in_month + 1):
            local_date = date(year, month, day_number)
            stats = day_stats.get(local_date)
            if not stats or stats["expected_hours"] <= 0:
                continue
            day_coverage = stats["evaluable_hours"] / stats["expected_hours"]
            if day_coverage < CONFIG["day_coverage_threshold"]:
                continue
            usable_days += 1
            adjusted = min(
                stats["high_evaluable_hours"] / day_coverage,
                stats["expected_hours"],
            )
            adjusted_high_hours.append(adjusted)

        complete_day_ratio = usable_days / days_in_month
        average_daily_high_hours = (
            sum(adjusted_high_hours) / len(adjusted_high_hours)
            if adjusted_high_hours
            else 0.0
        )
        high_hours_integer = min(24, math.floor(average_daily_high_hours + 0.5))

        exclusion_reasons = []
        if month_coverage < CONFIG["month_coverage_threshold"]:
            exclusion_reasons.append("month_coverage")
        if peak_coverage < CONFIG["peak_coverage_threshold"]:
            exclusion_reasons.append("peak_coverage")
        if complete_day_ratio < CONFIG["monthly_complete_days_threshold"]:
            exclusion_reasons.append("complete_day_ratio")
        if not (0.0 <= peak_energy_share <= 1.0):
            exclusion_reasons.append("peak_energy_share")
        if adjusted_total_kwh <= 0:
            exclusion_reasons.append("consumo_kwh")

        # Variables descriptivas de auditoría (sidecar ideal_monthly_audit.parquet).
        potencia_promedio_w = (
            month_bucket["sum_watts"] / month_bucket["valid_seconds"]
            if month_bucket["valid_seconds"] > 0
            else 0.0
        )
        potencia_maxima_w = month_bucket["maximum_watts"]
        night_expected_seconds = expected_night_seconds_month(year, month)
        night_coverage = (
            month_bucket["night_valid_seconds"] / night_expected_seconds
            if night_expected_seconds > 0
            else 0.0
        )
        observed_night_kwh = month_bucket["night_sum_watts"] * WATTS_TO_KWH
        if night_coverage >= CONFIG["night_coverage_threshold"]:
            consumo_nocturno_kwh = observed_night_kwh / night_coverage
            night_eligible = True
        else:
            consumo_nocturno_kwh = None
            night_eligible = False

        month_rows.append(
            {
                "homeid": int(specification["homeid"]),
                "year_month": f"{year:04d}-{month:02d}",
                "consumo_kwh": round(adjusted_total_kwh, 6),
                "uso_horario_pico": bool(
                    peak_energy_share > CONFIG["peak_share_boolean_threshold"]
                ),
                "cantidad_equipos": int(specification["cantidad_equipos"]),
                "tipo_inmueble": specification["tipo_inmueble"],
                "horas_alto_consumo": int(high_hours_integer),
                "month_coverage": round(month_coverage, 6),
                "peak_coverage": round(peak_coverage, 6),
                "peak_energy_share": round(peak_energy_share, 6),
                "complete_day_ratio": round(complete_day_ratio, 6),
                "observed_kwh": round(observed_kwh, 6),
                "source_member": member,
                "eligible": not exclusion_reasons,
                "exclusion_reasons": ";".join(exclusion_reasons),
                "potencia_promedio_w": round(float(potencia_promedio_w), 6),
                "potencia_maxima_w": float(potencia_maxima_w),
                "night_valid_seconds": int(month_bucket["night_valid_seconds"]),
                "night_expected_seconds": int(night_expected_seconds),
                "observed_night_kwh": round(float(observed_night_kwh), 6),
                "night_coverage": round(float(night_coverage), 6),
                "consumo_nocturno_kwh": (
                    float(consumo_nocturno_kwh)
                    if consumo_nocturno_kwh is not None
                    else None
                ),
                "night_eligible": bool(night_eligible),
            }
        )

    counters["months_total"] = len(month_rows)
    counters["months_eligible"] = sum(bool(row["eligible"]) for row in month_rows)
    return month_rows, counters


def build_monthly_dataset(
    sensors_zip: Path, manifest: list[dict[str, Any]]
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Procesa secuencialmente los medidores descubiertos en el ZIP original."""
    all_rows: list[dict[str, Any]] = []
    quality: dict[str, Any] = {}

    with zipfile.ZipFile(sensors_zip) as archive:
        for index, specification in enumerate(manifest, start=1):
            started = time.time()
            rows, counters = process_home_streaming(archive, specification)
            counters["elapsed_seconds"] = round(time.time() - started, 3)
            home_key = str(specification["homeid"])
            quality[home_key] = counters
            all_rows.extend(rows)
            print(
                f"[{index}/{len(manifest)}] home={home_key}: "
                f"{counters['months_eligible']}/{counters['months_total']} meses elegibles, "
                f"{counters['elapsed_seconds']:.1f} s"
            )

    if not all_rows:
        raise RuntimeError("El ZIP no produjo ninguna fila mensual.")
    return pd.DataFrame(all_rows), quality


# %% [markdown]
# ### Ejecución y progreso de la agregación mensual
#
# Esta es la celda costosa. Muestra una línea por vivienda con meses elegibles,
# meses observados y duración. Al finalizar enseña las primeras filas **antes**
# de filtrar por calidad, de modo que también sean visibles los meses parciales.

# %%

if RUN_PIPELINE:
    processing_started = time.time()
    all_months, processing_quality = build_monthly_dataset(sensors_zip, manifest)
    processing_elapsed = time.time() - processing_started
    raw_monthly_view = pd.DataFrame(
        [
            {
                "métrica": "viviendas procesadas",
                "valor": all_months["homeid"].nunique(),
            },
            {"métrica": "filas hogar-mes", "valor": len(all_months)},
            {
                "métrica": "meses elegibles inicialmente",
                "valor": int(all_months["eligible"].sum()),
            },
            {"métrica": "duración minutos", "valor": round(processing_elapsed / 60, 2)},
        ]
    )
    notebook_display(raw_monthly_view)
    notebook_display(
        all_months[
            [
                "homeid",
                "year_month",
                "consumo_kwh",
                "month_coverage",
                "peak_coverage",
                "complete_day_ratio",
                "eligible",
                "exclusion_reasons",
            ]
        ].head(10)
    )


# %% [markdown]
# ## 6. Elegibilidad y validación del dataset mensual
#
# Una fila se conserva únicamente si cumple simultáneamente:
#
# ```text
# month_coverage      >= 0.90
# peak_coverage       >= 0.90
# complete_day_ratio  >= 0.80
# 0 <= peak_energy_share <= 1
# consumo_kwh > 0
# ```
#
# También se verifican nulos, duplicados hogar-mes, dominios de variables y
# constancia de tipo de inmueble y cantidad de equipos dentro de cada hogar.

# %%


def validate_monthly_dataset(frame: pd.DataFrame) -> None:
    required = FEATURE_COLUMNS + [
        "homeid",
        "year_month",
        "month_coverage",
        "peak_coverage",
        "peak_energy_share",
        "complete_day_ratio",
        "observed_kwh",
        "source_member",
    ]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"Faltan columnas mensuales obligatorias: {missing}")
    if frame.empty:
        raise ValueError("No hay meses elegibles para etiquetar.")

    nulls = frame[required].isna().sum()
    nulls = nulls[nulls > 0]
    if not nulls.empty:
        raise ValueError(f"Hay valores nulos en columnas obligatorias:\n{nulls}")

    duplicate = frame.duplicated(["homeid", "year_month"], keep=False)
    if duplicate.any():
        raise ValueError(
            "Hay duplicados hogar-mes:\n"
            f"{frame.loc[duplicate, ['homeid', 'year_month']].sort_values(['homeid', 'year_month'])}"
        )

    found_types = set(frame["tipo_inmueble"].unique())
    if found_types != ALLOWED_HOME_TYPES:
        raise ValueError(
            f"Se esperaban exactamente {sorted(ALLOWED_HOME_TYPES)} y se encontraron {sorted(found_types)}."
        )
    if (frame["cantidad_equipos"] < 1).any():
        raise ValueError("cantidad_equipos debe ser un entero positivo.")
    if not frame["horas_alto_consumo"].between(0, 24).all():
        raise ValueError("horas_alto_consumo debe estar entre 0 y 24.")
    if (frame["consumo_kwh"] <= 0).any():
        raise ValueError("consumo_kwh debe ser positivo.")
    if not frame["peak_energy_share"].between(0, 1).all():
        raise ValueError("peak_energy_share debe estar entre 0 y 1.")

    coverage_failure = frame[
        (frame["month_coverage"] < CONFIG["month_coverage_threshold"])
        | (frame["peak_coverage"] < CONFIG["peak_coverage_threshold"])
        | (frame["complete_day_ratio"] < CONFIG["monthly_complete_days_threshold"])
    ]
    if not coverage_failure.empty:
        raise ValueError(
            f"{len(coverage_failure)} filas incumplen los umbrales de cobertura."
        )

    for column in ("tipo_inmueble", "cantidad_equipos"):
        inconsistent = frame.groupby("homeid")[column].nunique() > 1
        if inconsistent.any():
            raise ValueError(
                f"{column} no es constante en los hogares: {list(inconsistent[inconsistent].index)}"
            )

    homes_per_type = frame.groupby("tipo_inmueble")["homeid"].nunique()
    if (homes_per_type < 2).any():
        raise ValueError(
            "Cada tipo requiere al menos dos hogares elegibles para el split estratificado: "
            f"{homes_per_type.to_dict()}"
        )


def calculate_coverage_sensitivity(frame: pd.DataFrame) -> dict[str, dict[str, int]]:
    """Cuenta filas y hogares al endurecer cobertura mensual y pico."""
    sensitivity: dict[str, dict[str, int]] = {}
    for threshold in (0.90, 0.92, 0.93, 0.94, 0.95):
        if threshold == CONFIG["month_coverage_threshold"]:
            rows = frame[frame["eligible"]]
        else:
            rows = frame[
                (frame["month_coverage"] >= threshold)
                & (frame["peak_coverage"] >= threshold)
                & (
                    frame["complete_day_ratio"]
                    >= CONFIG["monthly_complete_days_threshold"]
                )
                & frame["peak_energy_share"].between(0, 1)
                & (frame["consumo_kwh"] > 0)
            ]
        sensitivity[f"{threshold:.2f}"] = {
            "rows": int(len(rows)),
            "homes": int(rows["homeid"].nunique()),
        }
    return sensitivity


# %% [markdown]
# ### Resultado visible de los controles de calidad
#
# Se muestran el total conservado, las combinaciones exactas de exclusión y la
# sensibilidad al endurecer el 90% hasta 95%. La muestra final permite revisar
# las cinco variables que utilizará el modelo y sus columnas de auditoría.

# %%

if RUN_PIPELINE:
    eligible = (
        all_months[all_months["eligible"]]
        .drop(columns=["eligible", "exclusion_reasons"])
        .sort_values(["homeid", "year_month"])
        .reset_index(drop=True)
    )
    validate_monthly_dataset(eligible)
    exclusion_counts = (
        all_months.loc[~all_months["eligible"], "exclusion_reasons"]
        .value_counts()
        .rename_axis("combinación_de_exclusión")
        .reset_index(name="filas")
    )
    coverage_sensitivity = calculate_coverage_sensitivity(all_months)

    eligibility_view = pd.DataFrame(
        [
            {"métrica": "filas antes de elegibilidad", "valor": len(all_months)},
            {"métrica": "filas elegibles", "valor": len(eligible)},
            {"métrica": "filas excluidas", "valor": len(all_months) - len(eligible)},
            {"métrica": "hogares elegibles", "valor": eligible["homeid"].nunique()},
            {"métrica": "nulos", "valor": int(eligible.isna().sum().sum())},
            {
                "métrica": "duplicados hogar-mes",
                "valor": int(eligible.duplicated(["homeid", "year_month"]).sum()),
            },
        ]
    )
    notebook_display(eligibility_view)
    notebook_display(exclusion_counts)
    notebook_display(
        pd.DataFrame.from_dict(coverage_sensitivity, orient="index")
        .rename_axis("umbral_mensual_y_pico")
        .reset_index()
    )
    notebook_display(eligible.head(10))


# %% [markdown]
# ## 7. Split por vivienda, referencias de train y pseudoetiquetas
#
# El split se hace sobre hogares únicos y estratificado por tipo de inmueble.
# Antes de llamar a `train_test_split` se ordena por `homeid`: así
# `random_state=42` produce el mismo split aunque cambie el orden de lectura.
# Ninguna vivienda puede aparecer a la vez en train y test.
#
# Solamente train ajusta:
#
# - las distribuciones de referencia para percentiles de consumo y equipos;
# - los cortes `t1` y `t2` de los terciles del score.
#
# Esas referencias congeladas se aplican después tanto a train como a test.

# %%


def percentile_against_reference(value: float, reference: np.ndarray) -> float:
    reference = np.asarray(reference, dtype=float)
    if len(reference) == 0:
        return float("nan")
    less = int((reference < value).sum())
    equal = int((reference == value).sum())
    return (less + 0.5 * equal) / len(reference)


def apply_references(
    frame: pd.DataFrame,
    consumption_references: dict[str, np.ndarray],
    equipment_references: dict[str, np.ndarray],
) -> pd.DataFrame:
    transformed = frame.copy()
    transformed["percentile_consumo"] = np.nan
    transformed["percentile_equipos"] = np.nan
    for home_type in consumption_references:
        mask = transformed["tipo_inmueble"] == home_type
        transformed.loc[mask, "percentile_consumo"] = transformed.loc[
            mask, "consumo_kwh"
        ].apply(
            lambda value: percentile_against_reference(
                value, consumption_references[home_type]
            )
        )
        transformed.loc[mask, "percentile_equipos"] = transformed.loc[
            mask, "cantidad_equipos"
        ].apply(
            lambda value: percentile_against_reference(
                value, equipment_references[home_type]
            )
        )
    return transformed


def compute_score(frame: pd.DataFrame) -> np.ndarray:
    peak_component = frame["uso_horario_pico"].astype(float).to_numpy()
    high_hours_component = np.minimum(
        frame["horas_alto_consumo"].astype(float).to_numpy() / 12.0,
        1.0,
    )
    return (
        WEIGHTS["percentile_consumo"] * frame["percentile_consumo"].to_numpy()
        + WEIGHTS["peak_component"] * peak_component
        + WEIGHTS["high_hours_component"] * high_hours_component
        + WEIGHTS["percentile_equipos"] * frame["percentile_equipos"].to_numpy()
    )


def classify_score(score: float, lower: float, upper: float) -> str:
    if score < lower:
        return "Eficiente"
    if score <= upper:
        return "Moderado"
    return "Ineficiente"


def label_dataset(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    homes = (
        frame[["homeid", "tipo_inmueble"]]
        .drop_duplicates()
        .sort_values("homeid")
        .reset_index(drop=True)
    )
    train_homes, test_homes = train_test_split(
        homes,
        test_size=CONFIG["test_size"],
        random_state=CONFIG["random_state"],
        stratify=homes["tipo_inmueble"],
    )
    train_ids = set(int(value) for value in train_homes["homeid"])
    test_ids = set(int(value) for value in test_homes["homeid"])
    if train_ids & test_ids:
        raise RuntimeError(
            f"Leakage entre train y test: {sorted(train_ids & test_ids)}"
        )

    split_frame = frame.copy()
    split_frame["split"] = split_frame["homeid"].map(
        lambda home_id: "train" if int(home_id) in train_ids else "test"
    )
    train = split_frame[split_frame["split"] == "train"].copy()
    test = split_frame[split_frame["split"] == "test"].copy()

    consumption_references: dict[str, np.ndarray] = {}
    equipment_references: dict[str, np.ndarray] = {}
    train_counts: dict[str, dict[str, int]] = {}
    for home_type, group in train.groupby("tipo_inmueble"):
        unique_homes = group.drop_duplicates("homeid")
        consumption_references[home_type] = np.sort(
            group["consumo_kwh"].astype(float).to_numpy()
        )
        equipment_references[home_type] = np.sort(
            unique_homes["cantidad_equipos"].astype(float).to_numpy()
        )
        train_counts[home_type] = {
            "rows": int(len(group)),
            "homes": int(unique_homes["homeid"].nunique()),
        }

    missing_train_types = ALLOWED_HOME_TYPES - set(consumption_references)
    if missing_train_types:
        raise RuntimeError(
            f"Tipos sin referencia en train: {sorted(missing_train_types)}"
        )

    train_transformed = apply_references(
        train, consumption_references, equipment_references
    )
    test_transformed = apply_references(
        test, consumption_references, equipment_references
    )

    for transformed in (train_transformed, test_transformed):
        transformed["peak_component"] = transformed["uso_horario_pico"].astype(float)
        transformed["high_hours_component"] = np.minimum(
            transformed["horas_alto_consumo"].astype(float) / 12.0,
            1.0,
        )
        transformed["score"] = compute_score(transformed)
        if (
            transformed[["percentile_consumo", "percentile_equipos", "score"]]
            .isna()
            .any()
            .any()
        ):
            raise RuntimeError(
                "Se generaron NaN al aplicar referencias o calcular el score."
            )
        if not transformed["score"].between(0, 1).all():
            raise RuntimeError("El score salió del rango [0, 1].")

    train_scores = train_transformed["score"].to_numpy()
    lower = float(np.percentile(train_scores, 100.0 / 3.0, method="linear"))
    upper = float(np.percentile(train_scores, 200.0 / 3.0, method="linear"))
    if lower >= upper:
        raise RuntimeError(f"Colapso de terciles: t1={lower}, t2={upper}.")

    for transformed in (train_transformed, test_transformed):
        transformed["categoria"] = transformed["score"].map(
            lambda score: classify_score(float(score), lower, upper)
        )

    found_train_classes = set(train_transformed["categoria"].unique())
    if found_train_classes != set(EXPECTED_CLASSES):
        raise RuntimeError(
            f"Train no contiene las tres categorías: {sorted(found_train_classes)}"
        )

    labeled = pd.concat([train_transformed, test_transformed]).sort_values(
        ["homeid", "year_month"]
    )
    sample_flag = any(counts["homes"] < 30 for counts in train_counts.values())
    context = {
        "train_homeids": sorted(train_ids),
        "test_homeids": sorted(test_ids),
        "train_counts_by_type": train_counts,
        "sample_flag": bool(sample_flag),
        "train_size_note": (
            f"muestra reducida: {len(train_ids)} hogares y "
            f"{len(train_transformed)} filas hogar-mes de train; "
            "no representa el universo IDEAL"
            if sample_flag
            else ""
        ),
        "thresholds": {
            "method": "terciles_of_train_score",
            "t1": lower,
            "t2": upper,
        },
        "references": {
            home_type: {
                "consumo_n_train_rows": int(len(consumption_references[home_type])),
                "equipos_n_train_homes": int(len(equipment_references[home_type])),
                "consumo_sorted": consumption_references[home_type].tolist(),
                "equipos_sorted": equipment_references[home_type].tolist(),
            }
            for home_type in sorted(consumption_references)
        },
    }
    return labeled, context


# %% [markdown]
# ### Resultado visible del split y las pseudoetiquetas
#
# Estas salidas comprueban que cada hogar pertenece a un solo split, que ambos
# tipos están representados y que los terciles se ajustaron solo con train. El
# balance de test se observa, pero no se fuerza.

# %%

if RUN_PIPELINE:
    labeled, context = label_dataset(eligible)
    labeled_columns = [
        "homeid",
        "year_month",
        "split",
        *FEATURE_COLUMNS,
        "percentile_consumo",
        "percentile_equipos",
        "peak_component",
        "high_hours_component",
        "score",
        "categoria",
        "month_coverage",
        "peak_coverage",
        "peak_energy_share",
        "complete_day_ratio",
        "observed_kwh",
        "source_member",
    ]
    labeled_output = labeled[labeled_columns].copy()
    labeled_output["category_method_version"] = CATEGORY_METHOD_VERSION
    labeled_output["sample_flag"] = bool(context["sample_flag"])

    # Sidecar de auditoría: misma clave (homeid, year_month), columnas disjuntas
    # de FEATURE_COLUMNS. No alimenta score, categoría nielegibilidad.
    audit_subset = [
        "homeid",
        "year_month",
        "potencia_promedio_w",
        "potencia_maxima_w",
        "night_valid_seconds",
        "night_expected_seconds",
        "observed_night_kwh",
        "night_coverage",
        "consumo_nocturno_kwh",
        "night_eligible",
    ]
    audit_df = labeled[audit_subset].copy()
    audit_df["audit_schema_version"] = AUDIT_SCHEMA_VERSION
    audit_df = audit_df[AUDIT_COLUMNS]

    train_homeids = set(context["train_homeids"])
    test_homeids = set(context["test_homeids"])
    split_view = (
        labeled_output.groupby(["split", "tipo_inmueble"])
        .agg(filas=("homeid", "size"), hogares=("homeid", "nunique"))
        .reset_index()
    )
    class_view = pd.crosstab(
        labeled_output["split"], labeled_output["categoria"]
    ).reindex(columns=EXPECTED_CLASSES, fill_value=0)
    reference_view = pd.DataFrame(
        [
            {
                "tipo_inmueble": home_type,
                "filas_consumo_train": values["consumo_n_train_rows"],
                "hogares_equipos_train": values["equipos_n_train_homes"],
            }
            for home_type, values in context["references"].items()
        ]
    )

    notebook_display(split_view)
    notebook_display(class_view)
    notebook_display(reference_view)
    print(
        f"t1={context['thresholds']['t1']:.10f}; t2={context['thresholds']['t2']:.10f}"
    )
    print(
        f"Hogares compartidos entre train y test: {sorted(train_homeids & test_homeids)}"
    )
    print(f"sample_flag: {context['sample_flag']}")
    notebook_display(labeled_output.head(10))


# %% [markdown]
# ## 8. Diagnósticos descriptivos no bloqueantes
#
# Los diagnósticos no cambian filas ni categorías. Sirven para inspeccionar
# balance por tipo, estabilidad temporal, asociación con variables del score y
# sensibilidad del ajuste por cobertura. No constituyen validación externa.

# %%


def safe_spearman(left: pd.Series, right: pd.Series) -> float | None:
    valid = pd.concat([left, right], axis=1).dropna()
    if (
        len(valid) < 3
        or valid.iloc[:, 0].nunique() < 2
        or valid.iloc[:, 1].nunique() < 2
    ):
        return None
    statistic = spearmanr(valid.iloc[:, 0], valid.iloc[:, 1]).statistic
    return None if not math.isfinite(float(statistic)) else float(statistic)


def safe_pearson(left: pd.Series, right: pd.Series) -> float | None:
    valid = pd.concat([left, right], axis=1).dropna()
    if (
        len(valid) < 3
        or valid.iloc[:, 0].nunique() < 2
        or valid.iloc[:, 1].nunique() < 2
    ):
        return None
    statistic = pearsonr(valid.iloc[:, 0], valid.iloc[:, 1]).statistic
    return None if not math.isfinite(float(statistic)) else float(statistic)


def calculate_diagnostics(
    labeled: pd.DataFrame, context: dict[str, Any]
) -> dict[str, Any]:
    ordinal = {"Eficiente": 0, "Moderado": 1, "Ineficiente": 2}
    diagnostic_frame = labeled.copy()
    diagnostic_frame["categoria_ord"] = diagnostic_frame["categoria"].map(ordinal)

    balance = pd.crosstab(
        diagnostic_frame["tipo_inmueble"],
        diagnostic_frame["categoria"],
        normalize="index",
    ).reindex(columns=EXPECTED_CLASSES, fill_value=0.0)
    balance_percent = (balance * 100.0).round(4)
    balance_warning = bool((balance_percent < 10.0).any().any())

    ordered = diagnostic_frame.sort_values(["homeid", "year_month"]).copy()
    ordered["period"] = pd.PeriodIndex(ordered["year_month"], freq="M")
    ordered["previous_period"] = ordered.groupby("homeid")["period"].shift(1)
    ordered["previous_category"] = ordered.groupby("homeid")["categoria_ord"].shift(1)
    ordered["consecutive"] = ordered.apply(
        lambda row: (
            False
            if pd.isna(row["previous_period"])
            else (row["period"] - row["previous_period"]).n == 1
        ),
        axis=1,
    )
    transitions = ordered[ordered["consecutive"]].copy()
    transitions["delta"] = (
        transitions["categoria_ord"] - transitions["previous_category"]
    ).abs()
    transitions["changed"] = transitions["delta"] > 0

    months_per_home = ordered.groupby("homeid").size()
    homes_three_plus = months_per_home[months_per_home >= 3].index
    transition_count = (
        transitions.groupby("homeid")["changed"]
        .sum()
        .reindex(homes_three_plus, fill_value=0)
    )
    largest_jump = (
        transitions.groupby("homeid")["delta"]
        .max()
        .reindex(homes_three_plus, fill_value=0)
    )
    if len(homes_three_plus):
        median_transitions = float(transition_count.median())
        proportion_two_plus = float((transition_count >= 2).mean())
        proportion_extreme = float((largest_jump == 2).mean())
    else:
        median_transitions = None
        proportion_two_plus = None
        proportion_extreme = None
    temporal_warning = bool(
        (proportion_two_plus is not None and proportion_two_plus > 0.25)
        or (proportion_extreme is not None and proportion_extreme > 0.10)
    )

    coherence = {
        "peak_energy_share": safe_spearman(
            diagnostic_frame["categoria_ord"], diagnostic_frame["peak_energy_share"]
        ),
        "month_coverage": safe_spearman(
            diagnostic_frame["categoria_ord"], diagnostic_frame["month_coverage"]
        ),
        "cantidad_equipos": safe_spearman(
            diagnostic_frame["categoria_ord"], diagnostic_frame["cantidad_equipos"]
        ),
    }

    adjusted_correlation = safe_spearman(
        diagnostic_frame["categoria_ord"], diagnostic_frame["consumo_kwh"]
    )
    observed_correlation = safe_spearman(
        diagnostic_frame["categoria_ord"], diagnostic_frame["observed_kwh"]
    )
    coverage_difference = (
        adjusted_correlation - observed_correlation
        if adjusted_correlation is not None and observed_correlation is not None
        else None
    )

    train = diagnostic_frame[diagnostic_frame["split"] == "train"]
    equipment_consumption_by_type: dict[str, Any] = {}
    home_level = train.groupby(["homeid", "tipo_inmueble"], as_index=False).agg(
        cantidad_equipos=("cantidad_equipos", "first"),
        consumo_kwh_medio=("consumo_kwh", "mean"),
    )
    for home_type, group in home_level.groupby("tipo_inmueble"):
        equipment_consumption_by_type[home_type] = {
            "n_homes": int(len(group)),
            "pearson": safe_pearson(
                group["cantidad_equipos"], group["consumo_kwh_medio"]
            ),
            "spearman": safe_spearman(
                group["cantidad_equipos"], group["consumo_kwh_medio"]
            ),
        }

    lower = context["thresholds"]["t1"]
    upper = context["thresholds"]["t2"]
    return {
        "balance_by_type_percent": balance_percent.to_dict(orient="index"),
        "balance_by_type_below_10pct": balance_warning,
        "temporal_homes_with_at_least_3_months": int(len(homes_three_plus)),
        "temporal_median_transitions": median_transitions,
        "temporal_proportion_with_2_or_more_transitions": proportion_two_plus,
        "temporal_proportion_with_extreme_jump": proportion_extreme,
        "temporal_stability_low_power": bool(len(homes_three_plus) < 30),
        "temporal_stability_warning": temporal_warning,
        "spearman_category_coherence": coherence,
        "coherence_peak_energy_share_low": bool(
            coherence["peak_energy_share"] is not None
            and coherence["peak_energy_share"] < 0.20
        ),
        "coherence_month_coverage_high": bool(
            coherence["month_coverage"] is not None
            and coherence["month_coverage"] > 0.40
        ),
        "coverage_adjustment_diff": coverage_difference,
        "coverage_adjustment_neutral": bool(
            coverage_difference is not None and abs(coverage_difference) < 0.05
        ),
        "coverage_adjustment_warning": bool(
            coverage_difference is not None and abs(coverage_difference) > 0.15
        ),
        "equipment_vs_consumption_train_home_level": equipment_consumption_by_type,
        "train_unique_scores": int(train["score"].nunique()),
        "train_proportion_near_t1": float(
            (np.abs(train["score"] - lower) < 0.02).mean()
        ),
        "train_proportion_near_t2": float(
            (np.abs(train["score"] - upper) < 0.02).mean()
        ),
    }


# %% [markdown]
# ### Resultado visible de los diagnósticos
#
# Ningún diagnóstico modifica las etiquetas. Estas tablas permiten inspeccionar
# balance, estabilidad temporal, coherencia descriptiva, sensibilidad al ajuste
# de cobertura y relación entre equipos declarados y consumo medio.

# %%

if RUN_PIPELINE:
    diagnostics = calculate_diagnostics(labeled, context)
    notebook_display(
        pd.DataFrame.from_dict(
            diagnostics["balance_by_type_percent"], orient="index"
        ).rename_axis("tipo_inmueble")
    )
    notebook_display(
        pd.DataFrame(
            [
                {
                    "hogares_con_3_meses": diagnostics[
                        "temporal_homes_with_at_least_3_months"
                    ],
                    "mediana_transiciones": diagnostics["temporal_median_transitions"],
                    "proporción_2_o_más": diagnostics[
                        "temporal_proportion_with_2_or_more_transitions"
                    ],
                    "proporción_salto_extremo": diagnostics[
                        "temporal_proportion_with_extreme_jump"
                    ],
                    "warning": diagnostics["temporal_stability_warning"],
                }
            ]
        )
    )
    notebook_display(
        pd.DataFrame(
            [diagnostics["spearman_category_coherence"]],
            index=["Spearman con categoría ordinal"],
        )
    )
    notebook_display(
        pd.DataFrame.from_dict(
            diagnostics["equipment_vs_consumption_train_home_level"],
            orient="index",
        ).rename_axis("tipo_inmueble")
    )
    print(
        "Diferencia por ajuste de cobertura: "
        f"{diagnostics['coverage_adjustment_diff']:.6f}; "
        f"neutral={diagnostics['coverage_adjustment_neutral']}"
    )
    print(f"Scores únicos en train: {diagnostics['train_unique_scores']}")


# %% [markdown]
# ## 9. Escritura de artefactos y resumen final
#
# Las etapas ya se ejecutaron y comprobaron por separado. Esta última celda no
# recalcula el pipeline: solamente serializa los objetos visibles anteriores.
# Escribe:
#
# 1. el dataset mensual elegible;
# 2. el dataset etiquetado;
# 3. la configuración y evidencia completa de reproducibilidad.
#
# `label_metadata.json` conserva las referencias ordenadas de train, IDs de
# ambos splits, umbrales, reglas de limpieza, calidad por hogar, sensibilidad
# de cobertura y diagnósticos. No hace falta recalcular nada con test para
# auditar una etiqueta.

# %%


if RUN_PIPELINE:
    # Resolución segura de la ruta del script: __file__ no existe dentro de
    # un kernel Jupyter; en ese caso se registra None para no bloquear la
    # serialización (los hashes de insumos siguen siendo reproducibles).
    try:
        _self_path = Path(__file__).resolve()
    except NameError:
        _self_path = None
    _script_local_path = (
        _self_path.parent / "de_zip_a_category_local.py" if _self_path else None
    )
    script_local_sha = (
        sha256_of_file(_script_local_path)
        if _script_local_path and _script_local_path.is_file()
        else None
    )
    script_cuaderno_sha = (
        sha256_of_file(_self_path) if _self_path else None
    )

    # Modo muestra: si IDEAL_MAX_HOMES > 0 se escriben los artefactos a un
    # subdirectorio sample_outputs/ con prefijo sample_, para nunca
    # sobrescribir los artefactos canónicos con una muestra didáctica.
    sample_mode = max_homes is not None and max_homes > 0
    if sample_mode:
        out_root = destination / "sample_outputs"
        out_root.mkdir(parents=True, exist_ok=True)
        artifact_prefix = "sample_"
    else:
        out_root = destination
        artifact_prefix = ""

    monthly_path = out_root / f"{artifact_prefix}ideal_monthly_features.csv"
    labeled_path = out_root / f"{artifact_prefix}ideal_monthly_features_labeled.csv"
    labeled_parquet_path = out_root / f"{artifact_prefix}ideal_monthly_features_labeled.parquet"
    audit_path = out_root / f"{artifact_prefix}ideal_monthly_audit.parquet"
    metadata_path = out_root / f"{artifact_prefix}label_metadata.json"

    # Proyección explícita al contrato de 13 columnas; las 8 columnas de
    # auditoría viven únicamente en ideal_monthly_audit.parquet.
    monthly_frame = eligible[MONTHLY_COLUMNS].copy()

    # Hashes SHA-256 de insumos y scripts (reproducibilidad).
    print("Calculando hashes SHA-256 de insumos y scripts...")
    sensors_zip_sha = sha256_of_file(sensors_zip)
    metadata_zip_sha = sha256_of_file(metadata_zip)
    run_id = datetime.now(tz=TZ_UTC).isoformat(timespec="seconds")
    print(f"  run_id: {run_id}")

    metadata = {
        "category_method_version": CATEGORY_METHOD_VERSION,
        "audit_schema_version": AUDIT_SCHEMA_VERSION,
        "run_id": run_id,
        "input_hashes": {
            "household_sensors_zip_sha256": sensors_zip_sha,
            "ideal_metadata_zip_sha256": metadata_zip_sha,
        },
        "script_hashes": {
            "de_zip_a_category_local_py_sha256": script_local_sha,
            "de_zip_a_category_cuaderno_py_sha256": script_cuaderno_sha,
        },
        "audit_sidecar": {
            "path": "data/processed/ideal_monthly_audit.parquet",
            "n_rows": int(len(audit_df)),
            "n_columns": len(AUDIT_COLUMNS),
            "keys_match_canonical": True,
            "disjoint_from_feature_columns": True,
            "night_window_local": "[22:00, 24:00) U [00:00, 06:00)",
            "night_coverage_threshold": CONFIG["night_coverage_threshold"],
        },
        "input_archives": {
            "sensors": sensors_zip.name,
            "metadata": metadata_zip.name,
        },
        "input_dependencies": [
            "household_sensors.zip",
            "ideal_metadata_and_surveys.zip (metadata/home.csv + metadata/appliance.csv)",
        ],
        "sample_flag": bool(context["sample_flag"]),
        "train_size_note": context["train_size_note"],
        "unit_of_analysis": "home-month",
        "manifest_summary": manifest_summary,
        "manifest": manifest,
        "cleaning": {
            "timezone": "Europe/London",
            "defective_interval_utc": {
                "start_inclusive": DEFECTIVE_INTERVAL_START.isoformat(),
                "end_exclusive": DEFECTIVE_INTERVAL_END.isoformat(),
            },
            "discard_negative_watts": True,
            "maximum_plausible_watts": CONFIG["maximum_plausible_watts"],
            "duplicate_policy": "keep_first_adjacent_timestamp",
            "out_of_order_policy": "discard",
        },
        "configuration": CONFIG,
        "weights": WEIGHTS,
        "split": {
            "method": (
                "unique homes sorted by homeid, then train_test_split "
                "stratified by tipo_inmueble"
            ),
            "test_size": CONFIG["test_size"],
            "random_state": CONFIG["random_state"],
            "train_homeids": context["train_homeids"],
            "test_homeids": context["test_homeids"],
            "train_counts_by_type": context["train_counts_by_type"],
        },
        "thresholds": context["thresholds"],
        "references": context["references"],
        "processing_quality_by_home": processing_quality,
        "monthly_quality": {
            "rows_before_eligibility": int(len(all_months)),
            "rows_eligible": int(len(eligible)),
            "homes_eligible": int(eligible["homeid"].nunique()),
            "exclusion_reason_combinations": exclusion_counts.set_index(
                "combinación_de_exclusión"
            )["filas"].to_dict(),
            "coverage_sensitivity": coverage_sensitivity,
        },
        "diagnostics": diagnostics,
        "limitations": [
            "Pseudoetiquetas relativas; IDEAL no aporta ground truth de eficiencia.",
            "Datos de Edimburgo 2016–2018; no generalizables directamente a otras regiones.",
            "La elegibilidad por cobertura reduce el universo a los hogares con meses utilizables.",
            "cantidad_equipos cuenta equipos grandes o fijos declarados, no el inventario total.",
            "La etiqueta se construye con las mismas variables que recibirá el clasificador.",
        ],
    }

    # Serialización al final (post-validación de metadata) para evitar
    # artefactos parciales con apariencia canónica si una celda intermedia
    # falla. En modo muestra, los archivos quedan bajo sample_outputs/.
    monthly_frame.to_csv(monthly_path, index=False)
    labeled_output.to_csv(labeled_path, index=False)
    labeled_output.to_parquet(labeled_parquet_path, index=False)
    audit_df.to_parquet(audit_path, index=False)
    with metadata_path.open("w", encoding="utf-8") as output:
        json.dump(json_ready(metadata), output, ensure_ascii=False, indent=2)

    train = labeled_output[labeled_output["split"] == "train"]
    test = labeled_output[labeled_output["split"] == "test"]
    final_view = pd.DataFrame(
        [
            {
                "split": "train",
                "hogares": train["homeid"].nunique(),
                "filas": len(train),
            },
            {
                "split": "test",
                "hogares": test["homeid"].nunique(),
                "filas": len(test),
            },
            {
                "split": "total",
                "hogares": labeled_output["homeid"].nunique(),
                "filas": len(labeled_output),
            },
        ]
    )
    artifact_view = pd.DataFrame(
        [
            {"artefacto": monthly_path.name, "ruta": str(monthly_path)},
            {"artefacto": labeled_path.name, "ruta": str(labeled_path)},
            {"artefacto": labeled_parquet_path.name, "ruta": str(labeled_parquet_path)},
            {"artefacto": audit_path.name, "ruta": str(audit_path)},
            {"artefacto": metadata_path.name, "ruta": str(metadata_path)},
        ]
    )
    if sample_mode:
        print(
            "Modo muestra activo: los artefactos se escribieron en "
            f"{out_root} con prefijo '{artifact_prefix}'. No se sobrescribió "
            "el dataset canónico."
        )
    notebook_display(final_view)
    notebook_display(artifact_view)
    print(
        "Advertencia: las categorías son relativas y no equivalen a una certificación."
    )
