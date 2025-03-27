import pandas as pd
import numpy as np

# Load the CSV file into a DataFrame
try:
    df = pd.read_csv('pressure_data.csv')  # replace with your filename
except Exception as e:
    print(f"Error reading CSV file: {e}")
    raise

# Verify that all required columns are present
required_cols = ['Target_pressure', 'pressure0', 'pressure1', 'pressure2',
                 'LPS_pressure', 'LPS_temperature']
for col in required_cols:
    if col not in df.columns:
        raise ValueError(f"Required column '{col}' not found in the data.")

# Handle missing values by dropping any rows with NaNs in required columns
if df[required_cols].isnull().any().any():
    print("Warning: Missing values detected. Dropping rows with missing data.")
    df = df.dropna(subset=required_cols).reset_index(drop=True)

# Extract features (X) and target (y)
X = df[['pressure0', 'pressure1', 'pressure2', 'LPS_pressure', 'LPS_temperature']]
y = df['Target_pressure']

print("Data shape:", X.shape, "Features:", list(X.columns))
# Data is now loaded and cleaned, ready for model training.
