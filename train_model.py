import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
# from sklearn.preprocessing import LabelEncoder  <-- No longer needed
from sklearn.metrics import r2_score, mean_absolute_error
import joblib

print("Starting Model Trainer (v2 with 'Form' features)...")

# --- 1. Load Data ---
try:
    df = pd.read_csv('f1_race_data_2018_2024.csv')
    print(f"Successfully loaded dataset with {len(df)} rows.")
except FileNotFoundError:
    print("Error: `f1_race_data_2018_2024.csv` not found.")
    print("Please run `build_dataset.py` first!")
    exit()

# --- 2. Data Cleaning & Preparation ---

# We need 'Points' and 'Position'
df['Position'] = pd.to_numeric(df['Position'], errors='coerce')
df['Points'] = pd.to_numeric(df['Points'], errors='coerce')
df['GridPosition'] = pd.to_numeric(df['GridPosition'], errors='coerce')

# Handle Rainfall
df['Rainfall'] = df['Rainfall'].apply(lambda x: 1 if x == True or x > 0 else 0)

# Sort by time. This is CRITICAL for calculating 'form'
df = df.sort_values(by=['Year', 'RoundNumber'])

# Drop rows where our target (Position) or key features are missing
df = df.dropna(subset=['Position', 'GridPosition', 'AirTemp', 'TrackTemp', 'Points'])

print(f"Rows after cleaning: {len(df)}")

# --- 3. Feature Engineering (v2 - Recent Form) ---

print("Calculating 'Recent Form' features...")

# We'll calculate a driver's average points in their last 5 races
# min_periods=1 means it will calculate even if they only have 1 race (i.e., for rookies)
df['driver_form'] = df.groupby('Abbreviation')['Points'].transform(
    lambda x: x.shift(1).rolling(window=5, min_periods=1).mean()
).fillna(0) # fillna(0) is for a driver's first-ever race

# We'll do the same for the constructor
df['constructor_form'] = df.groupby('TeamName')['Points'].transform(
    lambda x: x.shift(1).rolling(window=5, min_periods=1).mean()
).fillna(0)


# Define our features (X) and target (y)
features = [
    'GridPosition',
    # 'DriverEncoded',      <-- REMOVED
    # 'ConstructorEncoded', <-- REMOVED
    'driver_form',        # <-- NEW
    'constructor_form',   # <-- NEW
    'AirTemp',
    'TrackTemp',
    'Humidity',
    'Rainfall'
]

# This is what we want to predict
target = 'Position'

# Drop any rows that might have NaN after feature engineering (though fillna(0) should prevent it)
df = df.dropna(subset=features)

X = df[features]
y = df[target]

print(f"Using new features: {features}")
print(f"Predicting target: {target}")

# --- 4. Split Data ---
df_train = df[df['Year'] < 2024]
df_test = df[df['Year'] == 2024]

if df_test.empty or len(df_test) < 10: # Need a few test samples
    print("No 2024 data found for testing. Using random split.")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
else:
    print("Using 2024 as test set and 2018-2023 as training set.")
    X_train = df_train[features]
    y_train = df_train[target]
    X_test = df_test[features]
    y_test = df_test[target]

print(f"Training samples: {len(X_train)}, Test samples: {len(X_test)}")

# --- 5. Train Model ---
print("Training RandomForestRegressor model...")
model = RandomForestRegressor(n_estimators=100, random_state=42, min_samples_leaf=5)
model.fit(X_train, y_train)
print("Model training complete.")

# --- 6. Evaluate Model ---
y_pred = model.predict(X_test)

r2 = r2_score(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)

print("\n--- Model Evaluation ---")
print(f"R-squared (R2): {r2:.4f}")
print(f"Mean Absolute Error (MAE): {mae:.4f} positions")

print("\n--- Feature Importances ---")
importance_df = pd.DataFrame({
    'feature': features,
    'importance': model.feature_importances_
}).sort_values(by='importance', ascending=False)
print(importance_df)

# --- 7. Save Model (Encoders NO LONGER NEEDED) ---
model_filename = 'f1_prediction_model.joblib'
joblib.dump(model, model_filename)

# We don't save encoders anymore
# encoders_filename = 'f1_encoders.joblib'
# joblib.dump({'driver_encoder': driver_encoder, 'constructor_encoder': constructor_encoder}, encoders_filename)

print(f"\nModel saved to {model_filename}")
print("Encoders are no longer used.")
print("\n--- Model training script finished ---")
print("Next step: Update `api.py` to use these new features!")