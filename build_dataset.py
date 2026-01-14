import fastf1
import pandas as pd
import time
import os

print("Starting F1 Dataset Builder...")
print("This script is resumable.")
print("It's downloading data for multiple F1 seasons. This may take a while.")

# --- 1. Setup Cache ---
CACHE_DIR = 'cache'
if not os.path.exists(CACHE_DIR):
    try:
        os.makedirs(CACHE_DIR)
        print(f"Cache directory '{CACHE_DIR}' created.")
    except Exception as e:
        print(f"Error creating cache directory: {e}")
        pass

try:
    fastf1.Cache.enable_cache(CACHE_DIR)
    print(f"FastF1 cache enabled at: ./{CACHE_DIR}")
except Exception as e:
    print(f"Could not enable cache: {e}. Make sure the 'cache' folder exists.")
    exit()

# --- 2. Setup Output File and Resume Logic ---
OUTPUT_FILE = 'f1_race_data_2018_2024.csv'
YEARS = [2018, 2019, 2020, 2021, 2022, 2023, 2024]
START_YEAR = YEARS[0]
START_ROUND = 1

# Check if the output file already exists to resume
if os.path.exists(OUTPUT_FILE):
    try:
        print(f"Found existing data file: {OUTPUT_FILE}")
        df_existing = pd.read_csv(OUTPUT_FILE)
        
        if not df_existing.empty:
            # Find the last successfully processed race
            last_entry = df_existing.iloc[-1]
            last_year = int(last_entry['Year'])
            last_round = int(last_entry['RoundNumber'])
            
            print(f"Last saved race: {last_year}, Round {last_round}")
            
            # Get schedule to see if it was the last race of the season
            schedule_last_year = fastf1.get_event_schedule(last_year)
            races_last_year = schedule_last_year[schedule_last_year['EventFormat'] != 'testing']
            
            if last_round == races_last_year['RoundNumber'].max():
                # It was the last race, start from the next year
                START_YEAR = last_year + 1
                START_ROUND = 1
                print(f"Resuming from {START_YEAR}, Round {START_ROUND}")
            else:
                # Start from the next round in the same year
                START_YEAR = last_year
                START_ROUND = last_round + 1
                print(f"Resuming from {START_YEAR}, Round {START_ROUND}")
        else:
             print("Data file is empty. Starting from scratch.")
             
    except Exception as e:
        print(f"Error reading {OUTPUT_FILE}: {e}. Starting from scratch.")
        START_YEAR = YEARS[0]
        START_ROUND = 1
else:
    print(f"No data file found. Creating {OUTPUT_FILE} and starting from scratch.")
    # Create an empty file with headers to make it appendable
    # We need to know the columns. We'll get them by loading one session first.
    pass # We will handle header writing on the first loop


# --- 3. Main Data Collection Loop ---
print(f"Collecting data for seasons: {YEARS}")

for year in YEARS:
    if year < START_YEAR:
        print(f"\n--- Skipping Year {year} (already processed) ---")
        continue
        
    print(f"\n--- Processing Year: {year} ---")
    
    # Get the event schedule for the year
    schedule = fastf1.get_event_schedule(year)
    
    # Filter out testing events
    races = schedule[schedule['EventFormat'] != 'testing']
    
    # Loop through each race event
    for _, event in races.iterrows():
        event_name = event['EventName']
        round_number = event['RoundNumber']
        
        if year == START_YEAR and round_number < START_ROUND:
            print(f"Skipping: {year} {event_name} (Round {round_number}) (already processed)")
            continue
        
        print(f"Processing: {year} {event_name} (Round {round_number})")
        
        try:
            # Get the race session
            session = fastf1.get_session(year, round_number, 'R')
            
            # Load the session data (results and weather)
            session.load(weather=True, telemetry=False, messages=False)
            
            # Check if we got results
            if session.results is None or session.results.empty:
                print(f"No results found for {year} {event_name}. Skipping.")
                continue
                
            # Get race results
            results = session.results
            
            # Get weather data (we'll take the weather at the start of the race)
            weather = session.weather_data.iloc[0] # First row
            
            # Add weather data and identifiers to each driver's result
            results['Year'] = year
            results['RaceName'] = event_name
            results['RoundNumber'] = round_number
            results['AirTemp'] = weather['AirTemp']
            results['TrackTemp'] = weather['TrackTemp']
            results['Humidity'] = weather['Humidity']
            results['Rainfall'] = weather['Rainfall']
            
            # --- Append data to CSV ---
            # Check if file exists to decide whether to write headers
            file_exists = os.path.exists(OUTPUT_FILE)
            
            results.to_csv(OUTPUT_FILE, mode='a', header=not file_exists, index=False)
            
            print(f"Successfully processed and saved {year} {event_name}")
            
        except Exception as e:
            print(f"!! ERROR loading session for {year} {event_name}: {e}")
            print("This might be a cancelled session or a data loading issue. Skipping.")
        
        # Be nice to the API
        time.sleep(1) # Wait 1 second between API calls

print("\n--- Data collection complete ---")

try:
    final_dataset = pd.read_csv(OUTPUT_FILE)
    print(f"Total rows collected in {OUTPUT_FILE}: {len(final_dataset)}")
    # De-duplicate, just in case
    final_dataset.drop_duplicates(subset=['Year', 'RoundNumber', 'Abbreviation'], inplace=True)
    final_dataset.to_csv(OUTPUT_FILE, index=False)
    print(f"De-duplicated. Final row count: {len(final_dataset)}")
except Exception as e:
    print(f"Could not read final dataset for a count: {e}")


print("\nNext step: Run `train_model.py` to build the model!")