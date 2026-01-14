import uvicorn
import fastf1
import pandas as pd
import joblib
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import numpy as np

print("Starting Prediction & Insights API...")

# --- 1. Load Model (For Predictions) ---
try:
    model = joblib.load('f1_prediction_model.joblib')
    print("Prediction Model loaded.")
except FileNotFoundError:
    print("Warning: Prediction model not found. /predict endpoint will fail.")

# --- 2. Load Historical Data (For Insights) ---
# We load the CSV into memory once when the API starts
HISTORICAL_DATA_FILE = 'f1_race_data_2018_2024.csv'
historical_df = pd.DataFrame()
try:
    historical_df = pd.read_csv(HISTORICAL_DATA_FILE)
    # Basic cleaning
    historical_df['Position'] = pd.to_numeric(historical_df['Position'], errors='coerce')
    historical_df['GridPosition'] = pd.to_numeric(historical_df['GridPosition'], errors='coerce')
    historical_df['Points'] = pd.to_numeric(historical_df['Points'], errors='coerce')
    print(f"Historical data loaded: {len(historical_df)} rows.")
except FileNotFoundError:
    print(f"Warning: {HISTORICAL_DATA_FILE} not found. /insights endpoint will fail.")

# --- 3. Setup FastAPI App ---
app = FastAPI(title="F1 API", description="Predictions and Historical Insights")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 4. Setup Cache ---
CACHE_DIR = 'cache'
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)
fastf1.Cache.enable_cache(CACHE_DIR)

# ==========================================
# ENDPOINT 1: PREDICTION (Existing Logic)
# ==========================================
@app.get("/predict/last_race")
async def predict_last_race():
    # ... (Same prediction logic as before) ...
    # For brevity in this display, I am including the full logic below
    # so you can copy-paste the whole file safely.
    try:
        current_year = pd.Timestamp.now().year
        year_to_load = current_year
        schedule = fastf1.get_event_schedule(year_to_load, include_testing=False)
        races_completed = schedule[schedule['EventDate'] < pd.to_datetime('now')]
        
        if races_completed.empty:
            year_to_load = current_year - 1
            schedule = fastf1.get_event_schedule(year_to_load, include_testing=False)
            last_race = schedule.iloc[-1]
            all_season_results = pd.DataFrame()
        else:
            last_race = races_completed.iloc[-1]
            rounds_to_load = races_completed[races_completed['RoundNumber'] < last_race['RoundNumber']]['RoundNumber']
            season_results_list = []
            for round_num in rounds_to_load:
                try:
                    s = fastf1.get_session(year_to_load, round_num, 'R')
                    s.load(weather=False, telemetry=False, messages=False)
                    if s.results is not None:
                        res = s.results
                        res['RoundNumber'] = round_num
                        season_results_list.append(res)
                except: pass
            
            if season_results_list:
                all_season_results = pd.concat(season_results_list).sort_values(by='RoundNumber')
                all_season_results['Points'] = pd.to_numeric(all_season_results['Points'], errors='coerce')
            else:
                all_season_results = pd.DataFrame()

        session = fastf1.get_session(year_to_load, last_race['RoundNumber'], 'R')
        session.load(weather=True, telemetry=False, messages=False)
        
        if session.results is None: return {"error": "No results found"}

        race_data = session.results
        weather = session.weather_data.iloc[0]
        
        # Form Calculation
        form_data = pd.DataFrame()
        if not all_season_results.empty:
            d_form = all_season_results.groupby('Abbreviation')['Points'].rolling(5, min_periods=1).mean()
            d_form = d_form.reset_index().groupby('Abbreviation').last()['Points']
            c_form = all_season_results.groupby('TeamName')['Points'].rolling(5, min_periods=1).mean()
            c_form = c_form.reset_index().groupby('TeamName').last()['Points']
            form_data['driver_form'] = race_data['Abbreviation'].map(d_form).fillna(0)
            form_data['constructor_form'] = race_data['TeamName'].map(c_form).fillna(0)
        else:
            form_data['driver_form'] = 0
            form_data['constructor_form'] = 0

        df_p = pd.DataFrame()
        df_p['GridPosition'] = pd.to_numeric(race_data['GridPosition'], errors='coerce').replace(0, 20).fillna(20)
        df_p = pd.concat([df_p, form_data], axis=1)
        df_p['AirTemp'] = weather['AirTemp']
        df_p['TrackTemp'] = weather['TrackTemp']
        df_p['Humidity'] = weather['Humidity']
        df_p['Rainfall'] = 1 if weather['Rainfall'] else 0

        features = ['GridPosition', 'driver_form', 'constructor_form', 'AirTemp', 'TrackTemp', 'Humidity', 'Rainfall']
        race_data['PredictedPosition'] = model.predict(df_p[features])
        race_data['ActualPosition'] = pd.to_numeric(race_data['Position'], errors='coerce')
        
        race_data['PredictedRank'] = race_data['PredictedPosition'].rank(method='first').astype(int)
        output = race_data.sort_values(by='PredictedRank')[['PredictedRank', 'Abbreviation', 'FullName', 'TeamName', 'GridPosition', 'ActualPosition']]
        
        # Clean JSON
        output = output.where(pd.notnull(output), None)
        return {"race_name": f"{year_to_load} {last_race['EventName']}", "predictions": output.to_dict(orient='records')}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

# ==========================================
# ENDPOINT 2: HISTORICAL INSIGHTS (New)
# ==========================================
@app.get("/insights/{year}")
async def get_year_insights(year: int):
    if historical_df.empty:
        raise HTTPException(status_code=500, detail="Historical data not loaded.")
    
    # Filter for the requested year
    df_year = historical_df[historical_df['Year'] == year].copy()
    
    if df_year.empty:
        raise HTTPException(status_code=404, detail=f"No data found for {year}")

    # 1. Champion (Most Points)
    driver_points = df_year.groupby(['Abbreviation', 'TeamName'])['Points'].sum().sort_values(ascending=False)
    champion = driver_points.index[0][0]
    champion_points = int(driver_points.iloc[0])
    champion_team = driver_points.index[0][1]

    # 2. Constructor Champion
    team_points = df_year.groupby('TeamName')['Points'].sum().sort_values(ascending=False)
    top_team = team_points.index[0]
    top_team_points = int(team_points.iloc[0])

    # 3. Pole to Win Ratio
    winners = df_year[df_year['Position'] == 1]
    wins_from_pole = len(winners[winners['GridPosition'] == 1])
    total_races = len(winners)
    pole_win_pct = round((wins_from_pole / total_races) * 100, 1) if total_races > 0 else 0

    # 4. Rainy Races count
    # Assuming 'Rainfall' is boolean or 1/0
    rainy_races = df_year[df_year['Rainfall'] > 0]['RaceName'].nunique()

    return {
        "year": year,
        "champion": {
            "name": champion,
            "team": champion_team,
            "points": champion_points
        },
        "constructor": {
            "name": top_team,
            "points": top_team_points
        },
        "stats": {
            "pole_win_percentage": pole_win_pct,
            "total_races": total_races,
            "rainy_races": rainy_races
        }
    }

if __name__ == "__main__":
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)