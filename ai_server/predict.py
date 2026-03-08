import joblib
import pandas as pd

model = joblib.load("soil_model.pkl")

temp = 31
humidity = 50
light = 80
soil = 64

input_data = pd.DataFrame([[temp,humidity,light,soil]],
columns=['temp','humidity','light','soil_moisture'])

prediction = model.predict(input_data)

print("Predicted next soil moisture:", prediction[0])

dry_threshold = 35
drop_rate = soil - prediction[0]

hours_to_dry = (soil - dry_threshold) / drop_rate

print("\nSoil Moisture:",soil,"%")
print("Temperature:",temp,"°C")

print("\nPrediction:")
print("Soil will dry in",round(hours_to_dry,2),"hours")

def score_range(value, low, high):

    if low <= value <= high:
        return 100
    elif value < low:
        return max(0, 100 - (low - value) * 5)
    else:
        return max(0, 100 - (value - high) * 5)


def farm_health(soil, temp, humidity, light):

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

    return min(round(health,2),96)


health = farm_health(soil, temp, humidity, light)

print("\nFarm Health Score:", health, "%")

