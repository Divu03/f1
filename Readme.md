🏎️ F1 Prediction Engine & Performance Analysis

This project combines a Machine Learning model to predict Formula 1 race results with an interactive Data Analysis Dashboard to explore historical performance trends.

It leverages FastF1 for deep telemetry and race data, Scikit-learn for predictive modeling, and Streamlit for visual analysis.

🛠️ Tech Stack & Tools

Language: Python 3.9+

Data Source: FastF1 (Open-source bridge to F1 data)

Data Processing: Pandas, NumPy

Machine Learning: Scikit-learn (Random Forest Regressor)

Backend API: FastAPI, Uvicorn

Visualization: Streamlit, Plotly, Seaborn

Frontend (Prediction): HTML5, TailwindCSS

🚀 Installation

Clone the repository:

git clone [https://github.com/your-username/f1-prediction-project.git](https://github.com/your-username/f1-prediction-project.git)
cd f1-prediction-project



Install dependencies:

pip install -r requirements.txt



🚦 Usage Guide

This project consists of two main parts: the Prediction Engine and the Analysis Dashboard.

Step 1: Data Collection (The Foundation)

Before running anything, you need to build the historical dataset. This script downloads race results and weather data from 2018 to present.

python build_dataset.py



Note: This process takes time as it caches data locally to avoid repeated downloads.

Output: f1_race_data_2018_2024.csv

Step 2: Analysis Dashboard (The Pivot)

Launch the interactive dashboard to explore factors like Grid Position, Team Dominance, and Weather Impact.

streamlit run analysis_app.py



Opens automatically in your browser (usually http://localhost:8501).

Step 3: Machine Learning Prediction (Optional)

If you want to run the predictive model:

Train the Model:
Calculates "Recent Form" features and trains a Random Forest model.

python train_model.py



Output: f1_prediction_model.joblib

Start the API Server:
Hosted using FastAPI to serve real-time predictions.

uvicorn api:app --reload



Use the Frontend:
Open the index.html file in your browser to interact with the API.

📂 Project Structure

build_dataset.py: Scrapes and compiles the master CSV dataset.

analysis_app.py: Streamlit Dashboard source code.

train_model.py: Feature engineering (calculating form) and Model Training.

api.py: FastAPI server that loads the model and predicts the latest race.

index.html: User interface for the prediction engine.

cache/: Stores raw FastF1 data (Git-ignored).

📊 Model Insights: Feature Importance

The Machine Learning model (Random Forest Regressor) ranks the "features" (inputs) based on how much they contribute to predicting the final finishing position. Based on training data from 2018-2024, here is the approximate breakdown of importance:

Grid Position (~55-60%): By far the most critical factor. Where a driver qualifies is the single best predictor of where they finish.

Constructor Form (~15-20%): The performance of the car team in the last 5 races. This captures the mechanical advantage (e.g., Red Bull vs. Haas).

Driver Form (~10-15%): The driver's personal average points in the last 5 races. This helps distinguish teammates (e.g., Verstappen vs. Perez).

Weather (Temp/Rain) (<5%): While rain causes chaos, it is statistically rare. In the global model, weather has a lower overall weight, though it causes high variance when it does happen.

Why this matters: The model confirms that F1 is largely an engineering championship (Car + Grid Position), but "Form" features allow it to adapt to mid-season upgrades or driver slumps.

💡 Code Highlights

Feature Engineering: "Recent Form"

Instead of relying on static driver IDs, the model calculates dynamic "form" based on the rolling average of points scored in the last 5 races. This allows the model to handle rookies and mid-season team changes effectively.

# Calculating rolling average points for drivers
df['driver_form'] = df.groupby('Abbreviation')['Points'].transform(
    lambda x: x.shift(1).rolling(window=5, min_periods=1).mean()
).fillna(0)

# Calculating rolling average points for constructors
df['constructor_form'] = df.groupby('TeamName')['Points'].transform(
    lambda x: x.shift(1).rolling(window=5, min_periods=1).mean()
).fillna(0)



Prediction Logic

The API calculates the current form for the active season on-the-fly before asking the model for a prediction.

# From api.py
features = [
    'GridPosition',      # Where they start
    'driver_form',       # How they've been driving lately
    'constructor_form',  # How good the car is lately
    'AirTemp',           # Weather conditions
    'Rainfall'           # Wet or Dry
]

