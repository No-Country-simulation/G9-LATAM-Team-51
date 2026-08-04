"""Entrena, serializa y valida los artefactos de inferencia de EnergiAI.

Este script reproduce el modelo ganador documentado en el PR #4:
Regresión Logística con C=10.0, entrenada únicamente con el split ``train``.

Genera:

* ``models/energy_efficiency_pipeline_v1.joblib`` para reproducibilidad Python.
* ``models/energy_efficiency_classifier_v1.onnx`` para inferencia desde Java.
* ``models/model_contract_v1.json`` con el contrato exacto de entradas/salidas.
* ``models/SHA256SUMS.txt`` para verificar integridad.
* ``reports/onnx_parity_report.json`` con la prueba Python vs. ONNX.
* ``reports/onnx_prediction_examples.json`` con casos para Back-End.

El dataset canónico no contiene nulos en las cinco variables obligatorias y la
API debe rechazarlos. El artefacto joblib conserva los imputadores originales.
El grafo ONNX omite esos pasos sin efecto para evitar operadores Imputer no
portables; la paridad se comprueba sobre las 555 filas válidas del contrato.
"""

from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import onnx
import onnxruntime as ort
import pandas as pd
import scipy
import sklearn
import skl2onnx
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from skl2onnx import to_onnx
from skl2onnx.common.data_types import (
    DoubleTensorType,
    Int64TensorType,
    StringTensorType,
)

RANDOM_STATE = 42
MODEL_VERSION = "1.0.0"
TARGET_OPSET = 17
PARITY_TOLERANCE = 1e-10

FEATURE_COLUMNS = [
    "consumo_kwh",
    "uso_horario_pico",
    "cantidad_equipos",
    "tipo_inmueble",
    "horas_alto_consumo",
]
NUMERIC_FEATURES = ["consumo_kwh", "cantidad_equipos", "horas_alto_consumo"]
CATEGORICAL_FEATURES = ["tipo_inmueble", "uso_horario_pico"]
TARGET_COLUMN = "categoria"
SPLIT_COLUMN = "split"
GROUP_COLUMN = "homeid"

EXPECTED_TEST_METRICS = {
    "accuracy": 0.9435483870967742,
    "f1_macro": 0.9441585632874531,
}


def find_repo_root() -> Path:
    """Encuentra la raíz del repositorio desde terminal, VS Code o Jupyter."""
    for candidate in [Path.cwd(), *Path.cwd().parents]:
        expected = (
            candidate
            / "data"
            / "processed"
            / "ideal_monthly_features_labeled.parquet"
        )
        if expected.exists():
            return candidate
    raise FileNotFoundError(
        "No se encontró data/processed/ideal_monthly_features_labeled.parquet. "
        "Ejecute este script desde el repositorio G9-LATAM-Team-51."
    )


