# app.py
import streamlit as st
import requests
import pandas as pd

# 1. Load your secret access token
try:
    ACCESS_TOKEN = st.secrets["STRAVA_ACCESS_TOKEN"]
except FileNotFoundError:
    st.error("Missing secrets.toml file. Please create .streamlit/secrets.toml with your STRAVA_ACCESS_TOKEN.")
    st.stop()
except KeyError:
    st.error("STRAVA_ACCESS_TOKEN not found in secrets.toml. Please add it.")
    st.stop()

# 2. Define the Strava API endpoint and headers
ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities"
headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}

# 3. Add a button to fetch data
if st.button('Fetch My Strava Data'):
    st.write("Fetching data from Strava...")

    # 4. Make the API request
    # We'll just get the first page (30 activities) for this MVP
    params = {'page': 1, 'per_page': 30}
    response = requests.get(ACTIVITIES_URL, headers=headers, params=params)

    # 5. Check for a successful response
    if response.status_code == 200:
        st.success('Success! Data fetched.')
        data = response.json()
        
        # 6. Display the raw data as JSON
        st.subheader("Raw Activity Data (JSON)")
        st.json(data)
        
    else:
        st.error(f"Failed to fetch data from Strava. Status Code: {response.status_code}")
        st.json(response.json())

else:
    st.write("Click the button to get your Strava data.")