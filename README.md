 AI Driven Smart Irrigation System

This project uses IoT and AI to automate irrigation.

System Flow

Soil Moisture Sensor → ESP32 → Flask API → AI Prediction → Water Pump

Modules

Hardware
- ESP32
- Soil Moisture Sensor
- Relay
- Water Pump

Arpit Contribution
- Arduino programming
- Sensor data acquisition
- Dashboard monitoring

Aryan Sisodia Contribution
- AI model development
- Dataset preparation
- Flask backend
- Render cloud deployment

Soil Moisture Sensor
        │
        ▼
      ESP32
        │
        ▼
   Internet (WiFi)
        │
        ▼
   Flask API (Render)
        │
        ▼
     AI Model
        │
        ▼
 Pump ON/OFF Decision
