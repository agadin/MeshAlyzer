import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score, roc_curve, auc
import matplotlib.pyplot as plt
from joblib import dump, load


class PressureCalibrator:
    def __init__(self, data_folder=None, max_iter=900000000000000000000000000000000000000000000000000009090909090909090909090900, random_state=42):
        """
        Initialize the PressureCalibrator.

        Parameters:
            data_folder (str): Path to folder containing CSV files for training.
            max_iter (int): Maximum number of iterations for the neural network.
            random_state (int): Random state for reproducibility.
        """
        self.data_folder = data_folder
        self.max_iter = max_iter
        self.random_state = random_state
        self.model = None  # Will hold the pipeline after training

    def load_data(self):
        """
        Load and concatenate CSV files from the provided folder.
        Each CSV must contain the following columns:
            'Measured_pressure', 'pressure0', 'pressure1', 'pressure2'
            (other columns will be ignored)
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

                # Verify that all required columns are present
                required_cols = ['Measured_pressure', 'pressure0', 'pressure1', 'pressure2']
                for col in required_cols:
                    if col not in df.columns:
                        raise ValueError(f"Required column '{col}' not found in file {file_path}.")

                # Drop rows with missing data in required columns
                if df[required_cols].isnull().any().any():
                    print(f"Warning: Missing values in file {file_path}. Dropping rows with missing data.")
                    df = df.dropna(subset=required_cols).reset_index(drop=True)

                dataframes.append(df)

        if not dataframes:
            raise ValueError("No CSV files were loaded from the folder.")

        combined_df = pd.concat(dataframes, ignore_index=True)
        return combined_df

    def train(self):
        """
        Train a multi-output model using only the sensor readings (pressure0, pressure1, pressure2)
        as features. The target is a three-column DataFrame where each column is the Measured_pressure.
        This setup allows the model to share hidden layers and learn calibration for all sensors simultaneously.
        """
        combined_df = self.load_data()
        features = ['pressure0', 'pressure1', 'pressure2']
        X = combined_df[features]

        # Create a multi-output target: each sensor's calibrated pressure should equal Measured_pressure.
        # (This allows the model to learn sensor-specific biases while sharing representations.)
        y = pd.DataFrame({
            'calibrated0': combined_df['Measured_pressure'],
            'calibrated1': combined_df['Measured_pressure'],
            'calibrated2': combined_df['Measured_pressure']
        })

        print("Training data shape:", X.shape, "Features:", features)

        # Split data into train (70%) and test (30%) sets.
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.30, random_state=self.random_state
        )

        # Create a pipeline that scales the data and trains an MLP regressor.
        self.model = Pipeline([
            ('scaler', StandardScaler()),
            ('regressor', MLPRegressor(hidden_layer_sizes=(10,),
                                       activation='tanh',
                                       solver='lbfgs',
                                       max_iter=self.max_iter,
                                       random_state=self.random_state))
        ])

        # Train the model on the training set.
        self.model.fit(X_train, y_train)

        # Evaluate the model on the test set.
        y_pred = self.model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        # For multi-output, r2_score averages across outputs by default.
        r2 = r2_score(y_test, y_pred)
        print(f"Test RMSE: {rmse:.3f}")
        print(f"Test R^2: {r2:.3f}")

        # Save actual vs. predicted pressures for the first sensor to a CSV for review.
        # (All three outputs should be similar.)
        results_df = pd.DataFrame({
            'Measured_pressure': y_test['calibrated0'].values,
            'Predicted_pressure': y_pred[:, 0]
        })
        results_df.to_csv('calibrated_predictions.csv', index=False)
        print("Calibrated predictions saved to 'calibrated_predictions.csv'.")

        # (Optional) Plot Predicted vs Actual Pressure for the first sensor.
        plt.figure(figsize=(6, 5))
        plt.scatter(y_test['calibrated0'], y_pred[:, 0], color='blue', alpha=0.6, label='Predicted')
        plt.plot([y_test['calibrated0'].min(), y_test['calibrated0'].max()],
                 [y_test['calibrated0'].min(), y_test['calibrated0'].max()], 'r--', label='Ideal fit')
        plt.xlabel('Actual Measured Pressure')
        plt.ylabel('Predicted Pressure')
        plt.title('Predicted vs Actual Pressure (Sensor 0)')
        plt.legend()
        plt.tight_layout()
        plt.show()

    def pressure_sensor_converter(self, raw_input):
        """
        Convert raw sensor readings into calibrated pressures for all sensors.

        Parameters:
            raw_input (list): A list of three raw sensor readings in the order:
                              [pressure0, pressure1, pressure2]

        Returns:
            numpy array: A 1D array with three calibrated pressure values.
        """
        if self.model is None:
            raise ValueError("Model is not trained. Call the train() method first.")

        # Ensure raw_input is a 2D array (one sample).
        if isinstance(raw_input[0], (int, float)):
            input_data = [raw_input]
        else:
            input_data = raw_input

        prediction = self.model.predict(input_data)
        # prediction shape will be (n_samples, 3); for a single sample, return the first row.
        return prediction[0]

    def get_neural_network_parameters(self):
        """
        Extracts the neural network parameters (weights and biases) from the trained model.
        Returns:
            Dictionary with keys: 'W1', 'b1', 'w2', 'b2'
        """
        if self.model is None:
            raise ValueError("Model is not trained. Call the train() method first.")

        mlp_regressor = self.model.named_steps['regressor']
        params = {
            'W1': mlp_regressor.coefs_[0],
            'b1': mlp_regressor.intercepts_[0],
            'w2': mlp_regressor.coefs_[1],
            'b2': mlp_regressor.intercepts_[1]
        }
        return params


# Example usage in another file:
if __name__ == "__main__":
    # If training, set data_folder to where your CSV files are stored.
    calibrator = PressureCalibrator(data_folder='/Users/colehanan/Desktop/scaled_combined_csv_files')

    # Train the multi-output model.
    calibrator.train()

    # Save the trained model for later use.
    dump(calibrator.model, 'trained_pressure_calibrator_multioutput.joblib')
    print("Model saved to 'trained_pressure_calibrator_multioutput.joblib'.")
