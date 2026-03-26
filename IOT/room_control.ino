/*
 * ESP32 Room Control Server
 * SilentVoice ESP32 Controller
 */

#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>

// WiFi credentials
const char *ssid = "Adhil";
const char *password = "Adhil@999";

// Static IP Configuration
const bool USE_STATIC_IP = true;
 
IPAddress staticIP(10, 11, 255, 50); // ESP32 IP
IPAddress gateway(10, 11, 255, 210); // Router Gateway
IPAddress subnet(255, 255, 255, 0);
IPAddress dns1(8, 8, 8, 8);
IPAddress dns2(8, 8, 4, 4);

// Web server
WebServer server(80);

// GPIO pins
const int LIGHT1_PIN = 2;
const int LIGHT2_PIN = 4;
const int FAN_PIN = 5;
const int AC_PIN = 18;

// Device states
bool light1State = false;
bool light2State = false;
bool fanState = false;
bool acState = false;

void setup()
{
    Serial.begin(115200);
    delay(1000);

    pinMode(LIGHT1_PIN, OUTPUT);
    pinMode(LIGHT2_PIN, OUTPUT);
    pinMode(FAN_PIN, OUTPUT);
    pinMode(AC_PIN, OUTPUT);

    digitalWrite(LIGHT1_PIN, LOW);
    digitalWrite(LIGHT2_PIN, LOW);
    digitalWrite(FAN_PIN, LOW);
    digitalWrite(AC_PIN, LOW);

    Serial.println("\nConnecting to WiFi...");

    WiFi.mode(WIFI_STA);

    if (USE_STATIC_IP)
    {
        if (!WiFi.config(staticIP, gateway, subnet, dns1, dns2))
        {
            Serial.println("Static IP configuration failed!");
        }
        else
        {
            Serial.println("Static IP configured");
        }
    }

    WiFi.begin(ssid, password);

    int attempts = 0;

    while (WiFi.status() != WL_CONNECTED && attempts < 30)
    {
        delay(500);
        Serial.print(".");
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED)
    {
        Serial.println("\nWiFi Connected");
        Serial.print("ESP32 IP Address: ");
        Serial.println(WiFi.localIP());
    }
    else
    {
        Serial.println("\nWiFi Connection Failed");
        return;
    }

    setupRoutes();

    server.begin();

    Serial.println("Web Server Started");
}

void loop()
{
    server.handleClient();
}

void setupRoutes()
{
    server.on("/ping", HTTP_GET, handlePing);

    server.on("/device/light1/on", HTTP_GET, []()
              { handleDeviceControl("light1", "on"); });

    server.on("/device/light1/off", HTTP_GET, []()
              { handleDeviceControl("light1", "off"); });

    server.on("/device/light1/toggle", HTTP_GET, []()
              { handleDeviceControl("light1", "toggle"); });

    server.on("/device/light2/on", HTTP_GET, []()
              { handleDeviceControl("light2", "on"); });

    server.on("/device/light2/off", HTTP_GET, []()
              { handleDeviceControl("light2", "off"); });

    server.on("/device/light2/toggle", HTTP_GET, []()
              { handleDeviceControl("light2", "toggle"); });

    server.on("/device/fan/on", HTTP_GET, []()
              { handleDeviceControl("fan", "on"); });

    server.on("/device/fan/off", HTTP_GET, []()
              { handleDeviceControl("fan", "off"); });

    server.on("/device/fan/toggle", HTTP_GET, []()
              { handleDeviceControl("fan", "toggle"); });

    server.on("/device/ac/on", HTTP_GET, []()
              { handleDeviceControl("ac", "on"); });

    server.on("/device/ac/off", HTTP_GET, []()
              { handleDeviceControl("ac", "off"); });

    server.on("/device/ac/toggle", HTTP_GET, []()
              { handleDeviceControl("ac", "toggle"); });

    server.on("/device/light1/status", HTTP_GET, []()
              { handleDeviceStatus("light1"); });

    server.on("/device/light2/status", HTTP_GET, []()
              { handleDeviceStatus("light2"); });

    server.on("/device/fan/status", HTTP_GET, []()
              { handleDeviceStatus("fan"); });

    server.on("/device/ac/status", HTTP_GET, []()
              { handleDeviceStatus("ac"); });

    server.on("/devices/all", HTTP_GET, handleAllDevices);

    server.on("/devices/alloff", HTTP_GET, handleAllOff);

    server.onNotFound(handleNotFound);
}

void handlePing()
{
    server.send(200, "application/json", "{\"status\":\"ok\",\"message\":\"ESP32 is online\"}");
}

void handleDeviceControl(String device, String action)
{
    int pin = 0;
    bool *statePtr = nullptr;

    if (device == "light1")
    {
        pin = LIGHT1_PIN;
        statePtr = &light1State;
    }
    else if (device == "light2")
    {
        pin = LIGHT2_PIN;
        statePtr = &light2State;
    }
    else if (device == "fan")
    {
        pin = FAN_PIN;
        statePtr = &fanState;
    }
    else if (device == "ac")
    {
        pin = AC_PIN;
        statePtr = &acState;
    }
    else
    {
        server.send(404, "application/json", "{\"status\":\"error\",\"message\":\"Device not found\"}");
        return;
    }

    if (action == "on")
    {
        digitalWrite(pin, HIGH);
        *statePtr = true;
    }
    else if (action == "off")
    {
        digitalWrite(pin, LOW);
        *statePtr = false;
    }
    else if (action == "toggle")
    {
        *statePtr = !(*statePtr);
        digitalWrite(pin, *statePtr ? HIGH : LOW);
    }

    String stateStr = *statePtr ? "on" : "off";

    String response = "{\"status\":\"success\",\"device\":\"" + device + "\",\"state\":\"" + stateStr + "\"}";

    server.send(200, "application/json", response);
}

void handleDeviceStatus(String device)
{
    bool state = false;

    if (device == "light1")
        state = light1State;
    else if (device == "light2")
        state = light2State;
    else if (device == "fan")
        state = fanState;
    else if (device == "ac")
        state = acState;
    else
    {
        server.send(404, "application/json", "{\"status\":\"error\",\"message\":\"Device not found\"}");
        return;
    }

    String stateStr = state ? "on" : "off";

    String response = "{\"status\":\"success\",\"device\":\"" + device + "\",\"state\":\"" + stateStr + "\"}";

    server.send(200, "application/json", response);
}

void handleAllDevices()
{
    StaticJsonDocument<256> doc;

    doc["status"] = "success";

    JsonObject devices = doc.createNestedObject("devices");

    devices["light1"] = light1State ? "on" : "off";
    devices["light2"] = light2State ? "on" : "off";
    devices["fan"] = fanState ? "on" : "off";
    devices["ac"] = acState ? "on" : "off";

    String response;

    serializeJson(doc, response);

    server.send(200, "application/json", response);
}

void handleAllOff()
{
    digitalWrite(LIGHT1_PIN, LOW);
    digitalWrite(LIGHT2_PIN, LOW);
    digitalWrite(FAN_PIN, LOW);
    digitalWrite(AC_PIN, LOW);

    light1State = false;
    light2State = false;
    fanState = false;
    acState = false;

    server.send(200, "application/json", "{\"status\":\"success\",\"message\":\"All devices turned off\"}");
}

void handleNotFound()
{
    server.send(404, "application/json", "{\"status\":\"error\",\"message\":\"Endpoint not found\"}");
}
