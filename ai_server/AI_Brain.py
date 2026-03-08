from flask import Flask, request, jsonify
import pandas as pd
import joblib
import requests

app = Flask(__name__)

# load trained model
model = joblib.load("soil_model.pkl")

BLYNK_TOKEN = "IWvwGsrSqTh8I02Z-3LHe0K7MNd8YA3U"


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


@app.route("/predict", methods=["POST"])
def predict():

    data = request.json

    temp = data["temp"]
    humidity = data["humidity"]
    light = data["light"]
    soil = data["soil"]

    # ML prediction
    input_data = pd.DataFrame([[temp, humidity, light, soil]],
                              columns=['temp', 'humidity', 'light', 'soil_moisture'])

    prediction = model.predict(input_data)[0]

    dry_threshold = 35
    drop_rate = soil - prediction

    if drop_rate <= 0:
        hours_to_dry = 0
    else:
        hours_to_dry = (soil - dry_threshold) / drop_rate

    health = farm_health(soil, temp, humidity, light)

    # send results to Blynk
    requests.get(
        f"https://blynk.cloud/external/api/update?token={BLYNK_TOKEN}&V5={round(hours_to_dry,2)}"
    )

    requests.get(
        f"https://blynk.cloud/external/api/update?token={BLYNK_TOKEN}&V6={health}"
    )

    return jsonify({
        "hours_to_dry": round(hours_to_dry, 2),
        "health_score": health
    })


app.run(host="0.0.0.0", port=5000)
