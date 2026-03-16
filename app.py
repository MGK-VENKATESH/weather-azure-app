from flask import Flask, render_template, request
from azure.cosmos import CosmosClient
from dotenv import load_dotenv
import requests
import uuid
import os
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Load from environment variables
API_KEY = os.getenv("API_KEY")
COSMOS_URL = os.getenv("COSMOS_URL")
COSMOS_KEY = os.getenv("COSMOS_KEY")
DATABASE_NAME = "weatherdb"
CONTAINER_NAME = "searches"

# Connect to Cosmos DB
client = CosmosClient(COSMOS_URL, COSMOS_KEY)
database = client.get_database_client(DATABASE_NAME)
container = database.get_container_client(CONTAINER_NAME)

@app.route("/", methods=["GET", "POST"])
def index():
    weather = None
    error = None
    history = []

    # Load search history
    try:
        history = list(container.read_all_items())
        history = sorted(history, key=lambda x: x["timestamp"], reverse=True)[:5]
    except:
        history = []

    if request.method == "POST":
        city = request.form["city"]
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()

        if data.get("cod") == 200:
            weather = {
                "city": data["name"],
                "country": data["sys"]["country"],
                "temp": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "humidity": data["main"]["humidity"],
                "description": data["weather"][0]["description"].capitalize(),
                "icon": data["weather"][0]["icon"]
            }

            # Save to Azure Cosmos DB
            try:
                container.create_item(body={
                    "id": str(uuid.uuid4()),
                    "city": data["name"],
                    "country": data["sys"]["country"],
                    "temp": data["main"]["temp"],
                    "description": data["weather"][0]["description"].capitalize(),
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                print(f"Cosmos DB save error: {e}")
        else:
            error = "City not found. Please try again."

    return render_template("index.html", weather=weather, error=error, history=history)

if __name__ == "__main__":
    app.run(debug=True)