def build_python_pipeline() -> Pipeline:
    """Crea el pipeline ganador completo para persistencia con joblib."""
    numeric_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preprocessor = ColumnTransformer(
        [
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )
    return Pipeline(
        [
            ("preprocessor", preprocessor),
            (
                "model",
                LogisticRegression(
                    C=10.0,
                    class_weight=None,
                    max_iter=3000,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def build_onnx_pipeline() -> Pipeline:
    """Crea el pipeline ONNX equivalente para entradas válidas del contrato.

    ``uso_horario_pico`` se representa como INT64 (false=0, true=1) porque el
    conversor de OneHotEncoder no admite tensores booleanos. Los imputadores se
    omiten: la API y el dataset canónico exigen las cinco entradas no nulas.
    """
    numeric_pipeline = Pipeline([("scaler", StandardScaler())])
    categorical_pipeline = Pipeline(
        [("onehot", OneHotEncoder(handle_unknown="ignore"))]
    )
    preprocessor = ColumnTransformer(
        [
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )
    return Pipeline(
        [
            ("preprocessor", preprocessor),
            (
                "model",
                LogisticRegression(
                    C=10.0,
                    class_weight=None,
                    max_iter=3000,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def validate_dataset(df: pd.DataFrame) -> None:
    """Valida las precondiciones metodológicas y el contrato del endpoint."""
    required = {
        GROUP_COLUMN,
        "year_month",
        SPLIT_COLUMN,
        TARGET_COLUMN,
        *FEATURE_COLUMNS,
    }
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError(f"Faltan columnas obligatorias: {missing}")
    if len(df) != 555 or df[GROUP_COLUMN].nunique() != 151:
        raise ValueError("El dataset no coincide con la versión canónica 555×151.")
    if df[list(required)].isna().any().any():
        raise ValueError("Hay nulos en columnas obligatorias.")
    if df.duplicated([GROUP_COLUMN, "year_month"]).any():
        raise ValueError("Hay duplicados hogar-mes.")
    if set(df[SPLIT_COLUMN]) != {"train", "test"}:
        raise ValueError("El split debe contener únicamente train y test.")
    if set(df[TARGET_COLUMN]) != {"Eficiente", "Moderado", "Ineficiente"}:
        raise ValueError("Se encontraron categorías no reconocidas.")

    train_homes = set(df.loc[df[SPLIT_COLUMN].eq("train"), GROUP_COLUMN])
    test_homes = set(df.loc[df[SPLIT_COLUMN].eq("test"), GROUP_COLUMN])
    if train_homes.intersection(test_homes):
        raise ValueError("Leakage: existen viviendas compartidas entre train y test.")


def as_onnx_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Adapta el booleano de la API al tipo tensor admitido por ONNX."""
    result = df[FEATURE_COLUMNS].copy()
    result["uso_horario_pico"] = result["uso_horario_pico"].astype(np.int64)
    return result


def make_onnx_feed(df: pd.DataFrame) -> dict[str, np.ndarray]:
    """Convierte un DataFrame al mapa de cinco tensores esperado por ORT."""
    adapted = as_onnx_frame(df)
    return {column: adapted[[column]].to_numpy() for column in FEATURE_COLUMNS}


def sha256(path: Path) -> str:
    """Calcula SHA-256 por bloques."""
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def json_ready(value: Any) -> Any:
    """Convierte escalares NumPy/Pandas a tipos serializables por JSON."""
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def main() -> None:
    repo_root = find_repo_root()
    data_path = (
        repo_root / "data" / "processed" / "ideal_monthly_features_labeled.parquet"
    )
    models_dir = repo_root / "models"
    reports_dir = repo_root / "reports"
    models_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    joblib_path = models_dir / "energy_efficiency_pipeline_v1.joblib"
    onnx_path = models_dir / "energy_efficiency_classifier_v1.onnx"
    contract_path = models_dir / "model_contract_v1.json"
    checksums_path = models_dir / "SHA256SUMS.txt"
    parity_path = reports_dir / "onnx_parity_report.json"
    examples_path = reports_dir / "onnx_prediction_examples.json"

    df = pd.read_parquet(data_path)
    validate_dataset(df)
    train_df = df[df[SPLIT_COLUMN].eq("train")].copy()
    test_df = df[df[SPLIT_COLUMN].eq("test")].copy()

    python_model = build_python_pipeline()
    python_model.fit(train_df[FEATURE_COLUMNS], train_df[TARGET_COLUMN])

    onnx_train = as_onnx_frame(train_df)
    onnx_model_source = build_onnx_pipeline()
    onnx_model_source.fit(onnx_train, train_df[TARGET_COLUMN])

    python_labels_all = python_model.predict(df[FEATURE_COLUMNS])
    python_probabilities_all = python_model.predict_proba(df[FEATURE_COLUMNS])
    source_labels_all = onnx_model_source.predict(as_onnx_frame(df))
    source_probabilities_all = onnx_model_source.predict_proba(as_onnx_frame(df))

    if not np.array_equal(python_labels_all, source_labels_all):
        raise AssertionError("El pipeline exportable no replica las etiquetas de Python.")
    source_difference = float(
        np.max(np.abs(python_probabilities_all - source_probabilities_all))
    )
    if source_difference > PARITY_TOLERANCE:
        raise AssertionError(
            "El pipeline exportable no replica las probabilidades de Python: "
            f"{source_difference}"
        )

    joblib.dump(python_model, joblib_path, compress=3)

    initial_types = [
        ("consumo_kwh", DoubleTensorType([None, 1])),
        ("uso_horario_pico", Int64TensorType([None, 1])),
        ("cantidad_equipos", Int64TensorType([None, 1])),
        ("tipo_inmueble", StringTensorType([None, 1])),
        ("horas_alto_consumo", Int64TensorType([None, 1])),
    ]
    converted = to_onnx(
        onnx_model_source,
        initial_types=initial_types,
        target_opset=TARGET_OPSET,
        options={"model__zipmap": False},
    )
    metadata = {
        "model_name": "EnergiAI Energy Efficiency Classifier",
        "model_version": MODEL_VERSION,
        "label_methodology": "ideal-relative-v1",
        "training_dataset": "ideal_monthly_features_labeled.parquet",
        "probability_class_order": json.dumps(
            python_model.classes_.tolist(), ensure_ascii=False
        ),
        "owner": "Tomás Maldonado (Data)",
    }
    for key, value in metadata.items():
        item = converted.metadata_props.add()
        item.key = key
        item.value = value

    onnx.checker.check_model(converted)
    onnx_path.write_bytes(converted.SerializeToString())

    session = ort.InferenceSession(
        str(onnx_path),
        providers=["CPUExecutionProvider"],
    )
    onnx_labels_all, onnx_probabilities_all = session.run(
        None,
        make_onnx_feed(df),
    )
    labels_match = bool(np.array_equal(python_labels_all, onnx_labels_all))
    max_probability_difference = float(
        np.max(np.abs(python_probabilities_all - onnx_probabilities_all))
    )
    if not labels_match or max_probability_difference > PARITY_TOLERANCE:
        raise AssertionError(
            "Falló la paridad Python↔ONNX: "
            f"labels_match={labels_match}, "
            f"max_probability_difference={max_probability_difference}"
        )

    test_mask = df[SPLIT_COLUMN].eq("test").to_numpy()
    onnx_test_labels = onnx_labels_all[test_mask]
    test_accuracy = float(accuracy_score(test_df[TARGET_COLUMN], onnx_test_labels))
    test_f1_macro = float(
        f1_score(test_df[TARGET_COLUMN], onnx_test_labels, average="macro")
    )
    if not np.isclose(test_accuracy, EXPECTED_TEST_METRICS["accuracy"]):
        raise AssertionError(f"Accuracy inesperada: {test_accuracy}")
    if not np.isclose(test_f1_macro, EXPECTED_TEST_METRICS["f1_macro"]):
        raise AssertionError(f"F1 macro inesperado: {test_f1_macro}")

    onnx_hash = sha256(onnx_path)
    joblib_hash = sha256(joblib_path)
    class_order = python_model.classes_.tolist()

    contract = {
        "model_name": "EnergiAI Energy Efficiency Classifier",
        "model_version": MODEL_VERSION,
        "label_methodology": "ideal-relative-v1",
        "onnx_opset": TARGET_OPSET,
        "artifacts": {
            "java_inference": {
                "path": "models/energy_efficiency_classifier_v1.onnx",
                "sha256": onnx_hash,
            },
            "python_reproducibility": {
                "path": "models/energy_efficiency_pipeline_v1.joblib",
                "sha256": joblib_hash,
                "trusted_source_only": True,
            },
        },
        "inputs": [
            {
                "name": "consumo_kwh",
                "onnx_type": "DOUBLE",
                "shape": ["batch", 1],
                "api_field": "consumoKwh",
                "validation": "required; > 0",
            },
            {
                "name": "uso_horario_pico",
                "onnx_type": "INT64",
                "shape": ["batch", 1],
                "api_field": "usoHorarioPico",
                "mapping": {"false": 0, "true": 1},
                "validation": "required",
            },
            {
                "name": "cantidad_equipos",
                "onnx_type": "INT64",
                "shape": ["batch", 1],
                "api_field": "cantidadEquipos",
                "validation": "required; >= 1",
            },
            {
                "name": "tipo_inmueble",
                "onnx_type": "STRING",
                "shape": ["batch", 1],
                "api_field": "tipoInmueble",
                "allowed_values": ["Casa", "Departamento"],
                "validation": "required; case-sensitive",
            },
            {
                "name": "horas_alto_consumo",
                "onnx_type": "INT64",
                "shape": ["batch", 1],
                "api_field": "horasAltoConsumo",
                "validation": "required; integer between 0 and 24",
            },
        ],
        "outputs": [
            {
                "name": "label",
                "onnx_type": "STRING",
                "shape": ["batch"],
                "meaning": "Categoría predicha",
            },
            {
                "name": "probabilities",
                "onnx_type": "DOUBLE",
                "shape": ["batch", 3],
                "class_order": class_order,
            },
        ],
        "class_order_warning": (
            "El orden tensorial es lexicográfico y no coincide con el orden "
            "visual de los reportes. Back-End debe usar exactamente outputs[1].class_order."
        ),
        "training": {
            "algorithm": "LogisticRegression",
            "parameters": {
                "C": 10.0,
                "class_weight": None,
                "max_iter": 3000,
                "random_state": RANDOM_STATE,
            },
            "train_rows": 431,
            "train_homes": 113,
            "test_rows": 124,
            "test_homes": 38,
            "test_accuracy": test_accuracy,
            "test_f1_macro": test_f1_macro,
        },
        "runtime": {
            "python_onnxruntime": ort.__version__,
            "recommended_java_dependency": (
                "com.microsoft.onnxruntime:onnxruntime:1.27.0"
            ),
        },
        "limitations": [
            "Las cinco entradas son obligatorias y no pueden ser nulas.",
            "Las categorías son pseudoetiquetas relativas, no certificaciones.",
            "La generalización a LATAM requiere validación externa.",
        ],
    }
    contract_path.write_text(
        json.dumps(contract, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    checksums_path.write_text(
        f"{onnx_hash}  energy_efficiency_classifier_v1.onnx\n"
        f"{joblib_hash}  energy_efficiency_pipeline_v1.joblib\n",
        encoding="utf-8",
    )

    parity_report = {
        "status": "PASS",
        "rows_compared": int(len(df)),
        "test_rows_compared": int(len(test_df)),
        "label_matches": int(np.sum(python_labels_all == onnx_labels_all)),
        "label_match_rate": float(np.mean(python_labels_all == onnx_labels_all)),
        "max_absolute_probability_difference": max_probability_difference,
        "tolerance": PARITY_TOLERANCE,
        "python_to_export_source_max_probability_difference": source_difference,
        "test_accuracy_onnx": test_accuracy,
        "test_f1_macro_onnx": test_f1_macro,
        "probability_class_order": class_order,
        "onnx_inputs": [
            {"name": item.name, "type": item.type, "shape": item.shape}
            for item in session.get_inputs()
        ],
        "onnx_outputs": [
            {"name": item.name, "type": item.type, "shape": item.shape}
            for item in session.get_outputs()
        ],
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "scikit_learn": sklearn.__version__,
            "skl2onnx": skl2onnx.__version__,
            "onnx": onnx.__version__,
            "onnxruntime": ort.__version__,
            "joblib": joblib.__version__,
        },
    }
    parity_path.write_text(
        json.dumps(parity_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    example_rows = (
        test_df.groupby(TARGET_COLUMN, observed=True, group_keys=False)
        .head(1)
        .copy()
    )
    example_indices = example_rows.index.to_numpy()
    examples: list[dict[str, Any]] = []
    for row_index in example_indices:
        position = int(np.flatnonzero(df.index.to_numpy() == row_index)[0])
        row = df.loc[row_index]
        probability_vector = onnx_probabilities_all[position]
        predicted_label = str(onnx_labels_all[position])
        predicted_index = class_order.index(predicted_label)
        examples.append(
            {
                "input_api": {
                    "consumoKwh": float(row["consumo_kwh"]),
                    "usoHorarioPico": bool(row["uso_horario_pico"]),
                    "cantidadEquipos": int(row["cantidad_equipos"]),
                    "tipoInmueble": str(row["tipo_inmueble"]),
                    "horasAltoConsumo": int(row["horas_alto_consumo"]),
                },
                "expected_output": {
                    "categoria": predicted_label,
                    "probabilidad": float(probability_vector[predicted_index]),
                    "probabilities_by_class": {
                        label: float(probability_vector[index])
                        for index, label in enumerate(class_order)
                    },
                },
                "reference_category": str(row[TARGET_COLUMN]),
            }
        )
    examples_path.write_text(
        json.dumps(examples, ensure_ascii=False, indent=2, default=json_ready) + "\n",
        encoding="utf-8",
    )

    print("Exportación y validación completadas.")
    print(f"ONNX: {onnx_path.relative_to(repo_root)}")
    print(f"joblib: {joblib_path.relative_to(repo_root)}")
    print(f"Contrato: {contract_path.relative_to(repo_root)}")
    print(
        "Paridad: "
        f"{int(np.sum(python_labels_all == onnx_labels_all))}/{len(df)} etiquetas, "
        f"diferencia máxima={max_probability_difference:.3e}"
    )


if __name__ == "__main__":
    main()
