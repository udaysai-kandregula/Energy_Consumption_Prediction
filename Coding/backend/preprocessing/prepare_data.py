from pathlib import Path
import pandas as pd

RAW = Path("data/raw")
OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)

# Expected canonical names. Extend this map if your CSV uses other headings.
COLUMN_MAP = {
    "datetime": "Date_Time",
    "date_time": "Date_Time",
    "global_active_power": "Global_active_power",
    "global_reactive_power": "Global_reactive_power",
    "voltage": "Voltage",
    "global_intensity": "Global_intensity",
    "sub_metering_1": "Sub_metering_1",
    "sub_metering_2": "Sub_metering_2",
    "sub_metering_3": "Sub_metering_3",
}

files = sorted(RAW.glob("*.csv"))
if not files:
    raise FileNotFoundError("Place the dataset CSV in backend/data/raw/")

source = files[0]
df = pd.read_csv(source, low_memory=False)
rename = {}
for col in df.columns:
    key = str(col).strip().lower()
    if key in COLUMN_MAP:
        rename[col] = COLUMN_MAP[key]
df = df.rename(columns=rename)

required = [
    "Date_Time", "Global_active_power", "Global_reactive_power",
    "Voltage", "Global_intensity", "Sub_metering_1",
    "Sub_metering_2", "Sub_metering_3"
]
missing = [c for c in required if c not in df.columns]
if missing:
    raise ValueError(
        f"Missing expected columns: {missing}\n"
        f"Found columns: {df.columns.tolist()}\n"
        "Update COLUMN_MAP in this script to match your CSV."
    )

df = df[required].copy()
df["Date_Time"] = pd.to_datetime(df["Date_Time"], errors="coerce")
for col in required[1:]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=["Date_Time", "Global_active_power"])
df = df.sort_values("Date_Time").drop_duplicates("Date_Time").reset_index(drop=True)

# Fill missing sensor readings using medians, calculated on the available dataset.
for col in required[2:]:
    df[col] = df[col].fillna(df[col].median())

# Split sequences at time gaps so lags/targets never cross missing periods.
df["segment_id"] = (df["Date_Time"].diff() != pd.Timedelta(hours=1)).cumsum()
target = "Global_active_power"
grouped = df.groupby("segment_id", sort=False)[target]

for lag in (1, 2, 3):
    df[f"power_lag_{lag}"] = grouped.shift(lag)

df["power_rolling_mean_3"] = grouped.transform(
    lambda series: series.rolling(window=3, min_periods=3).mean()
)
df["hour"] = df["Date_Time"].dt.hour
df["day_of_week"] = df["Date_Time"].dt.dayofweek
df["target_next_hour"] = grouped.shift(-1)

before = len(df)
df = df.dropna().reset_index(drop=True)

output = OUT / "energy_features.csv"
df.to_csv(output, index=False)
print("Input file:", source.name)
print("Rows before feature filtering:", before)
print("Rows after feature engineering:", len(df))
print("Continuous sequences:", df["segment_id"].nunique())
print("Saved:", output.resolve())
print("Feature columns:", [c for c in df.columns if c not in
      ["Date_Time", "segment_id", "target_next_hour"]])
