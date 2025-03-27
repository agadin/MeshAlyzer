from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score, roc_curve, auc
import numpy as np
import pandas as pd
import os

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
        required_cols = ['Measured_pressure', 'pressure0', 'pressure1', 'pressure2',
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


# Split data into train and test sets (e.g., 70% train, 30% test)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.30, random_state=42
)

# Define a pipeline with feature scaling and MLP regressor
mlp_model = Pipeline([
    ('scaler', StandardScaler()),  # feature scaling
    ('regressor', MLPRegressor(hidden_layer_sizes=(10,), activation='tanh',
                                solver='lbfgs', max_iter=1000,
                                random_state=42))
])

# Train the model on the training set
mlp_model.fit(X_train, y_train)

# Model training complete. We can now evaluate on the test set.

# Predict on the test set
y_pred = mlp_model.predict(X_test)

# Compute evaluation metrics
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
r2 = r2_score(y_test, y_pred)
print(f"Test RMSE: {rmse:.3f}")
print(f"Test R^2: {r2:.3f}")

# Save actual vs predicted pressures to a CSV for review
results_df = pd.DataFrame({
    'Target_pressure': y_test.values,
    'Predicted_pressure': y_pred
})
results_df.to_csv('calibrated_predictions.csv', index=False)
print("Calibrated predictions saved to 'calibrated_predictions.csv'.")

# Plot Predicted vs Actual Pressure
import matplotlib.pyplot as plt
plt.figure(figsize=(6,5))
plt.scatter(y_test, y_pred, color='blue', alpha=0.6, label='Predicted')
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', label='Ideal fit')
plt.xlabel('Actual Target Pressure')
plt.ylabel('Predicted Pressure')
plt.title('Predicted vs Actual Pressure')
plt.legend()
plt.tight_layout()
plt.show()

# (Optional) Plot ROC curve for classification of high-pressure events
# Define a threshold for "high" pressure (using median here for demonstration)
threshold = np.median(y_test)
y_test_binary = (y_test.values > threshold).astype(int)    # true labels: 1 if high pressure, 0 if low
y_score = y_pred                                           # continuous scores from model
fpr, tpr, _ = roc_curve(y_test_binary, y_score)            # compute ROC curve
roc_auc = auc(fpr, tpr)
plt.figure(figsize=(6,5))
plt.plot(fpr, tpr, color='orange', label=f'ROC curve (AUC = {roc_auc:.2f})')
plt.plot([0,1], [0,1], 'k--', label='Random guess')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curve for High Pressure Detection')
plt.legend(loc='lower right')
plt.tight_layout()
plt.show()
