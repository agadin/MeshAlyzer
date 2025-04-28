#!/usr/bin/env python3
"""
train_deflation_time_model.py

Loads MeshAlyzer summary CSVs (with vent_duration),
trains a RandomForestRegressor to predict deflation time,
evaluates performance, plots results, and saves the model.
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import joblib  # for saving/loading model


def load_summary_data(folder_path: Path) -> pd.DataFrame:
    """
    Reads all summary CSVs in folder_path matching '*summary_*.csv'
    and assembles a DataFrame with:
      - initial_pressure: avg_post
      - pre_inflation_pressure: avg_pre
      - supply_pressure: avg_in
      - deflation_time: vent_duration
    """
    rows = []
    for file in folder_path.glob("*summary_*.csv"):
        df = pd.read_csv(file)
        # Skip files missing the required column
        if "vent_duration" not in df.columns:
            continue

        for _, row in df.iterrows():
            rows.append({
                "initial_pressure": row["avg_post"],
                "pre_inflation_pressure": row["avg_pre"],
                "supply_pressure": row["avg_in"],
                "deflation_time": row["vent_duration"],
            })

    data = pd.DataFrame(rows)
    return data


def train_and_evaluate(data: pd.DataFrame,
                       test_size: float = 0.2,
                       random_state: int = 42):
    """
    Splits data, trains RandomForestRegressor on deflation_time,
    and returns the model plus test split and predictions.
    """
    # Features & target
    X = data[["initial_pressure", "pre_inflation_pressure", "supply_pressure"]]
    y = data["deflation_time"]

    # Train/Test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    # Train the model
    model = RandomForestRegressor(n_estimators=100, random_state=random_state)
    model.fit(X_train, y_train)

    # Predict on test set
    preds = model.predict(X_test)

    # Metrics
    mse = mean_squared_error(y_test, preds)
    r2 = r2_score(y_test, preds)
    print(f"Deflation Time Model\n• Mean Squared Error: {mse:.5f}\n• R² Score: {r2:.5f}\n")

    return model, X_test, y_test, preds


def plot_deflation_results(y_test, preds):
    """
    Scatterplot: Predicted vs. Actual deflation times.
    """
    plt.figure(figsize=(8, 6))
    plt.scatter(y_test, preds, alpha=0.6)
    lims = [min(y_test.min(), preds.min()), max(y_test.max(), preds.max())]
    plt.plot(lims, lims, '--', color='red', label='Ideal (y = x)')
    plt.xlabel("Actual Deflation Time [s]")
    plt.ylabel("Predicted Deflation Time [s]")
    plt.title("Predicted vs Actual Deflation Time")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()


def main():
    # 1. Folder containing your summary CSVs
    folder = Path("/Users/colehanan/Desktop/WashuClasses/MeshAlyzer/getting_Q")

    # 2. Load data
    print("Loading summary data (vent_duration)...")
    df = load_summary_data(folder)
    if df.empty:
        print("No summary CSVs with 'vent_duration' found in:", folder)
        return

    # 3. Train model & evaluate
    print("Training deflation-time model...")
    model, X_test, y_test, preds = train_and_evaluate(df)

    # 4. Plot results
    print("Plotting model performance...")
    plot_deflation_results(y_test, preds)

    # 5. Save model
    out_path = "deflation_time_model.pkl"
    joblib.dump(model, out_path)
    print(f"Model saved to {out_path}")


if __name__ == "__main__":
    main()