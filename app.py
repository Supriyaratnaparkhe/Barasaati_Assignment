import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import time
from pymongo import MongoClient
import uuid
import datetime
import requests
from flask import Flask, jsonify, render_template_string

# Load environment variables
load_dotenv()

TWITTER_USERNAME = os.getenv('TWITTER_USERNAME')
TWITTER_PASSWORD = os.getenv('TWITTER_PASSWORD')
MONGO_URI = os.getenv('MONGO_URI')
PROXYMESH_API = os.getenv('PROXYMESH_API')

# MongoDB setup
client = MongoClient(MONGO_URI)
db = client['twitter_trends']
collection = db['trends']

def get_proxy():
    # Fetch a new proxy from ProxyMesh
    response = requests.get(PROXYMESH_API)
    proxies = response.text.split()
    return proxies[0]

def fetch_trending_topics():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    proxy = get_proxy()
    options.add_argument(f'--proxy-server={proxy}')
    
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    
    driver.get('https://x.com/i/flow/login')
    time.sleep(3)
    
    # Log in to Twitter
    username = driver.find_element(By.NAME, "session[username_or_email]")
    password = driver.find_element(By.NAME, "session[password]")
    
    username.send_keys(TWITTER_USERNAME)
    password.send_keys(TWITTER_PASSWORD)
    password.send_keys(Keys.RETURN)
    
    time.sleep(5)
    
    # Fetch trending topics
    trends = driver.find_elements(By.XPATH, "//section[@aria-labelledby='accessible-list-0']//span")[1:6]
    trending_topics = [trend.text for trend in trends]

    driver.quit()
    
    # Store in MongoDB
    unique_id = str(uuid.uuid4())
    ip_address = proxy
    end_time = datetime.datetime.now()

    trend_data = {
        "unique_id": unique_id,
        "trend1": trending_topics[0],
        "trend2": trending_topics[1],
        "trend3": trending_topics[2],
        "trend4": trending_topics[3],
        "trend5": trending_topics[4],
        "end_time": end_time,
        "ip_address": ip_address
    }
    
    collection.insert_one(trend_data)

    return trend_data

# Flask app to display the trends
app = Flask(__name__)

@app.route('/')
def index():
    return '''
        <h1>Twitter Trending Topics</h1>
        <button onclick="fetchTrends()">Fetch Trends</button>
        <div id="trends"></div>
        <script>
            async function fetchTrends() {
                let response = await fetch('/fetch_trends');
                let data = await response.json();
                document.getElementById('trends').innerHTML = `
                    <p>Trend 1: ${data.trend1}</p>
                    <p>Trend 2: ${data.trend2}</p>
                    <p>Trend 3: ${data.trend3}</p>
                    <p>Trend 4: ${data.trend4}</p>
                    <p>Trend 5: ${data.trend5}</p>
                    <p>End Time: ${data.end_time}</p>
                    <p>IP Address: ${data.ip_address}</p>
                `;
            }
        </script>
    '''

@app.route('/fetch_trends')
def fetch_trends():
    trend_data = fetch_trending_topics()
    return jsonify(trend_data)

if __name__ == '__main__':
    app.run(debug=True)
