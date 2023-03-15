# CircuitPythonSHT40MQTT
Uses Circuitpython to poll the SHT40 and publish to a broker

This has been tested on an Adafruit QTPy ESP32S2 with the Adafruit SHT40 using the onboard STEMMA QT port.

You will need to create a privateInfo.py file which contains the elements used in 'secrets'.

Install the following libraries:

* pip install adafruit-circuitpython-sht4x
* pip install adafruit-circuitpython-minimqtt
