import uvicorn
import fastf1
import pandas as pd
import joblib
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from typing import Optional

print("Starting Prediction & Insights API...")

# --- 1. Load Model ---
try:
    model = joblib.load('f1_prediction_model.joblib')
    print("Prediction Model loaded.")
except FileNotFoundError:
    print("Warning: Prediction model not found.")

# --- 2. Load Historical Data ---
HISTORICAL_DATA_FILE = 'f1_race_data_2018_2024.csv'
historical_df = pd.DataFrame()
try:
    historical_df = pd.read_csv(HISTORICAL_DATA_FILE)
    historical_df['Position'] = pd.to_numeric(historical_df['Position'], errors='coerce')
    historical_df['GridPosition'] = pd.to_numeric(historical_df['GridPosition'], errors='coerce')
    historical_df['Points'] = pd.to_numeric(historical_df['Points'], errors='coerce')
    print(f"Historical data loaded: {len(historical_df)} rows.")
except FileNotFoundError:
    print(f"Warning: {HISTORICAL_DATA_FILE} not found.")

app = FastAPI(title="F1 API", description="Enhanced Analytics Hub")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Cache ---
CACHE_DIR = 'cache'
if not os.path.exists(CACHE_DIR): os.makedirs(CACHE_DIR)
fastf1.Cache.enable_cache(CACHE_DIR)

@app.get("/schedule/{year}")
async def get_schedule(year: int):
    try:
        schedule = fastf1.get_event_schedule(year, include_testing=False)
        # Only return races that have an event date
        races = schedule[schedule['EventFormat'] != 'testing']
        result = []
        for _, row in races.iterrows():
            result.append({
                "round": int(row['RoundNumber']),
                "name": row['EventName'],
                "date": str(row['EventDate'])
            })
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/predict")
async def predict_race(year: Optional[int] = None, round_num: Optional[int] = None):
    try:
        current_year = pd.Timestamp.now().year
        
        # Determine which race to load
        if year is None or round_num is None:
            # Default to last completed race logic
            year_to_load = current_year
            schedule = fastf1.get_event_schedule(year_to_load, include_testing=False)
            races_completed = schedule[schedule['EventDate'] < pd.to_datetime('now')]
            
            if races_completed.empty:
                year_to_load = current_year - 1
                schedule = fastf1.get_event_schedule(year_to_load, include_testing=False)
                last_race = schedule.iloc[-1]
            else:
                last_race = races_completed.iloc[-1]
            
            round_to_load = int(last_race['RoundNumber'])
        else:
            year_to_load = year
            round_to_load = round_num
            schedule = fastf1.get_event_schedule(year_to_load, include_testing=False)
            selected_event = schedule[schedule['RoundNumber'] == round_to_load].iloc[0]
            last_race = selected_event

        # Load season context for Form calculation
        # We load all races in THAT specific year prior to the target round
        full_schedule = fastf1.get_event_schedule(year_to_load, include_testing=False)
        prior_rounds = full_schedule[full_schedule['RoundNumber'] < round_to_load]['RoundNumber']
        
        season_results_list = []
        for r in prior_rounds:
            try:
                s = fastf1.get_session(year_to_load, r, 'R')
                s.load(weather=False, telemetry=False, messages=False)
                if s.results is not None:
                    res = s.results.copy()
                    res['RoundNumber'] = r
                    season_results_list.append(res)
            except: pass
        
        all_season_results = pd.concat(season_results_list) if season_results_list else pd.DataFrame()

        # Load Target Session
        session = fastf1.get_session(year_to_load, round_to_load, 'R')
        session.load(weather=True, telemetry=False, messages=False)
        
        race_data = session.results
        weather = session.weather_data.iloc[0]
        
        form_data = pd.DataFrame()
        if not all_season_results.empty:
            all_season_results['Points'] = pd.to_numeric(all_season_results['Points'], errors='coerce')
            d_form = all_season_results.groupby('Abbreviation')['Points'].rolling(5, min_periods=1).mean().reset_index().groupby('Abbreviation').last()['Points']
            c_form = all_season_results.groupby('TeamName')['Points'].rolling(5, min_periods=1).mean().reset_index().groupby('TeamName').last()['Points']
            form_data['driver_form'] = race_data['Abbreviation'].map(d_form).fillna(0)
            form_data['constructor_form'] = race_data['TeamName'].map(c_form).fillna(0)
        else:
            form_data['driver_form'] = 0
            form_data['constructor_form'] = 0

        df_p = pd.DataFrame()
        df_p['GridPosition'] = pd.to_numeric(race_data['GridPosition'], errors='coerce').replace(0, 20).fillna(20)
        df_p = pd.concat([df_p, form_data], axis=1)
        df_p['AirTemp'], df_p['TrackTemp'], df_p['Humidity'] = weather['AirTemp'], weather['TrackTemp'], weather['Humidity']
        df_p['Rainfall'] = 1 if weather['Rainfall'] else 0

        features = ['GridPosition', 'driver_form', 'constructor_form', 'AirTemp', 'TrackTemp', 'Humidity', 'Rainfall']
        race_data['PredictedPosition'] = model.predict(df_p[features])
        race_data['ActualPosition'] = pd.to_numeric(race_data['Position'], errors='coerce')
        race_data['PredictedRank'] = race_data['PredictedPosition'].rank(method='first').astype(int)
        
        output = race_data.sort_values(by='PredictedRank')[['PredictedRank', 'Abbreviation', 'FullName', 'TeamName', 'GridPosition', 'ActualPosition']]
        output = output.where(pd.notnull(output), None)
        return {"race_name": f"{year_to_load} {last_race['EventName']}", "predictions": output.to_dict(orient='records')}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@app.get("/insights/{year}")
