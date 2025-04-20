import joblib
import numpy as np

# Load your trained model
model_path = "/Users/colehanan/Desktop/WashuClasses/MeshAlyzer/getting_Q/inflation_time_model.pkl"
model = joblib.load(model_path)

def predict_duration(avg_pre, avg_input, avg_post):
    X = np.array([[avg_pre, avg_input, avg_post]])
    predicted_time = model.predict(X)[0]
    return round(predicted_time, 4)

if __name__ == "__main__":
    # --- USER INPUT ---
    avg_pre = 0.0       # psi, initial pressure
    avg_input = 50.0    # psi, supply pressure
    avg_post = 1.8      # psi, target pressure

    # Predict
    duration = predict_duration(avg_pre, avg_input, avg_post)
    print(f"Predicted inflation time: {duration} seconds")
