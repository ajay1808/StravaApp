import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import altair as alt

# Page config
st.set_page_config(page_title="Advanced Strava Dashboard", layout="wide")

# Custom CSS for better styling
st.markdown("""
    <style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
        box-shadow:         st.dataframe(
            activity_log.sort_values('start_date', ascending=False),
            use_container_width=True)  # TODO: Update to width='stretch' when Streamlit is updated 2px 5px rgba(0,0,0,0.1);
    }
    .record-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 10px 0;
        color: black;
    }
    .record-card h6 {
        color: black;
        margin-bottom: 8px;
        font-weight: 600;
    }
    .record-card p {
        color: black;
        margin: 4px 0;
    }
    .record-card small {
        color: #555;
        display: block;
        margin: 4px 0;
    }
    /* Force black text color for all metric components */
    [data-testid="stMetricValue"], 
    [data-testid="stMetricValue"] > div, 
    [data-testid="stMetricValue"] > div > div {
        color: rgb(0, 0, 0) !important;
    }
    [data-testid="stMetricDelta"],
    [data-testid="stMetricDelta"] > div,
    [data-testid="stMetricDelta"] > div > div {
        color: rgb(0, 0, 0) !important;
    }
    [data-testid="stMetricLabel"],
    [data-testid="stMetricLabel"] > div,
    [data-testid="stMetricLabel"] > div > div {
        color: rgb(0, 0, 0) !important;
    }
    div[data-testid="stMarkdownContainer"] > p {
        color: rgb(0, 0, 0);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 5px;
        gap: 8px;
        padding: 10px;
    }
    .metric-explanation {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        border-left: 3px solid #4CAF50;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Load access token
try:
    ACCESS_TOKEN = st.secrets["STRAVA_ACCESS_TOKEN"]
except (FileNotFoundError, KeyError):
    st.error("Missing STRAVA_ACCESS_TOKEN in secrets.toml")
    st.stop()

# API Configuration
ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities"
headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_strava_data(per_page=200):
    """Fetch one year of activities from Strava."""
    all_activities = []
    page = 1
    
    while True:
        params = {'page': page, 'per_page': per_page}
        response = requests.get(ACTIVITIES_URL, headers=headers, params=params)
        
        if response.status_code != 200:
            st.error(f"Error fetching data: {response.status_code}")
            return pd.DataFrame()
            
        activities = response.json()
        if not activities:
            break
            
        all_activities.extend(activities)
        if len(activities) < per_page:
            break
            
        page += 1
    
    return pd.DataFrame(all_activities)

def filter_activities_by_date(df, days):
    """Filter activities within the last N days."""
    if df.empty:
        return df
    cutoff_date = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=days)
    return df[df['start_date'] > cutoff_date]

def calculate_hybrid_score(time, elevation, distance):
    """Calculate hybrid score based on distance, time, and elevation gain.
    
    Components are normalized and weighted based on their relative importance:
    - Distance: 40% (primary indicator of effort)
    - Duration: 35% (important but slightly less than distance)
    - Elevation: 25% (significant but not dominant)
    
    Each component is normalized to a 0-10 scale before applying weights.
    """
    # Convert to more manageable units
    distance_km = distance / 1000  # meters to km
    time_hours = time / 3600  # seconds to hours
    elevation_km = elevation / 1000  # meters to km
    
    # Normalize each component to a 0-10 scale
    # These base values represent "moderate" achievement levels
    BASE_DISTANCE = 10  # 10 km as base distance
    BASE_TIME = 1  # 1 hour as base time
    BASE_ELEVATION = 0.1  # 100m elevation as base
    
    # Calculate normalized scores (0-10 scale)
    distance_score = min(10, (distance_km / BASE_DISTANCE) * 10)
    time_score = min(10, (time_hours / BASE_TIME) * 10)
    elevation_score = min(10, (elevation_km / BASE_ELEVATION) * 10)
    
    # Apply weights
    weighted_score = (
        (distance_score * 0.40) +  # 40% weight for distance
        (time_score * 0.35) +      # 35% weight for time
        (elevation_score * 0.25)    # 25% weight for elevation
    )
    
    return weighted_score

def format_time(seconds):
    """Format seconds into HH:MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def format_distance(meters, unit_system='metric'):
    """Format distance in appropriate units."""
    if unit_system == 'metric':
        if meters >= 1000:
            return f"{meters/1000:.2f} km"
        else:
            return f"{meters:.0f} m"
    else:  # imperial
        miles = meters * 0.000621371
        if miles >= 0.1:
            return f"{miles:.2f} mi"
        else:
            feet = meters * 3.28084
            return f"{feet:.0f} ft"

def calculate_calories(activity_type, duration_seconds, distance_meters=0):
    """Calculate approximate calories burned based on activity type and duration."""
    # MET values from the Compendium of Physical Activities
    met_values = {
        'Run': 9.8,  # Running 6 mph (10 min/mile)
        'Ride': 8.0,  # Cycling 12-14 mph
        'Swim': 7.0,  # Swimming, moderate effort
        'Workout': 6.0,  # Calisthenics, moderate effort
        'Walk': 3.5,  # Walking 3.5 mph
        'Hike': 5.3,  # Hiking, cross country
        'Yoga': 2.5,  # Yoga, general
        'WeightTraining': 3.5,  # Weight training, light effort
    }
    
    # Default to moderate exercise if activity type not found
    met = met_values.get(activity_type, 5.0)
    
    # Assume average weight of 70kg if not provided
    weight_kg = 70
    
    # Calories = MET × Weight (kg) × Duration (hours)
    hours = duration_seconds / 3600
    calories = met * weight_kg * hours
    
    return round(calories)

# Load data
st.title("🏃‍♂️ Advanced Strava Dashboard 🚴‍♀️")
data = load_strava_data()

if data.empty:
    st.error("No data available")
    st.stop()

# Process data
data['start_date'] = pd.to_datetime(data['start_date'])
data['hybrid_score'] = data.apply(
    lambda x: calculate_hybrid_score(
        x['moving_time'], 
        x['total_elevation_gain'], 
        x['distance']
    ), 
    axis=1
)

# Sidebar configuration
st.sidebar.title("🎯 Dashboard Settings")

# Activity selection
available_activities = sorted(data['type'].unique())
selected_activity = st.sidebar.selectbox("Select Activity Type", available_activities)

# Unit system selection
unit_system = st.sidebar.radio("Unit System", ["Metric", "Imperial"], horizontal=True)
unit_system = unit_system.lower()

# Visualization type
viz_type = st.sidebar.radio("Chart Metric", ["Distance", "Hybrid Score"], horizontal=True)

# Hybrid Score Explanation
with st.sidebar.expander("ℹ️ What is Hybrid Score?"):
    st.markdown("""
    The Hybrid Score is a comprehensive metric that combines distance, duration, and elevation gain to measure overall activity intensity. Each component is normalized to a 0-10 scale and weighted based on its relative importance.

    **Components & Weights:**
    - 🏃‍♂️ Distance (40%): Primary indicator of effort
    - ⏱️ Duration (35%): Time investment in activity
    - 🏔️ Elevation (25%): Intensity factor from climbing
    
    **How it works:**
    1. Each component is normalized on a 0-10 scale:
        - Distance: 10km = 10 points
        - Duration: 1 hour = 10 points
        - Elevation: 100m = 10 points
    2. Weights are applied to balance the components
    3. Final score ranges from 0-10

    A higher score indicates a more challenging activity overall, considering all three factors.
    
    **Example:**
    - 10km run (10 pts)
    - 1 hour duration (10 pts)
    - 100m elevation (10 pts)
    Would score: (10×0.4) + (10×0.35) + (10×0.25) = 10
    """)

# Filter data by activity type
filtered_data = data[data['type'] == selected_activity]

# Determine if elevation is relevant for this activity type
elevation_relevant = selected_activity in ['Run', 'Ride', 'Hike']

# Time period tabs
time_periods = {
    "Last 7 Days": 7,
    "Last Month": 30,
    "Last 3 Months": 90,
    "Last Year": 365
}

tabs = st.tabs(list(time_periods.keys()))

for tab, (period_name, days) in zip(tabs, time_periods.items()):
    with tab:
        period_data = filter_activities_by_date(filtered_data, days)
        
        if period_data.empty:
            st.info(f"No {selected_activity} activities found in the {period_name.lower()}")
            continue

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Activities", len(period_data))
        with col2:
            total_distance = period_data['distance'].sum()
            st.metric("Total Distance", format_distance(total_distance, unit_system))
        with col3:
            if elevation_relevant:
                total_elevation = period_data['total_elevation_gain'].sum()
                elevation_label = "Total Elevation"
                elevation_value = f"{total_elevation:.0f} m" if unit_system == 'metric' else f"{total_elevation * 3.28084:.0f} ft"
            else:
                total_calories = period_data.apply(
                    lambda x: calculate_calories(selected_activity, x['moving_time'], x['distance']), 
                    axis=1
                ).sum()
                elevation_label = "Est. Calories"
                elevation_value = f"{total_calories:,.0f} kcal"
            st.metric(elevation_label, elevation_value)
        with col4:
            total_time = period_data['moving_time'].sum() / 3600
            st.metric("Total Time", f"{total_time:.1f} hrs")

        # Records section
        st.subheader("🏆 Records")
        
        # Time-based records
        time_record = period_data.nlargest(1, 'moving_time').iloc[0]
        distance_record = period_data.nlargest(1, 'distance').iloc[0]
        elevation_record = period_data.nlargest(1, 'total_elevation_gain').iloc[0]
        hybrid_record = period_data.nlargest(1, 'hybrid_score').iloc[0]

        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### ⏱️ Time Records")
            st.markdown(f"""
            <div class="record-card" style="background-color: #f0f2f6; color: black;">
                <h6 style="color: black; margin-bottom: 8px;">Longest Duration</h6>
                <p style="color: black; font-size: 20px; margin: 4px 0;">{format_time(time_record['moving_time'])}</p>
                <small style="color: #555;">{time_record['name']} on {time_record['start_date'].strftime('%Y-%m-%d')}</small>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("##### 🎯 Hybrid Score Records")
            st.markdown(f"""
            <div class="record-card" style="background-color: #f0f2f6; color: black;">
                <h6 style="color: black; margin-bottom: 8px;">Best Combined Performance</h6>
                <p style="color: black; font-size: 20px; margin: 4px 0;">Score: {hybrid_record['hybrid_score']:.2f}</p>
                <small style="color: #555;">{hybrid_record['name']} on {hybrid_record['start_date'].strftime('%Y-%m-%d')}</small>
                <p style="color: black; margin-top: 8px;">Time: {format_time(hybrid_record['moving_time'])} | Elevation: {hybrid_record['total_elevation_gain']:.0f}m</p>
            </div>
            """, unsafe_allow_html=True)

        # Interactive Charts
        st.subheader("📊 Activity Analysis")
        
        # Create time series chart
        chart_data = period_data.copy()
        chart_data['formatted_distance'] = chart_data['distance'].apply(lambda x: format_distance(x, unit_system))
        
        if viz_type == "Distance":
            y_field = 'distance'
            y_title = 'Distance (meters)' if unit_system == 'metric' else 'Distance (feet)'
            if unit_system == 'imperial':
                chart_data['distance'] = chart_data['distance'] * 3.28084  # convert to feet
            tooltip_fields = ['name', 'start_date', 'formatted_distance', 'moving_time']
        else:  # Hybrid Score
            y_field = 'hybrid_score'
            y_title = 'Hybrid Score'
            tooltip_fields = ['name', 'start_date', 'hybrid_score', 'moving_time']

        if elevation_relevant:
            tooltip_fields.append('total_elevation_gain')
        
        time_chart = alt.Chart(chart_data).mark_line(point=True).encode(
            x=alt.X('start_date:T', title='Date'),
            y=alt.Y(f'{y_field}:Q', 
                   title=y_title),
            tooltip=tooltip_fields
        ).properties(
            height=300,
            width='container'  # This makes the chart responsive
        ).interactive()

        st.altair_chart(time_chart, use_container_width=True)

        # Display detailed activity log
        st.subheader("📝 Activity Log")
        activity_log = period_data[[
            'name', 'start_date', 'distance', 'moving_time', 
            'total_elevation_gain', 'hybrid_score'
        ]].copy()
        
        # Format the columns
        activity_log['distance'] = activity_log['distance'].apply(format_distance)
        activity_log['moving_time'] = activity_log['moving_time'].apply(format_time)
        activity_log['total_elevation_gain'] = activity_log['total_elevation_gain'].apply(lambda x: f"{x:.0f} m")
        activity_log['hybrid_score'] = activity_log['hybrid_score'].apply(lambda x: f"{x:.2f}")
        
        st.dataframe(
            activity_log.sort_values('start_date', ascending=False),
            width='stretch'
        )
