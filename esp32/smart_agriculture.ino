#define BLYNK_TEMPLATE_ID "TMPL3RZOnQezr"
#define BLYNK_TEMPLATE_NAME "Smart Agriculture"
#define BLYNK_AUTH_TOKEN "TOKEN"

#include <WiFi.h>
#include <BlynkSimpleEsp32.h>
#include <DHT.h>
#include <HTTPClient.h>
String serverURL = "http://192.168.31.92:5000/predict";

char ssid[] = "wifi";
char pass[] = "pass";

#define RELAY_PIN 26
#define DHTPIN 4
#define DHTTYPE DHT11

#define SOIL_PIN 34
#define LDR_PIN 35

DHT dht(DHTPIN, DHTTYPE);
BlynkTimer timer;

void sendSensorData()
{
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();

  int soilRaw = analogRead(SOIL_PIN);
  int lightRaw = analogRead(LDR_PIN);

  int soil = map(soilRaw, 0, 4095, 0, 99);
  int light = map(lightRaw, 0, 4095, 0, 99);

  Serial.print("Temp: ");
  Serial.println(temperature);

  Serial.print("Humidity: ");
  Serial.println(humidity);

  Serial.print("Soil: ");
  Serial.println(soil);

  Serial.print("Light: ");
  Serial.println(light);

  Serial.println("----------------");

  // Send to Blynk Dashboard
  Blynk.virtualWrite(V0, temperature);
  Blynk.virtualWrite(V1, humidity);
  Blynk.virtualWrite(V2, soil);
  Blynk.virtualWrite(V3, light);

  // Send to AI Server
  HTTPClient http;

  http.begin(serverURL);
  http.addHeader("Content-Type", "application/json");

  String jsonData = "{";
  jsonData += "\"temp\":" + String(temperature) + ",";
  jsonData += "\"humidity\":" + String(humidity) + ",";
  jsonData += "\"light\":" + String(light) + ",";
  jsonData += "\"soil\":" + String(soil);
  jsonData += "}";

  int httpResponseCode = http.POST(jsonData);

  Serial.print("AI Server Response: ");
  Serial.println(httpResponseCode);

  http.end();
}
BLYNK_WRITE(V4)
{
  int motorState = param.asInt();

  if (motorState == 1)
  {
    digitalWrite(RELAY_PIN, LOW);
    Serial.println("Motor ON");
  }
  else
  {
    digitalWrite(RELAY_PIN, HIGH);
    Serial.println("Motor OFF");
  }
}

void setup() {
  Serial.begin(115200);
  delay(3000);

  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, HIGH);   // keep motor OFF initially

  Serial.println("ESP32 Booting...");
  Serial.println("Connecting to WiFi...");

  WiFi.begin(ssid, pass);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("WiFi Connected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  Serial.println("Connecting to Blynk...");
  Blynk.begin(BLYNK_AUTH_TOKEN, ssid, pass, "blynk.cloud", 80);

  Serial.println("Connected to Blynk!");

  dht.begin();

  timer.setInterval(60000L, sendSensorData);
}

void loop() {
  Blynk.run();
  timer.run();
}