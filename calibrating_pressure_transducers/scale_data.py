import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score, roc_curve, auc
import matplotlib.pyplot as plt

# Folder containing the CSV files (raw data)
folder_path = '/Users/colehanan/Desktop/combined_csv_files'

# List to hold dataframes
dataframes = []

# Iterate through all CSV files in the folder and load the data
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

        # Handle missing values by dropping rows with missing required columns
        if df[required_cols].isnull().any().any():
            print(f"Warning: Missing values detected in file {file_path}. Dropping rows with missing data.")
            df = df.dropna(subset=required_cols).reset_index(drop=True)

        dataframes.append(df)

# Concatenate all dataframes into one combined dataframe
combined_df = pd.concat(dataframes, ignore_index=True)

# Separate features (X) and target (y)
features = ['pressure0', 'pressure1', 'pressure2', 'LPS_pressure', 'LPS_temperature']
X = combined_df[features]
y = combined_df['Measured_pressure']

print("Original Data shape:", X.shape, "Features:", list(X.columns))

# -------------------------
# SCALE THE FEATURES
# -------------------------
# Create a StandardScaler instance and fit on the feature data
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Create a new DataFrame with scaled features and include Measured_pressure column unscaled
df_scaled = pd.DataFrame(X_scaled, columns=features)
df_scaled['Measured_pressure'] = y.values

# Save the scaled data to a new CSV file
scaled_csv_path = 'scaled_combined_data.csv'
df_scaled.to_csv(scaled_csv_path, index=False)
print(f"Scaled combined data saved to '{scaled_csv_path}'.")

# Optionally, display the means and scales (should be close to 0 and 1, respectively)
print("Scaling means:", scaler.mean_)
print("Scaling scales:", scaler.scale_)

# -------------------------
# TRAINING THE MODEL
# -------------------------
# Note: Even though we saved scaled data, we will use the original raw features for training
# in a pipeline that includes scaling. This ensures that if you want to deploy on new raw data,
# the same scaling is applied.

# Split data into train and test sets (70% train, 30% test)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.30, random_state=42
)

# Define a pipeline that scales the features and then fits an MLPRegressor.
# Even if you later use scaled CSV files for prediction, keeping scaling in the pipeline
# ensures consistency.
mlp_model = Pipeline([
    ('scaler', StandardScaler()),  # scales raw features
    ('regressor', MLPRegressor(hidden_layer_sizes=(10,), activation='tanh',
                                solver='lbfgs', max_iter=100000000000000000000000000000000000000000000000,  # increase iterations if needed
                                random_state=42))
])

# Train the model on the training set
mlp_model.fit(X_train, y_train)

# Model training complete. Evaluate on the test set.
y_pred = mlp_model.predict(X_test)

# Compute evaluation metrics
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
r2 = r2_score(y_test, y_pred)
print(f"Test RMSE: {rmse:.3f}")
print(f"Test R^2: {r2:.3f}")

# Save actual vs. predicted pressures to a CSV for review
results_df = pd.DataFrame({
    'Measured_pressure': y_test.values,
    'Predicted_pressure': y_pred
})
results_df.to_csv('calibrated_predictions.csv', index=False)
print("Calibrated predictions saved to 'calibrated_predictions.csv'.")

# -------------------------
# PLOT RESULTS
# -------------------------
# Plot Predicted vs Actual Pressure
plt.figure(figsize=(6,5))
plt.scatter(y_test, y_pred, color='blue', alpha=0.6, label='Predicted')
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', label='Ideal fit')
plt.xlabel('Actual Measured Pressure')
plt.ylabel('Predicted Pressure')
plt.title('Predicted vs Actual Pressure')
plt.legend()
plt.tight_layout()
plt.show()

# (Optional) Plot ROC curve for classification of high-pressure events.
# For demonstration, we classify pressures above the median as "high."
threshold = np.median(y_test)
y_test_binary = (y_test.values > threshold).astype(int)
y_score = y_pred  # using the continuous model outputs as scores
fpr, tpr, _ = roc_curve(y_test_binary, y_score)
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

# -------------------------
# EXTRACT NEURAL NETWORK PARAMETERS
# -------------------------
# To get an explicit representation of the trained neural network, extract weights and biases.
mlp_regressor = mlp_model.named_steps['regressor']
W1 = mlp_regressor.coefs_[0]
b1 = mlp_regressor.intercepts_[0]
w2 = mlp_regressor.coefs_[1]
b2 = mlp_regressor.intercepts_[1]

print("Hidden Layer Weights (W1):\n", W1)
print("Hidden Layer Biases (b1):\n", b1)
print("Output Layer Weights (w2):\n", w2)
print("Output Layer Bias (b2):\n", b2)

# Example of using the extracted parameters for a new raw input (after scaling):
# Suppose x_new is a new raw sensor input as a NumPy array in the same order as the features.
# Make sure to scale it using the same scaler (fitted on training data).
# x_new = np.array([raw_pressure0, raw_pressure1, raw_pressure2, raw_LPS_pressure, raw_LPS_temperature])
# x_new_scaled = mlp_model.named_steps['scaler'].transform([x_new])
# hidden = np.tanh(np.dot(x_new_scaled, W1) + b1)
# calibrated_pressure = np.dot(hidden, w2) + b2
# print("Calibrated pressure for new input:", calibrated_pressure)
