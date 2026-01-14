import uvicorn
import fastf1
import pandas as pd
import joblib  # Make sure joblib is imported
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import numpy as np # Import numpy for handling NaN

print("Starting Prediction API (v2 - Form Features)...")

# --- 1. Load Model ---
# We no longer load encoders, just the model
try:
    model = joblib.load('f1_prediction_model.joblib')
    print("Model loaded successfully.")
except FileNotFoundError:
    print("FATAL ERROR: `f1_prediction_model.joblib` not found.")
    print("Please run the new `train_model.py` (v2) first!")
    exit()

# --- 2. Setup FastAPI App ---
app = FastAPI(
    title="F1 Prediction API (v2)",
    description="API to predict F1 race results using 'recent form' features."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. Setup FastF1 Cache ---
CACHE_DIR = 'cache'
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)
fastf1.Cache.enable_cache(CACHE_DIR)
print("FastF1 cache enabled.")

# --- 4. API Endpoint ---
@app.get("/predict/last_race")
async def predict_last_race():
    print("Request received for /predict/last_race")
    try:
        # --- A. Get Schedule for Current Season ---
        print("Finding last completed race...")
        current_year = pd.Timestamp.now().year
        year_to_load = current_year
        
        schedule = fastf1.get_event_schedule(year_to_load, include_testing=False)
        
        # Find all races that have already happened
        races_completed_this_year = schedule[schedule['EventDate'] < pd.to_datetime('now')]
        
        if races_completed_this_year.empty:
            # It's the start of the season, get last race of last year
            print("No races completed this year. Getting last race of previous season.")
            year_to_load = current_year - 1
            schedule = fastf1.get_event_schedule(year_to_load, include_testing=False)
            last_race = schedule.iloc[-1]
            # No 'form' data to calculate yet, so we'll pass zeros
            all_season_results = pd.DataFrame()
        else:
            # Get the most recent race from the completed list
            last_race = races_completed_this_year.iloc[-1]
            print(f"Last race is {last_race['EventName']}. Loading all *other* completed races this year to calculate form...")
            
            # --- B. Calculate 'Recent Form' from Current Season ---
            # We need to get the results for ALL completed races *before* this one to calculate form
            
            # Get round numbers for all races *except* the one we are predicting
            rounds_to_load = races_completed_this_year[
                races_completed_this_year['RoundNumber'] < last_race['RoundNumber']
            ]['RoundNumber']

            season_results_list = []
            if not rounds_to_load.empty:
                for round_num in rounds_to_load:
                    try:
                        temp_session = fastf1.get_session(year_to_load, round_num, 'R')
                        temp_session.load(weather=False, telemetry=False, messages=False)
                        
                        if temp_session.results is not None:
                            # *** THIS IS THE FIX ***
                            # We must add the RoundNumber to the results DataFrame
                            results = temp_session.results
                            results['RoundNumber'] = round_num
                            season_results_list.append(results)
                            # *** END OF FIX ***
                            
                        print(f"Loaded form data for Round {round_num}")
                    except Exception as e:
                        print(f"Could not load form data for Round {round_num}: {e}")

            if season_results_list:
                all_season_results = pd.concat(season_results_list).sort_values(by='RoundNumber')
                all_season_results['Points'] = pd.to_numeric(all_season_results['Points'], errors='coerce')
            else:
                all_season_results = pd.DataFrame() # No prior races, form will be 0

        print(f"Loading data for prediction target: {year_to_load} {last_race['EventName']}")
        
        # Load the *actual* session we want to predict
        session = fastf1.get_session(year_to_load, last_race['RoundNumber'], 'R')
        session.load(weather=True, telemetry=False, messages=False)

        if session.results is None or session.results.empty:
            return {"error": "Could not load results for the last race."}
        
        # --- C. Prepare Data for Prediction ---
        race_data = session.results
        weather = session.weather_data.iloc[0]
        
        # This will hold the "form" data
        form_data = pd.DataFrame()

        if not all_season_results.empty:
            # Calculate form based on the races we just loaded
            driver_form_series = all_season_results.groupby('Abbreviation')['Points'].rolling(window=5, min_periods=1).mean()
            driver_form_series = driver_form_series.reset_index().groupby('Abbreviation').last()['Points']
            
            constructor_form_series = all_season_results.groupby('TeamName')['Points'].rolling(window=5, min_periods=1).mean()
            constructor_form_series = constructor_form_series.reset_index().groupby('TeamName').last()['Points']

            form_data['driver_form'] = race_data['Abbreviation'].map(driver_form_series).fillna(0)
            form_data['constructor_form'] = race_data['TeamName'].map(constructor_form_series).fillna(0)
        else:
            # No prior races, so everyone's form is 0
            print("No prior races this season. Setting all form features to 0.")
            form_data['driver_form'] = 0
            form_data['constructor_form'] = 0

        # Create the final feature DataFrame for the model
        df_predict = pd.DataFrame()
        df_predict['GridPosition'] = pd.to_numeric(race_data['GridPosition'], errors='coerce')
        df_predict['GridPosition'] = df_predict['GridPosition'].replace(0.0, 20.0).fillna(20.0) # Handle pit lane/missing
        
        df_predict = pd.concat([df_predict, form_data], axis=1) # Add the form features
        
        df_predict['AirTemp'] = weather['AirTemp']
        df_predict['TrackTemp'] = weather['TrackTemp']
        df_predict['Humidity'] = weather['Humidity']
        df_predict['Rainfall'] = 1 if weather['Rainfall'] == True else 0

        print(f"Prepared data for {len(df_predict)} drivers.")

        # --- D. Run Prediction ---
        features = [
            'GridPosition',
            'driver_form',
            'constructor_form',
            'AirTemp',
            'TrackTemp',
            'Humidity',
            'Rainfall'
        ]
        
        X_pred = df_predict[features]
        predictions = model.predict(X_pred)
        
        race_data['PredictedPosition'] = predictions
        
        # --- E. Format and Return Results ---
        # Add actual finishing position for comparison
        race_data['ActualPosition'] = pd.to_numeric(race_data['Position'], errors='coerce')

        print("Prediction complete.")
        
        # Sort by predicted position
        race_data['PredictedRank'] = race_data['PredictedPosition'].rank(method='first').astype(int)
        df_predict_sorted = race_data.sort_values(by='PredictedRank')
        
        # Select columns to return
        output_cols = [
            'PredictedRank',
            'Abbreviation',
            'FullName', # Use FullName from results
            'TeamName',
            'GridPosition',
            'ActualPosition'
        ]
        
        # Clean up for JSON
        # Replace NaN with None (which becomes null in JSON)
        df_final_output = df_predict_sorted[output_cols].copy()
        df_final_output['ActualPosition'] = df_final_output['ActualPosition'].apply(lambda x: None if pd.isna(x) else int(x))
        df_final_output['GridPosition'] = df_final_output['GridPosition'].apply(lambda x: None if pd.isna(x) else int(x))
        df_final_output['FullName'] = df_final_output['FullName'].fillna('N/A')

        results_json = df_final_output.to_dict(orient='records')
        
        return {
            "race_name": f"{year_to_load} {last_race['EventName']}",
            "predictions": results_json
        }

    except Exception as e:
        print(f"An error occurred in /predict/last_race: {e}")
        import traceback
        traceback.print_exc() # Print full error stack
        return {"error": str(e)}

# --- 5. Run the API ---
if __name__ == "__main__":
    print("Starting Uvicorn server at http://127.0.0.1:8000")
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)