from pathlib import Path
import json
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

BASE = Path(__file__).resolve().parent
MODEL_PATH = BASE / "models" / "best_model.joblib"
FEATURE_PATH = BASE / "models" / "feature_columns.json"
METRICS_PATH = BASE / "models" / "test_metrics.json"
PROCESSED_DATA_PATH = BASE / "data" / "processed" / "energy_features.csv"
COMPARISON_PATH = BASE / "models" / "model_comparison.csv"

app = FastAPI(
    title="Smart Energy Consumption Prediction API",
    description="Predict next-hour household active power consumption (kW).",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PredictionInput(BaseModel):
    Global_active_power: float = Field(..., ge=0, description="Current active power in kW")
    Global_reactive_power: float = Field(..., ge=0)
    Voltage: float = Field(..., gt=0)
    Global_intensity: float = Field(..., ge=0)
    Sub_metering_1: float = Field(..., ge=0)
    Sub_metering_2: float = Field(..., ge=0)
    Sub_metering_3: float = Field(..., ge=0)
    power_lag_1: float = Field(..., ge=0)
    power_lag_2: float = Field(..., ge=0)
    power_lag_3: float = Field(..., ge=0)
    power_rolling_mean_3: float = Field(..., ge=0)
    hour: int = Field(..., ge=0, le=23)
    day_of_week: int = Field(..., ge=0, le=6)

def load_artifacts():
    if not MODEL_PATH.exists() or not FEATURE_PATH.exists():
        return None, None
    model = joblib.load(MODEL_PATH)
    features = json.loads(FEATURE_PATH.read_text())
    return model, features

@app.get("/")
def home():
    return {"message": "Smart Energy Prediction API is running"}

@app.get("/health")
def health():
    model, _ = load_artifacts()
    return {"status": "healthy", "model_ready": model is not None}

@app.get("/metrics")
def metrics():
    if not METRICS_PATH.exists():
        raise HTTPException(status_code=404, detail="Train the model first.")
    return json.loads(METRICS_PATH.read_text())

@app.post("/predict")
def predict(payload: PredictionInput):
    model, features = load_artifacts()
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model not trained yet. Run python training/train_models.py from backend.",
        )
    row = pd.DataFrame([payload.model_dump()])[features]
    prediction = float(model.predict(row)[0])
    return {
        "predicted_next_hour_active_power_kw": round(max(0.0, prediction), 4),
        "unit": "kW",
        "model": "best validation model",
    }

@app.get("/analytics")
def analytics():
    if not PROCESSED_DATA_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Processed dataset not found. Run preprocessing/prepare_data.py first."
        )

    df = pd.read_csv(PROCESSED_DATA_PATH)
    df["Date_Time"] = pd.to_datetime(df["Date_Time"], errors="coerce")
    df = df.dropna(subset=["Date_Time"]).sort_values("Date_Time")

    # Recent hourly readings
    hourly = df.tail(48)
    hourly_data = [
        {
            "time": row["Date_Time"].strftime("%d %b %H:%M"),
            "active_power": round(float(row["Global_active_power"]), 3)
        }
        for _, row in hourly.iterrows()
    ]

    # Average active power by day
    daily = (
        df.set_index("Date_Time")["Global_active_power"]
        .resample("D")
        .mean()
        .dropna()
        .tail(14)
    )
    daily_data = [
        {"date": date.strftime("%d %b"), "average_power": round(float(value), 3)}
        for date, value in daily.items()
    ]

    # Total sub-metering readings (Wh)
    appliance_data = [
        {
            "name": "Kitchen",
            "value": round(float(df["Sub_metering_1"].sum()), 2)
        },
        {
            "name": "Laundry",
            "value": round(float(df["Sub_metering_2"].sum()), 2)
        },
        {
            "name": "Other appliances",
            "value": round(float(df["Sub_metering_3"].sum()), 2)
        }
    ]

    # Model validation comparison
    model_data = []
    if COMPARISON_PATH.exists():
        comparison = pd.read_csv(COMPARISON_PATH)
        model_data = [
            {
                "model": str(row["Model"]),
                "rmse": round(float(row["Validation_RMSE"]), 4),
                "mae": round(float(row["Validation_MAE"]), 4),
                "r2": round(float(row["Validation_R2"]), 4)
            }
            for _, row in comparison.iterrows()
        ]

    return {
        "total_records": int(len(df)),
        "date_from": df["Date_Time"].min().strftime("%Y-%m-%d"),
        "date_to": df["Date_Time"].max().strftime("%Y-%m-%d"),
        "average_active_power": round(float(df["Global_active_power"].mean()), 3),
        "maximum_active_power": round(float(df["Global_active_power"].max()), 3),
        "hourly": hourly_data,
        "daily": daily_data,
        "appliances": appliance_data,
        "models": model_data
    }

