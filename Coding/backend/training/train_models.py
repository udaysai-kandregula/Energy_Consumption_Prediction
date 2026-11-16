from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd

from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import (
    RandomForestRegressor,
    ExtraTreesRegressor,
    HistGradientBoostingRegressor,
)
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

DATA = Path("data/processed/energy_features.csv")
MODEL_DIR = Path("models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

if not DATA.exists():
    raise FileNotFoundError("Run: python preprocessing/prepare_data.py")

df = pd.read_csv(DATA)
target = "target_next_hour"
excluded = ["Date_Time", "segment_id", target]
features = [c for c in df.columns if c not in excluded]
X, y = df[features], df[target]

n = len(df)
train_end, val_end = int(n * .70), int(n * .85)
if val_end >= n or train_end == 0:
    raise ValueError("Dataset is too small for chronological train/validation/test splits.")

X_train, y_train = X.iloc[:train_end], y.iloc[:train_end]
X_val, y_val = X.iloc[train_end:val_end], y.iloc[train_end:val_end]
X_test, y_test = X.iloc[val_end:], y.iloc[val_end:]

models = {
    "Linear Regression": LinearRegression(),
    "Decision Tree": DecisionTreeRegressor(max_depth=10, random_state=42),
    "Random Forest": RandomForestRegressor(
        n_estimators=120, max_depth=15, random_state=42, n_jobs=-1
    ),
    "Extra Trees": ExtraTreesRegressor(
        n_estimators=120, max_depth=15, random_state=42, n_jobs=-1
    ),
    "Hist Gradient Boosting": HistGradientBoostingRegressor(
        max_iter=120, max_leaf_nodes=15, random_state=42
    ),
}

rows = []
trained = {}
print(f"Rows: train={len(X_train)}, validation={len(X_val)}, test={len(X_test)}")
print("Features:", features)

for name, model in models.items():
    print(f"\nTraining {name}...")
    model.fit(X_train, y_train)
    pred = model.predict(X_val)
    rmse = float(np.sqrt(mean_squared_error(y_val, pred)))
    rows.append({
        "Model": name,
        "Validation_MAE": float(mean_absolute_error(y_val, pred)),
        "Validation_RMSE": rmse,
        "Validation_R2": float(r2_score(y_val, pred)),
    })
    trained[name] = model

comparison = pd.DataFrame(rows).sort_values("Validation_RMSE")
comparison.to_csv(MODEL_DIR / "model_comparison.csv", index=False)
best_name = comparison.iloc[0]["Model"]
best_model = trained[best_name]

# Final evaluation only once on the held-out chronological test portion.
test_pred = best_model.predict(X_test)
test_metrics = {
    "selected_model": best_name,
    "test_mae": float(mean_absolute_error(y_test, test_pred)),
    "test_rmse": float(np.sqrt(mean_squared_error(y_test, test_pred))),
    "test_r2": float(r2_score(y_test, test_pred)),
    "test_rows": int(len(X_test)),
}
joblib.dump(best_model, MODEL_DIR / "best_model.joblib")
(MODEL_DIR / "feature_columns.json").write_text(json.dumps(features, indent=2))
(MODEL_DIR / "test_metrics.json").write_text(json.dumps(test_metrics, indent=2))

print("\nVALIDATION COMPARISON (lower RMSE is better)")
print(comparison.to_string(index=False))
print("\nHELD-OUT TEST METRICS")
print(json.dumps(test_metrics, indent=2))
print("\nSaved best_model.joblib and evaluation files in models/")
