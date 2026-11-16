from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/raw")
candidates = list(RAW_DIR.glob("*.csv"))
if not candidates:
    raise FileNotFoundError(
        f"No CSV found in {RAW_DIR.resolve()}. Add your dataset CSV first."
    )

for path in candidates:
    print(f"\nFILE: {path.name} ({path.stat().st_size:,} bytes)")
    df = pd.read_csv(path, low_memory=False)
    print("Shape:", df.shape)
    print("Columns:", df.columns.tolist())
    print("\nFirst 5 rows:")
    print(df.head().to_string())
    print("\nMissing values:")
    print(df.isna().sum().to_string())
    print("\nData types:")
    print(df.dtypes.to_string())