async def get_year_insights(year: int):
    if historical_df.empty: raise HTTPException(status_code=500, detail="No data")
    df_year = historical_df[historical_df['Year'] == year].copy()
    if df_year.empty: raise HTTPException(status_code=404, detail="No data for year")

    pts = df_year.groupby(['Abbreviation', 'TeamName'])['Points'].sum().sort_values(ascending=False)
    champ, champ_team = pts.index[0]
    c_pts = df_year.groupby('TeamName')['Points'].sum().sort_values(ascending=False)
    winners = df_year[df_year['Position'] == 1]
    pole_win_pct = round((len(winners[winners['GridPosition'] == 1]) / len(winners)) * 100, 1) if len(winners) > 0 else 0
    total_entries = len(df_year)
    dnfs = df_year['Position'].isna().sum()
    dnf_rate = round((dnfs / total_entries) * 100, 1)
    finishers = df_year.dropna(subset=['Position'])
    finishers['gained'] = finishers['GridPosition'] - finishers['Position']
    overtake_pts = finishers.groupby('Abbreviation')['gained'].sum().sort_values(ascending=False)
    overtake_king = overtake_pts.index[0]
    total_gained = int(overtake_pts.iloc[0])
    top_10s = df_year[df_year['Position'] <= 10].groupby('Abbreviation').size().sort_values(ascending=False)
    consistent_driver = top_10s.index[0]
    consistent_count = int(top_10s.iloc[0])
    avg_temp = round(df_year['TrackTemp'].mean(), 1)

    return {
        "year": year,
        "champion": {"name": champ, "team": champ_team, "points": int(pts.iloc[0]), "detail": f"{champ} dominated with {len(df_year[(df_year['Abbreviation']==champ) & (df_year['Position']==1)])} wins."},
        "constructor": {"name": c_pts.index[0], "points": int(c_pts.iloc[0]), "detail": f"{c_pts.index[0]} outperformed {c_pts.index[1]} by {int(c_pts.iloc[0] - c_pts.iloc[1])} points."},
        "pole_rate": {"value": pole_win_pct, "detail": f"In {year}, starting on Pole was {'crucial' if pole_win_pct > 50 else 'less vital'} as {pole_win_pct}% of poles converted to wins."},
        "reliability": {"value": dnf_rate, "detail": f"The field saw {dnfs} total retirements. Reliability was a major factor in the championship battle."},
        "overtake": {"driver": overtake_king, "value": total_gained, "detail": f"{overtake_king} gained a total of {total_gained} positions from their starting slots across the season."},
        "consistency": {"driver": consistent_driver, "value": consistent_count, "detail": f"{consistent_driver} finished in the points {consistent_count} times, showing incredible season-long stability."},
        "weather": {"avg_temp": avg_temp, "rainy": int(df_year[df_year['Rainfall'] > 0]['RaceName'].nunique()), "detail": f"Average track temperature was {avg_temp}°C. There were {int(df_year[df_year['Rainfall'] > 0]['RaceName'].nunique())} sessions with recorded rainfall."},
    }

if __name__ == "__main__":
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)