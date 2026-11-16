# Smart Energy Consumption Prediction

A fresh starter project for an MCA project using household electricity data, five regression models, FastAPI, React, and optional SHAP/LIME explanations.

## Architecture
- `backend/`: data inspection, cleaning, feature engineering, model training, FastAPI API
- `frontend/`: React + Vite dashboard
- Dataset is used for training only. Do not put the CSV inside the frontend or deploy it to Vercel.

## 1. Recommended setup (Windows + Git Bash)

Use **Python 3.12** (recommended) rather than Python 3.15 for smoother ML-library compatibility.
Install Python 3.12 from https://www.python.org/downloads/ and select "Add Python to PATH".

Check:
```bash
py -3.12 --version
node --version
npm --version
```

## 2. Create backend environment

From the project root:
```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 3. Add the dataset

Put your selected CSV file in:
`backend/data/raw/household_power_timeseries.csv`

Expected columns:
- `Date_Time`
- `Global_active_power`
- `Global_reactive_power`
- `Voltage`
- `Global_intensity`
- `Sub_metering_1`
- `Sub_metering_2`
- `Sub_metering_3`

If the downloaded CSV has slightly different column names, update `COLUMN_MAP` in `backend/preprocessing/prepare_data.py`.

## 4. Prepare data and train

From `backend/`, with `.venv` active:
```bash
python preprocessing/inspect_dataset.py
python preprocessing/prepare_data.py
python training/train_models.py
```

Training uses chronological splits (70% train, 15% validation, 15% test), compares five regressors, selects the best model by validation RMSE, and evaluates it once on the held-out test set.

Artifacts are saved under `backend/models/`:
- `best_model.joblib`
- `model_comparison.csv`
- `feature_columns.json`
- `test_metrics.json`

## 5. Run API

From `backend/`:
```bash
python -m uvicorn main:app --reload
```

Open:
- http://127.0.0.1:8000
- http://127.0.0.1:8000/docs

The `/predict` endpoint expects current sensor readings plus the recent active-power history fields used by the model. The frontend demo form includes these fields.

## 6. Run React frontend

Open a second Git Bash terminal:
```bash
cd frontend
npm install
npm run dev
```
Open the local URL printed by Vite (normally http://localhost:5173).

## 7. Important notes
- Keep the backend terminal running while using the frontend.
- The frontend talks to `http://127.0.0.1:8000`.
- For Vercel, deploy only `frontend/`. Deploy the Python API separately to a Python-compatible host.
- Do not train on `Date_Time`, `segment_id`, or `target_next_hour` as input features.
- This is a project starter, not a claim that a model has already been trained. Train it with your dataset before using predictions.
