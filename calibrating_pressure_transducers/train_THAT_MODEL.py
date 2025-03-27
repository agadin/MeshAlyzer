from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline

# Split data into train and test sets (e.g., 70% train, 30% test)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.30, random_state=42
)

# Define a pipeline with feature scaling and MLP regressor
mlp_model = Pipeline([
    ('scaler', StandardScaler()),  # feature scaling
    ('regressor', MLPRegressor(hidden_layer_sizes=(10,), activation='tanh',
                                solver='lbfgs', max_iter=1000,
                                random_state=42))
])

# Train the model on the training set
mlp_model.fit(X_train, y_train)

# Model training complete. We can now evaluate on the test set.
