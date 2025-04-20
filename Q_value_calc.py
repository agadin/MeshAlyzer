import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import joblib  # for saving/loading model

# Path to your CSV folder
folder_path = Path("/Users/colehanan/Desktop/WashuClasses/MeshAlyzer/getting_Q")

rows = []

# Read all CSVs and extract features + label
for file in folder_path.glob("*.csv"):
    df = pd.read_csv(file)

    for _, row in df.iterrows():
        # Ensure actual_duration column exists
        if "actual_duration" not in row:
            continue  # skip if missing

        rows.append({
            "initial_pressure": row["avg_pre"],
            "supply_pressure": row["avg_input"],
            "target_pressure": row["avg_post"],
            "duration": row["actual_duration"]
        })

# Build DataFrame
data = pd.DataFrame(rows)

# Features and target
X = data[["initial_pressure", "supply_pressure", "target_pressure"]]
y = data["duration"]

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Predict and evaluate
predictions = model.predict(X_test)
mse = mean_squared_error(y_test, predictions)
r2 = r2_score(y_test, predictions)

# Plot predicted vs actual durations
plt.figure(figsize=(8, 6))
plt.scatter(y_test, predictions, alpha=0.7)
plt.plot([y.min(), y.max()], [y.min(), y.max()], '--', color='red')
plt.xlabel("Actual Inflation Time [s]")
plt.ylabel("Predicted Inflation Time [s]")
plt.title("Predicted vs Actual Inflation Time")
plt.grid(True)
plt.tight_layout()
plt.show()

print(f"Mean Squared Error: {mse:.5f}")
print(f"R² Score: {r2:.5f}")

# Save trained model
model_path = folder_path / "inflation_time_model.pkl"
joblib.dump(model, model_path)
print(f"Model saved to {model_path}")
