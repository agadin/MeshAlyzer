import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.compose import TransformedTargetRegressor
from joblib import dump
import matplotlib.pyplot as plt

import warnings
warnings.filterwarnings(
    "ignore",
    message="X does not have valid feature names, but StandardScaler was fitted with feature names",
    category=UserWarning
)

class PressureCalibrator:
    def __init__(self, data_folder=None, max_iter=100000, random_state=42):
        self.data_folder = data_folder
        self.max_iter = max_iter
        self.random_state = random_state
        self.models = {}  # Dictionary to store individual models for each sensor

    def load_data(self):
        """
        Load and concatenate CSV files from the provided folder.
        Each CSV must contain at least the following columns:
            'Measured_pressure', 'LPS_pressure', 'LPS_temperature'
        Sensor columns (pressure0, pressure1, pressure2) are also expected but may have missing values.
        Returns:
            combined_df (DataFrame): Combined data from all CSV files.
        """
        if self.data_folder is None:
            raise ValueError("data_folder is not specified.")

        dataframes = []
        for filename in os.listdir(self.data_folder):
            if filename.endswith('.csv'):
                file_path = os.path.join(self.data_folder, filename)
                try:
                    df = pd.read_csv(file_path)
                except Exception as e:
                    print(f"Error reading CSV file {file_path}: {e}")
                    continue

                # Always required columns
                required_cols = ['Measured_pressure', 'LPS_pressure', 'LPS_temperature']
                for col in required_cols:
                    if col not in df.columns:
                        raise ValueError(f"Required column '{col}' not found in file {file_path}.")

                # Drop rows with missing values in always required columns
                if df[required_cols].isnull().any().any():
                    print(f"Warning: Missing values in {required_cols} in file {file_path}. Dropping those rows.")
                    df = df.dropna(subset=required_cols).reset_index(drop=True)

                dataframes.append(df)

        if not dataframes:
            raise ValueError("No CSV files were loaded from the folder.")

        combined_df = pd.concat(dataframes, ignore_index=True)
        return combined_df

    def train(self):
        """
        Train separate models for each sensor (pressure0, pressure1, pressure2) using only the sensor's raw value.
        The target is Measured_pressure. Data is split into training, validation, and test sets.
        After training, the method evaluates and plots metrics on both the validation and test sets.
        The target is scaled using TransformedTargetRegressor to improve convergence.
        """
        combined_df = self.load_data()
        sensors = ['pressure0', 'pressure1', 'pressure2']

        for sensor in sensors:
            # Use only the sensor's raw value as the feature.
            features = [sensor]
            # Drop rows if the sensor reading is missing
            df_sensor = combined_df.dropna(subset=[sensor])
            X = df_sensor[features]
            y = df_sensor['Measured_pressure']
            print(f"\nTraining model for {sensor} with features: {features} (Data shape: {X.shape})")

            # First split into train+validation and test sets (e.g., 70% train+val, 30% test)
            X_train_val, X_test, y_train_val, y_test = train_test_split(
                X, y, test_size=0.30, random_state=self.random_state
            )
            # Then split the train+validation into training and validation sets (e.g., 80% train, 20% validation)
            X_train, X_val, y_train, y_val = train_test_split(
                X_train_val, y_train_val, test_size=0.20, random_state=self.random_state
            )

            # Create a pipeline that scales the feature(s) and trains an MLP regressor.
            base_regressor = MLPRegressor(hidden_layer_sizes=(10,),
                                          activation='tanh',
                                          solver='lbfgs',
                                          max_iter=self.max_iter,
                                          random_state=self.random_state)
            regressor = TransformedTargetRegressor(
                regressor=base_regressor,
                transformer=StandardScaler()
            )
            model = Pipeline([
                ('scaler', StandardScaler()),
                ('regressor', regressor)
            ])

            # Train the model on the training set.
            model.fit(X_train, y_train)

            # Evaluate on the validation set.
            y_val_pred = model.predict(X_val)
            mse_val = mean_squared_error(y_val, y_val_pred)
            rmse_val = np.sqrt(mse_val)
            r2_val = r2_score(y_val, y_val_pred)
            mae_val = mean_absolute_error(y_val, y_val_pred)
            print(f"{sensor} Validation: RMSE: {rmse_val:.3f}, R^2: {r2_val:.3f}, MAE: {mae_val:.3f}")

            # Evaluate on the test set.
            y_test_pred = model.predict(X_test)
            mse_test = mean_squared_error(y_test, y_test_pred)
            rmse_test = np.sqrt(mse_test)
            r2_test = r2_score(y_test, y_test_pred)
            mae_test = mean_absolute_error(y_test, y_test_pred)
            print(f"{sensor} Test: RMSE: {rmse_test:.3f}, R^2: {r2_test:.3f}, MAE: {mae_test:.3f}")

            # Produce evaluation plots for the validation set.
            self._plot_evaluation(y_val, y_val_pred, sensor, dataset='Validation')
            # Produce evaluation plots for the test set.
            self._plot_evaluation(y_test, y_test_pred, sensor, dataset='Test')

            # Store the model for this sensor.
            self.models[sensor] = model

        # Optionally, save all models to a file.
        dump(self.models, 'trained_pressure_calibrator_multioutput.joblib')
        print("Models saved")

    def _plot_evaluation(self, y_true, y_pred, sensor, dataset='Validation'):
        """
        Generate evaluation plots: scatter, residual plot, and histogram of residuals.
        """
        # Scatter plot: Predicted vs. Actual
        plt.figure(figsize=(6, 5))
        plt.scatter(y_true, y_pred, alpha=0.6, label='Data points')
        plt.plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], 'r--', label='Ideal fit')
        plt.title(f"{sensor} - {dataset}: Predicted vs Actual")
        plt.xlabel("Measured Pressure")
        plt.ylabel("Predicted Pressure")
        plt.legend()
        plt.tight_layout()
        plt.show()

        # Residual plot: Residual vs. Actual
        residuals = y_true - y_pred
        plt.figure(figsize=(6, 5))
        plt.scatter(y_true, residuals, alpha=0.6)
        plt.axhline(y=0, color='r', linestyle='--')
        plt.title(f"{sensor} - {dataset}: Residual Plot")
        plt.xlabel("Measured Pressure")
        plt.ylabel("Residual (Measured - Predicted)")
        plt.tight_layout()
        plt.show()

        # Histogram of residuals
        plt.figure(figsize=(6, 5))
        plt.hist(residuals, bins=30, alpha=0.7)
        plt.title(f"{sensor} - {dataset}: Residual Histogram")
        plt.xlabel("Residual (Measured - Predicted)")
        plt.ylabel("Frequency")
        plt.tight_layout()
        plt.show()

    def pressure_sensor_converter_main(self, pressure0, pressure1, pressure2, LPS_pressure=None, LPS_temperature=None):
        """
        Convert raw sensor readings from each sensor into calibrated pressure values.
        Since the models are trained only on the sensor readings, LPS_pressure and LPS_temperature are not used.
        """
        if not self.models:
            raise ValueError("Models are not trained. Call the train() method first.")

        # Each model now expects a single feature: the sensor reading.
        input0 = [[pressure0]]
        input1 = [[pressure1]]
        input2 = [[pressure2]]

        conv_pressure0 = self.models['pressure0'].predict(input0)[0]
        conv_pressure1 = self.models['pressure1'].predict(input1)[0]
        conv_pressure2 = self.models['pressure2'].predict(input2)[0]

        return conv_pressure0, conv_pressure1, conv_pressure2

    def get_neural_network_parameters(self, sensor):
        """
        Extract the neural network parameters (weights and biases) from the model for a given sensor.
        """
        if sensor not in self.models:
            raise ValueError(f"Model for sensor {sensor} is not trained.")

        mlp_regressor = self.models[sensor].named_steps['regressor'].regressor
        params = {
            'W1': mlp_regressor.coefs_[0],
            'b1': mlp_regressor.intercepts_[0],
            'w2': mlp_regressor.coefs_[1],
            'b2': mlp_regressor.intercepts_[1]
        }
        return params

# Example usage:
if __name__ == "__main__":
    # Initialize the calibrator with the folder containing your training CSV files.
    calibrator = PressureCalibrator(data_folder='/Users/colehanan/Desktop/WashuClasses/MeshAlyzer/betterData_150_PSI/daily_combined_csv/')

    # Train the models for each sensor, with validation and test evaluation.
    calibrator.train()
