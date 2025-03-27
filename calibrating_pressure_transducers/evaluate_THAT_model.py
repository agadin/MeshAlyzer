from sklearn.metrics import mean_squared_error, r2_score, roc_curve, auc

# Predict on the test set
y_pred = mlp_model.predict(X_test)

# Compute evaluation metrics
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
r2 = r2_score(y_test, y_pred)
print(f"Test RMSE: {rmse:.3f}")
print(f"Test R^2: {r2:.3f}")

# Save actual vs predicted pressures to a CSV for review
results_df = pd.DataFrame({
    'Target_pressure': y_test.values,
    'Predicted_pressure': y_pred
})
results_df.to_csv('calibrated_predictions.csv', index=False)
print("Calibrated predictions saved to 'calibrated_predictions.csv'.")

# Plot Predicted vs Actual Pressure
import matplotlib.pyplot as plt
plt.figure(figsize=(6,5))
plt.scatter(y_test, y_pred, color='blue', alpha=0.6, label='Predicted')
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', label='Ideal fit')
plt.xlabel('Actual Target Pressure')
plt.ylabel('Predicted Pressure')
plt.title('Predicted vs Actual Pressure')
plt.legend()
plt.tight_layout()
plt.show()

# (Optional) Plot ROC curve for classification of high-pressure events
# Define a threshold for "high" pressure (using median here for demonstration)
threshold = np.median(y_test)
y_test_binary = (y_test.values > threshold).astype(int)    # true labels: 1 if high pressure, 0 if low
y_score = y_pred                                           # continuous scores from model
fpr, tpr, _ = roc_curve(y_test_binary, y_score)            # compute ROC curve
roc_auc = auc(fpr, tpr)
plt.figure(figsize=(6,5))
plt.plot(fpr, tpr, color='orange', label=f'ROC curve (AUC = {roc_auc:.2f})')
plt.plot([0,1], [0,1], 'k--', label='Random guess')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curve for High Pressure Detection')
plt.legend(loc='lower right')
plt.tight_layout()
plt.show()
