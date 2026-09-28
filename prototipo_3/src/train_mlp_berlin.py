"""Train and evaluate a Berlin MLP from the German contract Parquets.

The script deliberately builds new weights for Germany. It supports d=3, d=5
and d=8 contracts and offers --dry-run so the contract can be checked before
TensorFlow is installed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
TARGET = "target_scaled"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_contract(root: Path, dimension: int):
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError("The German trainer requires pandas and pyarrow") from exc
    manifest_path = root / f"berlin_training_contract_d{dimension}_2023_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("dimension") != dimension:
        raise ValueError(f"Contract dimension {manifest.get('dimension')} != requested d={dimension}")
    features = manifest["features"]
    if len(features) != 16 + dimension:
        raise ValueError(f"Expected {16 + dimension} features, got {len(features)}")
    frames = {}
    for split in ("train", "validation", "test"):
        path = root / f"berlin_2023_d{dimension}_{split}.parquet"
        if not path.is_file():
            raise FileNotFoundError(path)
        frame = pd.read_parquet(path, engine="pyarrow")
        expected = [*features, TARGET]
        if list(frame.columns) != expected:
            raise ValueError(f"Unexpected columns in {path}: {list(frame.columns)}")
        if frame.isna().any().any():
            raise ValueError(f"NaN values in {path}")
        if not np.isfinite(frame.to_numpy(dtype=float)).all():
            raise ValueError(f"Non-finite values in {path}")
        frames[split] = frame
    return manifest, features, frames


def metrics(y_true_scaled: np.ndarray, y_pred_scaled: np.ndarray, mu: float, sigma: float) -> dict[str, float]:
    actual = y_true_scaled * sigma + mu
    predicted = y_pred_scaled * sigma + mu
    errors = predicted - actual
    return {
        "mape_pct": float(np.mean(np.abs(errors) / np.maximum(np.abs(actual), 1e-9)) * 100),
        "mae_MW": float(np.mean(np.abs(errors))),
        "rmse_MW": float(np.sqrt(np.mean(errors ** 2))),
        "bias_MW": float(np.mean(errors)),
        "actual_mean_MW": float(np.mean(actual)),
        "predicted_mean_MW": float(np.mean(predicted)),
        "n": int(len(actual)),
    }


def build_mlp_model(input_dim: int):
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=REPO / "prototipo_3/data/de_alemania/berlin_training_2023")
    parser.add_argument("--dimension", type=int, choices=(3, 5, 8), default=8)
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--patience", type=int, default=10)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    data_root = args.data_root.resolve()
    manifest, features, frames = load_contract(data_root, args.dimension)
    mu = float(manifest["scaling"]["mu_train_MW"])
    sigma = float(manifest["scaling"]["sigma_train_MW"])
    print(f"Contract d={args.dimension}: {len(features)} inputs; train={len(frames['train'])}, validation={len(frames['validation'])}, test={len(frames['test'])}")
    print(f"Target scale: mu_train={mu:.9f} MW; sigma_train={sigma:.9f} MW")
    if args.dry_run:
        return

    os.environ.setdefault("CUDA_VISIBLE_DEVICES", "-1")
    os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    import tensorflow as tf
    tf.keras.utils.set_random_seed(2023)
    try:
        tf.config.experimental.enable_op_determinism()
    except Exception:
        pass

    x_train = frames["train"][features].to_numpy(dtype=np.float32)
    y_train = frames["train"][TARGET].to_numpy(dtype=np.float32)
    x_val = frames["validation"][features].to_numpy(dtype=np.float32)
    y_val = frames["validation"][TARGET].to_numpy(dtype=np.float32)
    x_test = frames["test"][features].to_numpy(dtype=np.float32)
    y_test = frames["test"][TARGET].to_numpy(dtype=np.float32)

    model = build_mlp_model(len(features))
    output_root = (args.output_root or data_root / f"model_d{args.dimension}").resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    checkpoint = output_root / f"best_merlin_mlp_berlin_d{args.dimension}.keras"
    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=args.patience, restore_best_weights=True),
        tf.keras.callbacks.ModelCheckpoint(checkpoint, monitor="val_loss", save_best_only=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=max(2, args.patience // 2), min_lr=1e-5),
    ]
    history = model.fit(
        x_train, y_train,
        validation_data=(x_val, y_val),
        epochs=args.epochs,
        batch_size=args.batch_size,
        callbacks=callbacks,
        verbose=1,
    )
    predictions = {
        split: model.predict(frames[split][features].to_numpy(dtype=np.float32), batch_size=2048, verbose=0).ravel()
        for split in ("train", "validation", "test")
    }
    result = {
        "dataset": "berlin_mlp_training_2023",
        "dimension": args.dimension,
        "features": features,
        "contract_manifest_sha256": sha256(data_root / f"berlin_training_contract_d{args.dimension}_2023_manifest.json"),
        "seed": 2023,
        "weights": str(checkpoint.relative_to(REPO)),
        "metrics": {
            split: metrics(frames[split][TARGET].to_numpy(dtype=float), pred.astype(float), mu, sigma)
            for split, pred in predictions.items()
        },
        "history": {key: [float(value) for value in values] for key, values in history.history.items()},
    }
    (output_root / f"berlin_mlp_d{args.dimension}_results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["metrics"], indent=2))


if __name__ == "__main__":
    main()
