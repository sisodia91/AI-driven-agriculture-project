from flask import Flask, request, jsonify
import pandas as pd
import joblib
import requests
import os
import sys
from flask_cors import CORS
from flask import render_template,redirect, url_for
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db import create_table, insert_data
from flask import send_file

app = Flask(__name__)
create_table()
CORS(app)


# load trained model
BASE_DIR = os.path.dirname(__file__)
model_path = os.path.abspath(os.path.join(BASE_DIR, "../ai_engine/soil_model.pkl"))
model = joblib.load(model_path)

# get token from environment variable
BLYNK_TOKEN = os.getenv("BLYNK_TOKEN")
if BLYNK_TOKEN is None:
    print("WARNING: BLYNK TOKEN NOT FOUND")

def crop_recommendation(temp, humidity, soil):
    from datetime import datetime
    month = datetime.now().month

    crops_data = {
        "🌾 Wheat": {
            "months": [10, 11, 12],
            "temp": (20, 30),
            "humidity": (50, 70),
            "soil": (40, 70)
        },
        "🌽 Maize": {
            "months": [3, 4, 5, 6],
            "temp": (25, 35),
            "humidity": (40, 80),
            "soil": (50, 100)
        },
        "🥔 Potato": {
            "months": [10, 11, 12, 1],
            "temp": (20, 28),
            "humidity": (60, 90),
            "soil": (50, 80)
        },
        "🌾 Rice": {
            "months": [6, 7, 8, 9],
            "temp": (25, 35),
            "humidity": (70, 100),
            "soil": (60, 100)
        },
        "🌿 Mustard": {
            "months": [10, 11],
            "temp": (15, 25),
            "humidity": (40, 60),
            "soil": (30, 60)
        },
        "🌱 Gram (Chana)": {
            "months": [10, 11],
            "temp": (20, 30),
            "humidity": (30, 50),
            "soil": (30, 50)
        },
        "🌶️ Chili": {
            "months": [2, 3, 4],
            "temp": (20, 30),
            "humidity": (50, 70),
            "soil": (40, 70)
        },
        "🥒 Cucumber": {
            "months": [2, 3, 4, 5],
            "temp": (22, 32),
            "humidity": (60, 80),
            "soil": (50, 80)
        }
    }

    results = []

    for crop, cond in crops_data.items():

        if month not in cond["months"]:
            continue

        score = 0

        # temp scoring
        if cond["temp"][0] <= temp <= cond["temp"][1]:
            score += 40

        # humidity scoring
        if cond["humidity"][0] <= humidity <= cond["humidity"][1]:
            score += 30

        # soil scoring
        if cond["soil"][0] <= soil <= cond["soil"][1]:
            score += 30

        if score > 0:
            results.append((crop, score))

    # sort best crops
    results.sort(key=lambda x: x[1], reverse=True)

    return [f"{crop} ({score}%)" for crop, score in results[:3]]

def check_and_export_csv():
    from database.db import connect_db

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM farm_logs")
    count = cursor.fetchone()[0]

    # 👉 Trigger when 20 records collected
    if count == 20:

        cursor.execute("""
            SELECT temperature, humidity, soil_moisture, health_score, prediction, timestamp
            FROM farm_logs        """)

        rows = cursor.fetchall()

        # Convert to DataFrame
        df = pd.DataFrame(rows, columns=[
            "temperature",
            "humidity",
            "soil_moisture",
            "health_score",
            "prediction",
            "timestamp"
        ])

        # Save CSV
        file_path = os.path.join(BASE_DIR, "../dataset/farm_dataset.csv")
        df.to_csv(file_path, index=False)

        print("✅ CSV dataset created:", file_path)

    conn.close()

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/")
def home():
    return redirect(url_for('dashboard'))

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
        r = requests.get(
            f"https://blynk.cloud/external/api/update?token={BLYNK_TOKEN}&V5={round(hours_to_dry,2)}&V6={health}",
            timeout=5
        )
        print("BLYNK RESPONSE:", r.text)

    except Exception as e:
        print("BLYNK ERROR:", e)

    # ✅ ALWAYS store data
    insert_data(temp, humidity, soil, health, str(round(hours_to_dry, 2)))
    check_and_export_csv()

    return jsonify({
        "hours_to_dry": round(hours_to_dry, 2),
        "health_score": health
    })

@app.route("/crop", methods=["GET"])
def crop_api():

    from database.db import connect_db

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT temperature, humidity, soil_moisture
        FROM farm_logs
        ORDER BY timestamp DESC
        LIMIT 1
    """)

    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "No data available"})

    temp, humidity, soil = row

    result = crop_recommendation(temp, humidity, soil)

    return jsonify({
    "temperature": temp,
    "humidity": humidity,
    "soil": soil,
    "recommendation": result   # now it's a LIST
})


@app.route("/history", methods=["GET"])
def history():

    from database.db import connect_db

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT temperature, humidity, soil_moisture, health_score, prediction, timestamp
        FROM farm_logs
        ORDER BY timestamp DESC
        LIMIT 100
    """)

    rows = cursor.fetchall()
    conn.close()

    result = []

    for row in rows:
        result.append({
            "temperature": row[0],
            "humidity": row[1],
            "soil_moisture": row[2],
            "health_score": row[3],
            "prediction": row[4],
            "timestamp": row[5]
        })

    return jsonify(result)

@app.route("/download-csv")
def download_csv():
    from database.db import connect_db

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT temperature, humidity, soil_moisture, health_score, prediction, timestamp
        FROM farm_logs
    """)

    rows = cursor.fetchall()
    conn.close()

    df = pd.DataFrame(rows, columns=[
        "temperature",
        "humidity",
        "soil_moisture",
        "health_score",
        "prediction",
        "timestamp"
    ])

    file_path = os.path.join(BASE_DIR, "farm_dataset.csv")
    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime('%Y-%m-%d %H:%M:%S')
    df.to_csv(file_path, index=False)

    return send_file(file_path, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)