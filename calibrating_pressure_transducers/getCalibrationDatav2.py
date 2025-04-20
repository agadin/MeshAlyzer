#!/usr/bin/env python3
import os
import numpy as np
import pandas as pd
from pathlib import Path
from joblib import dump
import matplotlib.pyplot as plt
import warnings

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, FunctionTransformer
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.compose import TransformedTargetRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

warnings.filterwarnings(
    "ignore",
    message="X does not have valid feature names, but StandardScaler was fitted with feature names",
    category=UserWarning
)

class PressureCalibrator:
    def __init__(self, data_folder=None, max_iter=10000000000, random_state=42):
        self.data_folder = data_folder
        self.max_iter = max_iter
        self.random_state = random_state
        self.models = {}

    def load_data(self):
        if self.data_folder is None:
            raise ValueError("data_folder is not specified.")
        dfs = []
        for fname in os.listdir(self.data_folder):
            if not fname.endswith('.csv'):
                continue
            path = os.path.join(self.data_folder, fname)
            df = pd.read_csv(path)
            required = ['Measured_pressure', 'LPS_pressure', 'LPS_temperature']
            if df[required].isnull().any().any():
                df = df.dropna(subset=required).reset_index(drop=True)
            df['Measured_pressure'] = df['Measured_pressure'].round(1)
            dfs.append(df)
        if not dfs:
            raise ValueError("No CSV files loaded.")
        return pd.concat(dfs, ignore_index=True)

    def train(self):
        df = self.load_data()
        sensors = ['pressure0', 'pressure1', 'pressure2']

        # target-transform to enforce >=0
        log_transform = FunctionTransformer(func=np.log1p,
                                            inverse_func=np.expm1,
                                            validate=True)

        for sensor in sensors:
            sub = df.dropna(subset=[sensor])
            X = sub[[sensor]]
            y = sub['Measured_pressure']
            print(f"\nTraining model for {sensor} (n_samples={len(y)})")

            # 80/20 train+val / test
            X_trval, X_test, y_trval, y_test = train_test_split(
                X, y, test_size=0.20, random_state=self.random_state
            )
            # 80/20 train / val
            X_train, X_val, y_train, y_val = train_test_split(
                X_trval, y_trval, test_size=0.20, random_state=self.random_state
            )

            # Base MLP with deeper layers & ReLU
            base_mlp = MLPRegressor(
                hidden_layer_sizes=(50, 25),
                activation='relu',
                solver='lbfgs',
                max_iter=self.max_iter,
                random_state=self.random_state
            )

            ttr = TransformedTargetRegressor(
                regressor=base_mlp,
                transformer=log_transform
            )

            model = Pipeline([
                ('scaler', StandardScaler()),
                ('regressor', ttr)
            ])

            # Fit
            model.fit(X_train, y_train)

            # Eval helper
            def eval_set(X_, y_, name):
                pred = model.predict(X_)
                mse = mean_squared_error(y_, pred)
                print(f"{sensor} {name}: RMSE={np.sqrt(mse):.3f}, R²={r2_score(y_, pred):.3f}, MAE={mean_absolute_error(y_, pred):.3f}")
                self._plot_evaluation(y_, pred, sensor, name)

            eval_set(X_val, y_val, 'Validation')
            eval_set(X_test, y_test, 'Test')

            self.models[sensor] = model

        dump(self.models, 'trained_pressure_calibrator_multioutput.joblib')
        print("All models saved to trained_pressure_calibrator_multioutput.joblib")

    def _plot_evaluation(self, y_true, y_pred, sensor, dataset):
        # Pred vs Actual
        plt.figure(figsize=(6,5))
        plt.scatter(y_true, y_pred, alpha=0.6)
        plt.plot([0, max(y_true.max(), y_pred.max())],
                 [0, max(y_true.max(), y_pred.max())],
                 'r--')
        plt.title(f"{sensor} {dataset} – Predicted vs Actual")
        plt.xlabel("Measured Pressure")
        plt.ylabel("Predicted Pressure")
        plt.tight_layout()
        plt.show()

        # Residuals
        res = y_true - y_pred
        plt.figure(figsize=(6,5))
        plt.scatter(y_true, res, alpha=0.6)
        plt.axhline(0, color='r', linestyle='--')
        plt.title(f"{sensor} {dataset} – Residuals")
        plt.xlabel("Measured Pressure")
        plt.ylabel("Residual")
        plt.tight_layout()
        plt.show()

    def pressure_sensor_converter_main(self, p0, p1, p2, *args, **kwargs):
        if not self.models:
            raise ValueError("Models not trained.")
        conv = []
        for sensor, val in zip(['pressure0','pressure1','pressure2'], [p0,p1,p2]):
            pred = self.models[sensor].predict([[val]])[0]
            # predictions are already >=0 thanks to log‐transform inverse
            conv.append(round(max(pred, 0), 1))
        return tuple(conv)

if __name__ == "__main__":
    calibrator = PressureCalibrator(
        data_folder='/Users/colehanan/Desktop/WashuClasses/MeshAlyzer/betterData_150_PSI/daily_combined_csv/',
        max_iter=10000000000,
        random_state=42
    )
    calibrator.train()
