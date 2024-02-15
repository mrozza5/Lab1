import datetime as dt
import json

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# Your API tokens
API_TOKEN = <your_token>
VISUAL_CROSSING_API_KEY = <your_API>

class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv


def fetch_weather(city, time):
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city}/{time}?key={VISUAL_CROSSING_API_KEY}"
    response = requests.get(url)

    if response.status_code == requests.codes.ok:
        weather_data = json.loads(response.text)
        if "days" in weather_data and len(weather_data["days"]) > 0:
            day_data = weather_data["days"][0]  
            return {
                "temp_c": round((day_data.get("temp")-32)*5/9),
                "wind_kph": day_data.get("windspeed"),
                "pressure_mb": round(day_data.get("pressure")/10000, 2),
                "humidity": day_data.get("humidity"),
                
            }
        else:
            raise InvalidUsage("No weather data available for the provided time", status_code=404)
    else:
        raise InvalidUsage(response.text, status_code=response.status_code)


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/")
def home_page():
    return "<p><h2>KMA L2: Python SaaS.</h2></p>"


@app.route("/content/api/v1/integration/generate", methods=["POST"])
def weather_endpoint():
    start_dt = dt.datetime.now()
    json_data = request.get_json()

    if json_data.get("token") is None:
        raise InvalidUsage("Token is required", status_code=400)

    token = json_data.get("token")

    if token != API_TOKEN:
        raise InvalidUsage("Wrong API token", status_code=403)

    requester_name = json_data.get("requester_name")  
    city = json_data.get("city")
    time = json_data.get("time")

    if not city or not time or not requester_name:
        raise InvalidUsage("City, time, and requester name are required", status_code=400)

    weather_data = fetch_weather(city, time)

    end_dt = dt.datetime.now()

    result = {
        "requester_name": requester_name,
        "timestamp": end_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "location": city,
        "date": time,
        "weather": weather_data,
    }

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
