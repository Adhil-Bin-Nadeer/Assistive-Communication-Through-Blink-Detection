# ESP32 Configuration
# Update this file with your ESP32 device IP address and settings

ESP32_CONFIG = {
    # Default ESP32 IP address - CHANGE THIS TO YOUR ESP32'S IP
        "ip": "10.58.13.50",
    
    # HTTP port (default: 80)
    "port": 80,
    
    # Request timeout in seconds
    "timeout": 5,
    
    # Device names mapping (customize based on your setup)
    "devices": {
        "light1": "Living Room Light",
        "light2": "Bedroom Light",
        "fan": "Ceiling Fan",
        "ac": "Air Conditioner"
    }
}

# How to find your ESP32 IP:
# 1. Check your router's connected devices list
# 2. Use ESP32 serial monitor to print IP at startup
# 3. Use network scanner tools like "Advanced IP Scanner"
# 4. Check your ESP32 code - it should print the IP when connecting to WiFi
