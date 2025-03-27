import os
import pandas as pd

# Folder containing the CSV files
folder_path = 'path/to/your/folder'

# List to hold dataframes
dataframes = []

# Iterate through all files in the folder
for filename in os.listdir(folder_path):
    if filename.endswith('.csv'):
        file_path = os.path.join(folder_path, filename)
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            print(f"Error reading CSV file {file_path}: {e}")
            continue

        # Verify that all required columns are present
        required_cols = ['Target_pressure', 'pressure0', 'pressure1', 'pressure2',
                         'LPS_pressure', 'LPS_temperature']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Required column '{col}' not found in the data of file {file_path}.")

        # Handle missing values by dropping any rows with NaNs in required columns
        if df[required_cols].isnull().any().any():
            print(f"Warning: Missing values detected in file {file_path}. Dropping rows with missing data.")
            df = df.dropna(subset=required_cols).reset_index(drop=True)

        dataframes.append(df)

# Concatenate all dataframes
combined_df = pd.concat(dataframes, ignore_index=True)

# Extract features (X) and target (y)
X = combined_df[['pressure0', 'pressure1', 'pressure2', 'LPS_pressure', 'LPS_temperature']]
y = combined_df['Target_pressure']

print("Data shape:", X.shape, "Features:", list(X.columns))
# Data is now loaded and cleaned, ready for model training.