from pathlib import Path
import pandas as pd

RAW = Path("data/raw")
OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)

files = sorted(RAW.glob("*.csv"))

if not files:
    raise FileNotFoundError("No CSV dataset found in data/raw/")

source = RAW / "household_power_timeseries.csv"

if not source.exists():
    source = files[0]

df = pd.read_csv(source, low_memory=False)

# Standardize column names
df.columns = [str(c).strip() for c in df.columns]

# Support both Date_Time and separate Date + Time columns
if "Date_Time" not in df.columns:
    if "Date" in df.columns and "Time" in df.columns:
        df["Date_Time"] = (
            df["Date"].astype(str).str.strip()
            + " "
            + df["Time"].astype(str).str.strip()
        )
    else:
        raise ValueError(
            f"Cannot find Date_Time or Date and Time columns. "
            f"Found: {df.columns.tolist()}"
        )

required = [
    "Date_Time",
    "Global_active_power",
    "Global_reactive_power",
    "Voltage",
    "Global_intensity",
    "Sub_metering_1",
    "Sub_metering_2",
    "Sub_metering_3",
]

missing = [c for c in required if c not in df.columns]

if missing:
    raise ValueError(f"Missing columns: {missing}")

df = df[required].copy()

# Convert timestamp and electrical readings
df["Date_Time"] = pd.to_datetime(
    df["Date_Time"], errors="coerce"
)

for col in required[1:]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Remove invalid timestamps and target values
df = df.dropna(
    subset=["Date_Time", "Global_active_power"]
)

df = (
    df.sort_values("Date_Time")
    .drop_duplicates("Date_Time")
    .reset_index(drop=True)
)

# Fill missing sensor values
for col in required[2:]:
    df[col] = df[col].fillna(df[col].median())

# Identify continuous hourly sequences
df["segment_id"] = (
    df["Date_Time"].diff() != pd.Timedelta(hours=1)
).cumsum()

target = "Global_active_power"
grouped = df.groupby("segment_id", sort=False)[target]

# Previous-hour power values
for lag in (1, 2, 3):
    df[f"power_lag_{lag}"] = grouped.shift(lag)

# Rolling average of previous three hours
df["power_rolling_mean_3"] = grouped.transform(
    lambda series: series.rolling(
        window=3, min_periods=3
    ).mean()
)

# Time-based features
df["hour"] = df["Date_Time"].dt.hour
df["day_of_week"] = df["Date_Time"].dt.day_of_week

# Predict the next hour
df["target_next_hour"] = grouped.shift(-1)

before = len(df)
df = df.dropna().reset_index(drop=True)

if df.empty:
    raise ValueError(
        "No rows remain after feature engineering. "
        "Check dataset timestamps and missing values."
    )

output = OUT / "energy_features.csv"
df.to_csv(output, index=False)

print("\nPREPROCESSING COMPLETED")
print("-----------------------")
print("Input file:", source.name)
print("Original rows:", before)
print("Final rows:", len(df))
print("Continuous sequences:", df["segment_id"].nunique())
print("Saved file:", output.resolve())
print("Feature columns:")

for col in df.columns:
    print("-", col)
