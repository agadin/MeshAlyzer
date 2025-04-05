import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks, regularizers, initializers
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

# Suppress TensorFlow warnings (optional)
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

class PressureCalibratorKeras:
    def __init__(self, data_folder, random_state=42):
        self.data_folder = data_folder
        self.random_state = random_state
        self.models = {}  # Dictionary to store individual models for each sensor

    def load_data(self):
        """
        Load and concatenate CSV files from the specified folder.
        Each CSV must contain at least the following columns:
            'Measured_pressure', 'pressure0', 'pressure1', 'pressure2'
        Rows with missing sensor data are dropped for that sensor's training.
        Returns:
            combined_df (DataFrame): Combined data from all CSV files.
        """
        dataframes = []
        for filename in os.listdir(self.data_folder):
            if filename.endswith('.csv'):
                file_path = os.path.join(self.data_folder, filename)
                try:
                    df = pd.read_csv(file_path)
                except Exception as e:
                    print(f"Error reading CSV file {file_path}: {e}")
                    continue

                # Required columns
                required_cols = ['Measured_pressure', 'pressure0', 'pressure1', 'pressure2']
                for col in required_cols:
                    if col not in df.columns:
                        raise ValueError(f"Required column '{col}' not found in file {file_path}.")

                # Drop rows with missing values in the required columns
                df = df.dropna(subset=required_cols).reset_index(drop=True)
                dataframes.append(df)

        if not dataframes:
            raise ValueError("No CSV files were loaded from the folder.")
        combined_df = pd.concat(dataframes, ignore_index=True)
        return combined_df

    def build_model(self):
        """
        Build and return a Keras regression model that uses:
          - Dense layers with He Normal initialization.
          - BatchNormalization and Dropout.
          - L2 regularization.
        The model has one input (the sensor reading) and outputs one calibrated pressure.
        """
        model = models.Sequential()
        # Input layer; since input is a single value, input shape = (1,)
        model.add(layers.Input(shape=(1,)))
        # Hidden layer with 64 neurons
        model.add(layers.Dense(64,
                               kernel_initializer=initializers.he_normal(),
                               kernel_regularizer=regularizers.l2(0.001)))
        model.add(layers.BatchNormalization())
        model.add(layers.Activation('relu'))
        model.add(layers.Dropout(0.2))
        # Another hidden layer
        model.add(layers.Dense(32,
                               kernel_initializer=initializers.he_normal(),
                               kernel_regularizer=regularizers.l2(0.001)))
        model.add(layers.BatchNormalization())
        model.add(layers.Activation('relu'))
        model.add(layers.Dropout(0.2))
        # Output layer
        model.add(layers.Dense(1, activation='linear'))
        return model

    def train(self, epochs=100, batch_size=32):
        """
        Train separate models for each sensor (pressure0, pressure1, pressure2) using the sensor's raw value only.
        The target is Measured_pressure.
        The data is split into training, validation, and test sets.
        Training uses early stopping and learning rate scheduling.
        """
        combined_df = self.load_data()
        sensors = ['pressure0', 'pressure1', 'pressure2']

        for sensor in sensors:
            # Use sensor reading as the sole feature
            X = combined_df[[sensor]].values  # shape (n_samples, 1)
            y = combined_df['Measured_pressure'].values  # shape (n_samples,)

            print(f"\nTraining model for {sensor} (Data shape: {X.shape})")

            # First split into train+validation (70%) and test (30%)
            X_train_val, X_test, y_train_val, y_test = train_test_split(
                X, y, test_size=0.30, random_state=self.random_state
            )
            # Then split train+validation into training (80%) and validation (20%)
            X_train, X_val, y_train, y_val = train_test_split(
                X_train_val, y_train_val, test_size=0.20, random_state=self.random_state
            )

            # Build model
            model = self.build_model()
            model.compile(optimizer=tf.keras.optimizers.Adam(),
                          loss='mse')

            # Callbacks for early stopping and learning rate reduction
            early_stop = callbacks.EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
            reduce_lr = callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-6)

            # Train the model
            history = model.fit(X_train, y_train,
                                validation_data=(X_val, y_val),
                                epochs=epochs,
                                batch_size=batch_size,
                                callbacks=[early_stop, reduce_lr],
                                verbose=1)

            # Evaluate on validation set
            y_val_pred = model.predict(X_val).flatten()
            mse_val = mean_squared_error(y_val, y_val_pred)
            rmse_val = np.sqrt(mse_val)
            r2_val = r2_score(y_val, y_val_pred)
            mae_val = mean_absolute_error(y_val, y_val_pred)
            print(f"{sensor} Validation: RMSE: {rmse_val:.3f}, R^2: {r2_val:.3f}, MAE: {mae_val:.3f}")

            # Evaluate on test set
            y_test_pred = model.predict(X_test).flatten()
            mse_test = mean_squared_error(y_test, y_test_pred)
            rmse_test = np.sqrt(mse_test)
            r2_test = r2_score(y_test, y_test_pred)
            mae_test = mean_absolute_error(y_test, y_test_pred)
            print(f"{sensor} Test: RMSE: {rmse_test:.3f}, R^2: {r2_test:.3f}, MAE: {mae_test:.3f}")

            # Produce evaluation plots for the validation set.
            self._plot_evaluation(y_val, y_val_pred, sensor, dataset='Validation')
            # Produce evaluation plots for the test set.
            self._plot_evaluation(y_test, y_test_pred, sensor, dataset='Test')

            # Save the trained model in the dictionary.
            self.models[sensor] = model

            # Optionally, save the model to file
            model.save(f"{sensor}_calibration_model.keras")

            print(f"Model for {sensor} saved as {sensor}_calibration_model.keras.")

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

    def pressure_sensor_converter(self, pressure0, pressure1, pressure2):
        """
        Convert raw sensor readings from each sensor into calibrated pressure values.
        Each model expects a single input feature: the sensor reading.
        """
        if not self.models:
            raise ValueError("Models are not trained. Please run the train() method first.")

        # Prepare inputs (each must be a 2D array with shape (1,1))
        input0 = np.array([[pressure0]])
        input1 = np.array([[pressure1]])
        input2 = np.array([[pressure2]])

        conv_pressure0 = self.models['pressure0'].predict(input0).flatten()[0]
        conv_pressure1 = self.models['pressure1'].predict(input1).flatten()[0]
        conv_pressure2 = self.models['pressure2'].predict(input2).flatten()[0]

        return conv_pressure0, conv_pressure1, conv_pressure2

# Example usage:
if __name__ == "__main__":
    data_folder = '/Users/colehanan/Desktop/WashuClasses/MeshAlyzer/combined_csv_files/'
    calibrator = PressureCalibratorKeras(data_folder=data_folder)
    calibrator.train(epochs=100, batch_size=32)
