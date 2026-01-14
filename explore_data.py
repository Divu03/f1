import fastf1
import pandas as pd
import os

# Set up pandas to show more columns
pd.set_option('display.max_columns', None)

# Define the cache directory
CACHE_DIR = 'cache'

# Check if the cache directory exists, and create it if it doesn't
if not os.path.exists(CACHE_DIR):
    try:
        os.makedirs(CACHE_DIR)
        print(f"Cache directory '{CACHE_DIR}' created.")
    except Exception as e:
        print(f"Error creating cache directory: {e}")
        pass

# Enable the FastF1 cache
# This is SUPER important. It will save data locally so you
# don't have to re-download it every time.
# Make sure to create a folder named 'cache' in your project directory
# or change this path to wherever you want to store the cache.
try:
    fastf1.Cache.enable_cache(CACHE_DIR)
    print(f"FastF1 cache enabled at: ./{CACHE_DIR}")
except Exception as e:
    print(f"Could not enable cache: {e}. Check folder permissions.")

# This is our "sandbox" script to see what data looks like for one race.
print("--- Loading data for a single race (2023 Monza GP) ---")

try:
    # Get the session data (Year, Race Name, Session Type 'R' for Race)
    session = fastf1.get_session(2023, 'Monza', 'R')

    # Load the data
    # This is the part that downloads the data if it's not in the cache.
    # We specify we need 'weather' data. 'results' comes with `load()`.
    session.load(weather=True)

    print(f"Successfully loaded session data for {session.event['EventName']}")

    # --- 1. Explore Race Results ---
    # `session.results` gives you the final classification.
    # This is our main target (what we want to predict).
    results = session.results
    
    print("\n--- Race Results (Top 5) ---")
    # Show relevant columns for the top 5 drivers
    # FIX: Changed 'Driver' to 'Abbreviation' and 'Constructor' to 'TeamName'
    print(results[['Position', 'Abbreviation', 'TeamName', 'GridPosition', 'Status']].head(5))
    
    # Let's look at one driver's full result data
    print("\n--- Full data for one driver ---")
    # FIX: Changed 'Driver' to 'Abbreviation'
    print(results.loc[results['Abbreviation'] == 'VER'])


    # --- 2. Explore Weather Data ---
    # `session.weather_data` gives you minute-by-minute weather.
    weather_data = session.weather_data
    
    print("\n--- Weather Data (First 5 minutes) ---")
    print(weather_data.head(5))

    # For our model, we probably just need the weather at the start of the race.
    race_start_weather = weather_data.iloc[0] # Get the first row
    print("\n--- Weather at Race Start ---")
    print(f"Air Temp: {race_start_weather['AirTemp']} C")
    print(f"Track Temp: {race_start_weather['TrackTemp']} C")
    print(f"Rainfall: {race_start_weather['Rainfall']}")
    print(f"Humidity: {race_start_weather['Humidity']} %")


except Exception as e:
    print(f"\nAn error occurred: {e}")
    print("Please make sure you have a 'cache' folder in your project directory.")

print("\n--- Exploration complete ---")
print("Next steps:")
print("1. Run `build_dataset.py` to collect data for *many* races.")
print("2. Run `train_model.py` to build the prediction model.")