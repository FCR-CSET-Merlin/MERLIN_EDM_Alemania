"""Train and evaluate the Berlin MLP on the multiyear contracts."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
TARGET = "target_scaled"
DEFAULT_DATA_ROOT = REPO / "prototipo_3/data/de_alemania/berlin_training_multiyear"
DEFAULT_REPORT_ROOT = REPO / "corfo-report/validation/berlin/multiyear_2020_2024"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_model(input_dim: int):
    import tensorflow as tf
    from tensorflow.keras import Sequential
    from tensorflow.keras.layers import Dense, Input
    from tensorflow.keras.losses import Huber

    model = Sequential([
        Input(shape=(input_dim,)),
        Dense(256, activation="elu"),
        Dense(128, activation="elu"),
        Dense(64, activation="elu"),
        Dense(32, activation="elu"),
        Dense(1, activation="linear"),
    ])
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.0005),
        loss=Huber(delta=1.0),
        metrics=["mae"],
    )
    return model


def metrics(y_true_scaled: np.ndarray, y_pred_scaled: np.ndarray, mu: float, sigma: float) -> dict[str, float]:
    actual = y_true_scaled * sigma + mu
    predicted = y_pred_scaled * sigma + mu
    errors = predicted - actual
    return {
        "mape_pct": float(np.mean(np.abs(errors) / np.maximum(np.abs(actual), 1e-9)) * 100.0),
        "mae_MW": float(np.mean(np.abs(errors))),
        "rmse_MW": float(np.sqrt(np.mean(errors ** 2))),
        "bias_MW": float(np.mean(errors)),
        "actual_mean_MW": float(np.mean(actual)),
        "predicted_mean_MW": float(np.mean(predicted)),
        "n": int(len(actual)),
    }


def load_contract(data_root: Path, dimension: int):
    import pandas as pd

    manifest_path = data_root / f"berlin_training_contract_multiyear_d{dimension}_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    features = manifest["features"]
    frames = {}
    for split in ("train", "validation", "test"):
        path = data_root / f"berlin_multiyear_d{dimension}_{split}.parquet"
        frame = pd.read_parquet(path, engine="pyarrow")
        expected = [*features, TARGET]
        if list(frame.columns) != expected:
            raise ValueError(f"Unexpected columns in {path}")
        if frame.isna().any().any() or not np.isfinite(frame.to_numpy(dtype=float)).all():
            raise ValueError(f"Non-finite data in {path}")
        frames[split] = frame
    return manifest, features, frames, manifest_path


def train_one(dimension: int, data_root: Path, report_root: Path, epochs: int, batch_size: int, patience: int) -> dict[str, object]:
    import tensorflow as tf

    manifest, features, frames, manifest_path = load_contract(data_root, dimension)
    mu = float(manifest["scaling"]["mu_train_MW"])
    sigma = float(manifest["scaling"]["sigma_train_MW"])
    os.environ.setdefault("CUDA_VISIBLE_DEVICES", "-1")
    os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    tf.keras.utils.set_random_seed(2023)
    try:
        tf.config.experimental.enable_op_determinism()
    except Exception:
        pass

    x_train = frames["train"][features].to_numpy(dtype=np.float32)
    y_train = frames["train"][TARGET].to_numpy(dtype=np.float32)
    x_val = frames["validation"][features].to_numpy(dtype=np.float32)
    y_val = frames["validation"][TARGET].to_numpy(dtype=np.float32)
    model = build_model(len(features))
    model_root = data_root / f"model_multiyear_d{dimension}"
    model_root.mkdir(parents=True, exist_ok=True)
    checkpoint = model_root / f"best_merlin_mlp_berlin_multiyear_d{dimension}.keras"
    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=patience, restore_best_weights=True),
        tf.keras.callbacks.ModelCheckpoint(checkpoint, monitor="val_loss", save_best_only=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=max(2, patience // 2), min_lr=1e-5),
    ]
    history = model.fit(
        x_train,
        y_train,
        validation_data=(x_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        shuffle=True,
        callbacks=callbacks,
        verbose=1,
    )
    prediction = {
        split: model.predict(frames[split][features].to_numpy(dtype=np.float32), batch_size=2048, verbose=0).ravel()
        for split in ("train", "validation", "test")
    }
    split_metrics = {
        split: metrics(frames[split][TARGET].to_numpy(dtype=float), prediction[split].astype(float), mu, sigma)
        for split in ("train", "validation", "test")
    }
    result: dict[str, object] = {
        "dataset": "berlin_mlp_training_multiyear_2020_2024",
        "dimension": dimension,
        "features": features,
        "contract_manifest": str(manifest_path.relative_to(REPO)),
        "contract_manifest_sha256": sha256(manifest_path),
        "seed": 2023,
        "architecture": "Dense 256-128-64-32 ELU + linear output; Huber; Adam lr=0.0005",
        "split_policy": "train 2020-2022; validation 2023; frozen holdout 2024",
        "batch_shuffle": "true only inside training partition; no row redistribution across partitions",
        "weights": str(checkpoint.relative_to(REPO)),
        "metrics": split_metrics,
        "history": {key: [float(value) for value in values] for key, values in history.history.items()},
    }
    output = model_root / f"berlin_mlp_multiyear_d{dimension}_results.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT)
    parser.add_argument("--dimensions", default="3,5,8")
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--patience", type=int, default=12)
    args = parser.parse_args()
    dimensions = tuple(int(item.strip()) for item in args.dimensions.split(",") if item.strip())
    report_root = args.report_root.resolve()
    results = [
        train_one(dimension, args.data_root.resolve(), report_root, args.epochs, args.batch_size, args.patience)
        for dimension in dimensions
    ]
    report_root.mkdir(parents=True, exist_ok=True)
    rows = []
    for result in results:
        for split, values in result["metrics"].items():
            rows.append({
                "dimension": result["dimension"],
                "split": split,
                "years": {"train": "2020-2022", "validation": "2023", "test": "2024"}[split],
                **values,
            })
    csv_path = report_root / "berlin_multiyear_model_metrics.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    md_path = report_root / "berlin_multiyear_model_metrics.md"
    lines = [
        "# Métricas MLP Berlín multianual 2020-2024",
        "",
        "La arquitectura se mantuvo igual al piloto alemán. Se ajustaron los modelos usando 2020-2022, se monitorizó la validación 2023 y se evaluó 2024 una sola vez como holdout temporal congelado. El MAPE no es una validación independiente de fuente: la carga observada sigue siendo HV de Stromnetz Berlin.",
        "",
        "| d | Partición | Años | n | MAPE (%) | MAE (MW) | RMSE (MW) | Sesgo (MW) |",
        "|---:|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['dimension']} | {row['split']} | {row['years']} | {row['n']} | {row['mape_pct']:.6f} | {row['mae_MW']:.6f} | {row['rmse_MW']:.6f} | {row['bias_MW']:.6f} |"
        )
    lines.extend([
        "",
        "La selección de d debe hacerse con la validación 2023; el resultado de 2024 debe permanecer reservado para reportar generalización temporal.",
    ])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"metrics": rows, "report": str(md_path)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
