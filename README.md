# CircuitPythonSHT40MQTT
Uses Circuitpython to poll an SHT40 sensor and publish telemetry to a MQTT broker

This has been tested on an Adafruit QTPy ESP32S2, with the Adafruit SHT40, using the onboard STEMMA QT port.

You will need to create a privateInfo.json file which must contain:
* a JSON object with the "clientId" property set to what will be used as both the hostname and the clientID for the MQTT broker
* an array of objects named "brokerConnections", where each object contains:
* * "ssid" the Wi-Fi SSID to connect to
* * "password" the Wi-Fi password for the SSID
* * "broker" a string representing the MQTT broker hostname or IP address
* * "port" a number representing the MQTT port

Two libraries are required, and can be installed with the following commands:
* pip install adafruit-circuitpython-sht4x
* pip install adafruit-circuitpython-minimqtt
