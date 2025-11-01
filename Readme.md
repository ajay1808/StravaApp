# Strava Activity Dashboard

A powerful analytics dashboard for your Strava activities, built with Streamlit and Python. Track your fitness progress with advanced metrics and interactive visualizations.

## 📱 Available Apps

This project includes two versions of the Strava dashboard:

1. **Basic Version** (`appv1.py`): A simple table view of your recent activities
2. **Dashboard Version** (`dashboard.py`): An enhanced version with:
   - Key performance indicators (KPIs)
   - Activity summary statistics
   - Visual charts showing activity distribution
   - Detailed activity log in table format

## 🚀 How to Run This Project

Follow these steps in order to get the project running on your local machine.

### 1. Clone the Repository

Clone this project to your local machine:
```
git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
cd YOUR_REPO_NAME
```
(Replace YOUR_USERNAME/YOUR_REPO_NAME with your actual GitHub repo URL)

### 2. Create a Virtual Environment

It's highly recommended to use a virtual environment to keep dependencies separate.

```
# Create a venv
python3 -m venv venv

# Activate it (on Mac/Linux)
source venv/bin/activate
# (on Windows, use: venv\Scripts\activate)
```

### 3. Install Requirements

Install all the necessary libraries from the requirements.txt file:

```
pip install -r requirements.txt
```

### 4. Get Your Strava Access Token

This is the most important part. The app needs an access token to talk to the Strava API. The token you get from this process expires every 6 hours, so you will need to repeat these steps when the app stops working.

#### Step 4a: Get Your Authorization Code

Go to your Strava API settings: https://www.strava.com/settings/api

Find your Client ID number.

Paste this URL into your browser, replacing YOUR_CLIENT_ID with your own ID.

[http://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost&approval_prompt=force&scope=activity:read_all](http://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost&approval_prompt=force&scope=activity:read_all)


Click "Authorize". Your browser will show a ERR_CONNECTION_REFUSED error page. This is normal and expected.

Look at the URL in your browser's address bar. Copy the code value from it. It will look like this:
http://localhost/?state=&code=THIS_IS_THE_CODE_YOU_WANT&scope=...

#### Step 4b: Exchange the Code for a Token

Open your Terminal.

You will need your Client ID, Client Secret (from the Strava API page), and the Code you just copied.

Run the following curl command, replacing all the placeholders with your actual values:

```
curl -X POST [https://www.strava.com/oauth/token](https://www.strava.com/oauth/token) \
  -F client_id=YOUR_CLIENT_ID \
  -F client_secret=YOUR_CLIENT_SECRET \
  -F code=THE_CODE_YOU_COPIED \
  -F grant_type=authorization_code
```

#### Step 4c: Add Token to Secrets File

The terminal will print a JSON response. Copy the long access_token string from it.

Navigate to the .streamlit folder in this project.

Create a new file named secrets.toml.

Paste your token into the file like this:

STRAVA_ACCESS_TOKEN = "PASTE_YOUR_NEW_ACCESS_TOKEN_HERE"


### 5. Run the App!

You can run either version of the app using Streamlit:

For the basic version:
```
streamlit run appv1.py
```

For the enhanced dashboard:
```
streamlit run dashboard.py
```

## 📊 Dashboard Features

The enhanced dashboard (`dashboard.py`) provides the following features:

- **Key Stats**: Overview of your last 30 activities including:
  - Total number of activities
  - Total distance covered
  - Total elevation gained
  - Total time spent
- **Activity Log**: Detailed table with activity name, type, date, distance, time, and elevation
- **Visual Analytics**: Bar chart showing distance covered per activity type