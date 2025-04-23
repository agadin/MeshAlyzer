#!/usr/bin/env python3
import os
import numpy as np
import pandas as pd
from pathlib import Path
from joblib import dump
import matplotlib.pyplot as plt
import warnings

plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 12,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'axes.linewidth': 1.2,
    'xtick.direction': 'in',
    'ytick.direction': 'in',
    'xtick.major.size': 5,
    'ytick.major.size': 5,
    'xtick.minor.visible': True,
    'xtick.minor.size': 3,
    'ytick.minor.visible': True,
    'ytick.minor.size': 3,
    'grid.linestyle': '--',
    'grid.alpha': 0.3,
    'savefig.dpi': 300,
    'figure.dpi': 300
})



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
            required = ['Measured_pressure']
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
                rmse = mean_squared_error(y_, pred)
                r2 = r2_score(y_, pred)
                mae = mean_absolute_error(y_, pred)
                print(f"{sensor} {name}: RMSE={np.sqrt(rmse):.3f}, "
                      f"R²={r2_score(y_, pred):.3f}, "
                      f"MAE={mean_absolute_error(y_, pred):.3f}")
                # if this is the Test set, save the raw data to CSV
                if name == 'Test':
                    results_df = pd.DataFrame({
                        'Measured_pressure': y_.values,
                        'Predicted_pressure': pred,
                        'Residual': (y_.values - pred)
                    })
                    out_path = Path(self.data_folder) / f"{sensor}_test_results.csv"
                    results_df.to_csv(out_path, index=False)
                    print(f"Saved test results for {sensor} → {out_path}")

                self._plot_evaluation(y_, pred, sensor, name, rmse, r2, mae)

            eval_set(X_val, y_val, 'Validation')
            eval_set(X_test, y_test, 'Test')

            self.models[sensor] = model

        dump(self.models, 'trained_pressure_calibrator_multioutput.joblib')
        print("All models saved to trained_pressure_calibrator_multioutput.joblib")

    def _plot_evaluation(self, y_true, y_pred, sensor, dataset, rmse, r2, mae):
        # Combined figure with Observed vs Predicted and Residuals
        fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=False)

        # Observed vs Predicted
        ax = axes[0]
        ax.scatter(y_true, y_pred, s=30, edgecolor='black', facecolor='none', alpha=0.7)
        max_val = max(y_true.max(), y_pred.max())
        ax.plot([0, max_val], [0, max_val], linestyle='--', linewidth=1, color='red')
        ax.set_title(f"{sensor} {dataset}\nObserved vs Predicted")
        ax.set_xlabel("Measured Pressure (PSI)")
        ax.set_ylabel("Predicted Pressure (PSI)")
        ax.set_aspect('equal', 'box')
        ax.grid(True)
        ax.text(0.05, 0.95, f"$R^2$={r2:.2f}\nRMSE={rmse:.2f}\nMAE={mae:.2f}",
                transform=ax.transAxes, verticalalignment='top',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.5))

        # Residuals
        ax = axes[1]
        residuals = y_true - y_pred
        ax.scatter(y_true, residuals, s=30, edgecolor='black', facecolor='none', alpha=0.7)
        ax.axhline(0, linestyle='--', linewidth=1, color='red')
        ax.set_title(f"{sensor} {dataset}\nResiduals")
        ax.set_xlabel("Measured Pressure (PSI)")
        ax.set_ylabel("Residual (PSI)")
        ax.grid(True)

        plt.tight_layout()
        # Save as high-resolution vector
        save_path = Path(self.data_folder) / f"{sensor}_{dataset}_evaluation.pdf"
        fig.savefig(save_path, bbox_inches='tight')
        plt.show()

    def pressure_sensor_converter_main(self, p0, p1, p2, *args, **kwargs):
        if not self.models:
            raise ValueError("Models not trained.")
        conv = []
        for sensor, val in zip(['pressure0','pressure1','pressure2'], [p0,p1,p2]):
            pred = self.models[sensor].predict([[val]])[0]
            conv.append(round(max(pred, 0), 1))
        return tuple(conv)

if __name__ == "__main__":
    calibrator = PressureCalibrator(
        data_folder='/Users/colehanan/Desktop/WashuClasses/MeshAlyzer/betterData_150_PSI/daily_combined_csv/',
        max_iter=10000000000,
        random_state=42
    )
    calibrator.train()
