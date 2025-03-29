import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score, roc_curve, auc
import matplotlib.pyplot as plt
from joblib import dump

class PressureCalibrator:
    def __init__(self, data_folder=None, max_iter=100000000000000000000000000000000000000000000000000, random_state=42):
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
            'Measured_pressure', 'pressure0', 'pressure1', 'pressure2',
            'LPS_pressure', 'LPS_temperature'

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
                required_cols = ['Measured_pressure', 'pressure0', 'pressure1', 'pressure2',
                                 'LPS_pressure', 'LPS_temperature']
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
        Load data, split into training and test sets, and train a neural network model
        using a pipeline with StandardScaler and MLPRegressor. The trained model is stored in self.model.
        """
        combined_df = self.load_data()
        features = ['pressure0', 'pressure1', 'pressure2', 'LPS_pressure', 'LPS_temperature']
        X = combined_df[features]
        y = combined_df['Measured_pressure']
        print("Data shape:", X.shape, "Features:", features)

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
        r2 = r2_score(y_test, y_pred)
        print(f"Test RMSE: {rmse:.3f}")
        print(f"Test R^2: {r2:.3f}")

        # Save actual vs. predicted pressures to a CSV for review.
        results_df = pd.DataFrame({
            'Measured_pressure': y_test.values,
            'Predicted_pressure': y_pred
        })
        results_df.to_csv('calibrated_predictions.csv', index=False)
        print("Calibrated predictions saved to 'calibrated_predictions.csv'.")

        # (Optional) Plot Predicted vs Actual Pressure
        plt.figure(figsize=(6, 5))
        plt.scatter(y_test, y_pred, color='blue', alpha=0.6, label='Predicted')
        plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', label='Ideal fit')
        plt.xlabel('Actual Measured Pressure')
        plt.ylabel('Predicted Pressure')
        plt.title('Predicted vs Actual Pressure')
        plt.legend()
        plt.tight_layout()
        plt.show()

        # (Optional) Plot ROC curve for high-pressure detection classification.
        threshold = np.median(y_test)
        y_test_binary = (y_test.values > threshold).astype(int)
        fpr, tpr, _ = roc_curve(y_test_binary, y_pred)
        roc_auc = auc(fpr, tpr)
        plt.figure(figsize=(6, 5))
        plt.plot(fpr, tpr, color='orange', label=f'ROC curve (AUC = {roc_auc:.2f})')
        plt.plot([0, 1], [0, 1], 'k--', label='Random guess')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('ROC Curve for High Pressure Detection')
        plt.legend(loc='lower right')
        plt.tight_layout()
        plt.show()

    def predict(self, raw_input):
        """
        Predict the calibrated pressure for new raw sensor data.

        Parameters:
            raw_input (list or list of lists): The raw sensor values. Each sample must be a list
                in the order: [pressure0, pressure1, pressure2, LPS_pressure, LPS_temperature].

        Returns:
            prediction (numpy array): The calibrated pressure predictions.
        """
        if self.model is None:
            raise ValueError("Model is not trained. Call the train() method first.")

        # Ensure raw_input is 2D (list of samples); if a single sample is provided, wrap it.
        if isinstance(raw_input[0], (int, float)):
            input_data = [raw_input]
        else:
            input_data = raw_input

        prediction = self.model.predict(input_data)
        return prediction

    def get_neural_network_parameters(self):
        """
        Extracts the neural network parameters (weights and biases) from the trained model.
        Returns:
            A dictionary with keys: 'W1', 'b1', 'w2', 'b2'
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
    # Initialize with the folder containing your training CSV files.
    calibrator = PressureCalibrator(data_folder='/Users/colehanan/Desktop/scaled_combined_csv_files')

    # Train the model
    calibrator.train()

    # Assuming calibrator.model holds your trained Pipeline
    dump(calibrator.model, 'trained_pressure_calibrator.joblib')
    print("Model saved to 'trained_pressure_calibrator.joblib'")
