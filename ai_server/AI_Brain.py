from flask import Flask, request, jsonify
import pandas as pd
import joblib
import requests
import os

app = Flask(__name__)

# load trained model
BASE_DIR = os.path.dirname(__file__)
model_path = os.path.join(BASE_DIR, "soil_model.pkl")
model = joblib.load(model_path)

# get token from environment variable
BLYNK_TOKEN = os.getenv("BLYNK_TOKEN")


def farm_health(soil, temp, humidity, light):

    def score_range(value, low, high):
        if low <= value <= high:
            return 100
        elif value < low:
            return max(0, 100 - (low - value) * 5)
        else:
            return max(0, 100 - (value - high) * 5)

    soil_score = score_range(soil, 50, 70)
    temp_score = score_range(temp, 20, 32)
    humidity_score = score_range(humidity, 40, 70)
    light_score = score_range(light, 30, 80)

    health = (
        soil_score * 0.4 +
        temp_score * 0.25 +
        humidity_score * 0.2 +
        light_score * 0.15
    )

    return round(health, 2)


@app.route("/")
def home():
    return "Smart Agriculture AI Server Running"


@app.route("/predict", methods=["POST"])
def predict():

    data = request.get_json(force=True)

    temp = data["temp"]
    humidity = data["humidity"]
    light = data["light"]
    soil = data["soil"]

    print("TEMP:", temp)
    print("HUMIDITY:", humidity)
    print("LIGHT:", light)
    print("SOIL:", soil)

    input_data = pd.DataFrame(
        [[temp, humidity, light, soil]],
        columns=['temp', 'humidity', 'light', 'soil_moisture']
    )

    prediction = model.predict(input_data)[0]
    print("MODEL PREDICTION:", prediction)

    dry_threshold = 35

    drop_rate = max(0.5, abs(soil - prediction))

    hours_to_dry = (soil - dry_threshold) / drop_rate

    if hours_to_dry < 0:
        hours_to_dry = 0

    # calculate farm health score
    health = farm_health(soil, temp, humidity, light)

    print("HOURS TO DRY:", hours_to_dry)
    print("HEALTH SCORE:", health)

    # send results to Blynk
    try:
       requests.get(
    f"https://blynk.cloud/external/api/update?token={BLYNK_TOKEN}&V5={round(hours_to_dry,2)}&V6={health}"
     )
    except:
        pass

    return jsonify({
        "hours_to_dry": round(hours_to_dry, 2),
        "health_score": health
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)