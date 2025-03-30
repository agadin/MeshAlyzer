import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib.pyplot as plt
from joblib import dump


class PressureCalibrator:
    def __init__(self, data_folder=None, max_iter=900000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000, random_state=42):
        """
        Initialize the PressureCalibrator.
        """
        self.data_folder = data_folder
        self.max_iter = max_iter
        self.random_state = random_state
        self.models = {}  # Dictionary to store individual models for each sensor

    def load_data(self):
        """
        Load and concatenate CSV files from the provided folder.
        Each CSV must contain at least the following columns:
            'Measured_pressure', 'LPS_pressure', 'LPS_temperature'
        Sensor columns (pressure0, pressure1, pressure2) are retained even if missing.

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

                # Drop rows with missing values in always-required columns only.
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
        Train separate models for each sensor (pressure0, pressure1, pressure2).
        For each sensor, the features used are:
            [sensor, LPS_pressure, LPS_temperature]
        and the target is Measured_pressure.
        Only rows with non-missing data for the sensor being trained are used.
        The scaling of features is performed via a pipeline that includes a StandardScaler.
        """
        combined_df = self.load_data()
        sensors = ['pressure0', 'pressure1', 'pressure2']

        for sensor in sensors:
            features = [sensor, 'LPS_pressure', 'LPS_temperature']
            # Drop rows only if the sensor reading (the one being trained) is missing.
            df_sensor = combined_df.dropna(subset=[sensor])
            X = df_sensor[features]
            y = df_sensor['Measured_pressure']
            print(f"Training model for {sensor} with features: {features} (Data shape: {X.shape})")

            # Split data into train (70%) and test (30%) sets.
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.30, random_state=self.random_state
            )

            # Pipeline: First scale the features, then train the MLP regressor.
            model = Pipeline([
                ('scaler', StandardScaler()),
                ('regressor', MLPRegressor(hidden_layer_sizes=(10,),
                                           activation='tanh',
                                           solver='lbfgs',
                                           max_iter=self.max_iter,
                                           random_state=self.random_state))
            ])

            # Train the model on the training set.
            model.fit(X_train, y_train)

            # Evaluate the model on the test set.
            y_pred = model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            r2 = r2_score(y_test, y_pred)
            print(f"{sensor}: Test RMSE: {rmse:.3f}, Test R^2: {r2:.3f}")

            # Store the model for this sensor.
            self.models[sensor] = model

        # Optionally, save all models to a file.
        dump(self.models, 'trained_pressure_calibrators.joblib')
        print("Models saved to 'trained_pressure_calibrators.joblib'.")

    def pressure_sensor_converter_main(self, pressure0, pressure1, pressure2, LPS_pressure, LPS_temperature):
        import pandas as pd
        # Create DataFrames with proper column names for each sensor
        input0 = pd.DataFrame([[pressure0, LPS_pressure, LPS_temperature]],
                              columns=['pressure0', 'LPS_pressure', 'LPS_temperature'])
        input1 = pd.DataFrame([[pressure1, LPS_pressure, LPS_temperature]],
                              columns=['pressure1', 'LPS_pressure', 'LPS_temperature'])
        input2 = pd.DataFrame([[pressure2, LPS_pressure, LPS_temperature]],
                              columns=['pressure2', 'LPS_pressure', 'LPS_temperature'])

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

        mlp_regressor = self.models[sensor].named_steps['regressor']
        params = {
            'W1': mlp_regressor.coefs_[0],
            'b1': mlp_regressor.intercepts_[0],
            'w2': mlp_regressor.coefs_[1],
            'b2': mlp_regressor.intercepts_[1]
        }
        return params


# Example usage in another file:
if __name__ == "__main__":
    # Initialize the calibrator with the folder containing your training CSV files.
    calibrator = PressureCalibrator(data_folder='/Users/colehanan/Desktop/combined_csv_files')

    # Train the models for each sensor.
    calibrator.train()
