#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This program is meant to use an Adafruit QTPy ESP32 to read an SHT40 sensor and publish the values to an MQTT broker.

Some variables are read in from a sidecar file named privateInfo.json, which contains the Wi-Fi SSID, Wi-Fi password,
the broker address and port, and the root topic.
The "root topic" is prepended to all other MQTT topics, and usually identifies the location and device.

This is what privateInfo.json should look like:
{
  "brokerConnections": [
    {
      "ssid": "nunya",
      "password": "nunya",
      "broker": "nunya",
      "port": 1883,
      "topic_root": "Home/QTPy"
    },
    {
      "ssid": "nunya",
      "password": "nunya",
      "broker": "nunya",
      "port": 1883,
      "topic_root": "Office/QTPy"
    }
  ],
  "clientId": "QPTyESP32S2",
  "location": "Utah, US",
  "aio_username": "",
  "aio_key": ""
}
"""
import json
import time
import neopixel
import adafruit_minimqtt.adafruit_minimqtt as mqtt_class
import adafruit_sht4x
import board
import socketpool
import wifi as wifi


"""
pip install adafruit-circuitpython-sht4x
pip install adafruit-circuitpython-minimqtt
"""

sht_temp = [21.12, 21.12, 21.12]
sht_humidity = [21.12, 21.12, 21.12]
sensor_interval = 15
mac_address = "00:11:22:AA:BB:CC"
ip_address = "127.0.0.1"
rssi = -21
pixel_modulus = 0


def set_topics( root_topic ):
  global topic_root, command_topic, rssi_topic, ip_topic, mac_topic, publish_count_topic, celsiusTopic, FahrenheitTopic, humidityTopic
  topic_root = root_topic
  command_topic = topic_root + "/commands"
  rssi_topic = topic_root + "/rssi"
  ip_topic = topic_root + "/ip"
  mac_topic = topic_root + "/mac"
  publish_count_topic = topic_root + "/publishCount"
  celsiusTopic = topic_root + "/SHT40/tempC"
  FahrenheitTopic = topic_root + "/SHT40/tempF"
  humidityTopic = topic_root + "/SHT40/humidity"


topic_root = "AdamsDesk/QTPy"
set_topics( topic_root )
command_topic = ""
rssi_topic = ""
ip_topic = ""
mac_topic = ""
publish_count_topic = ""
celsiusTopic = ""
FahrenheitTopic = ""
humidityTopic = ""


# noinspection PyUnusedLocal
def connect( connect_client, userdata, flags, rc ):
  # This function will be called when the mqtt_client is connected
  # successfully to the broker.
  print( "Connected to MQTT Broker!" )
  if userdata is not None:
    print( f"  User data: {userdata}" )
  if rc != 0:
    print( f"  Reason code: {rc}" )
  if flags != 0:
    print( f"  Reason code: {flags}" )


# noinspection PyUnusedLocal
def disconnect( disconnect_client, userdata, rc ):
  # This method is called when the mqtt_client disconnects
  # from the broker.
  print( "Disconnected from MQTT Broker!" )
  if userdata is not None:
    print( f"  User data: {userdata}" )
  if rc != 0:
    print( f"  Reason code: {rc}" )


# noinspection PyUnusedLocal
def subscribe( subscribe_client, userdata, topic, granted_qos ):
  # This method is called when the mqtt_client subscribes to a new feed.
  print( f"Subscribed to {topic} with QOS level {granted_qos}" )
  if userdata is not None:
    print( f"  User data: {userdata}" )


# noinspection PyUnusedLocal
def unsubscribe( unsubscribe_client, userdata, topic, pid ):
  # This method is called when the mqtt_client unsubscribes from a feed.
  print( f"Unsubscribed from {topic} with PID {pid}" )
  if userdata is not None:
    print( f"  User data: {userdata}" )


# noinspection PyUnusedLocal
def publish( publish_client, userdata, topic, pid ):
  # This method is called when the mqtt_client publishes data to a feed.
  print( f"Published to {topic} with PID {pid}" )
  if userdata is not None:
    print( f"  User data: {userdata}" )


# noinspection PyUnusedLocal
def message( message_client, topic, inbound_message ):
  # Method called when a client's subscribed feed has a new value.
  print( f"New message on topic {topic}: {inbound_message}" )
  # ToDo: Add code to process commands.


def add_value( input_list, value ):
  """
  This will copy element 1 to position 2,
  move element 0 to position 1,
  and add the value to element 0
  :param input_list: the list to add a value to
  :param value: the value to add
  """
  if len( input_list ) == 3:
    input_list[2] = input_list[1]
    input_list[1] = input_list[0]
    input_list[0] = value
  else:
    print( f"Input list is not the expected size: {input_list}" )


def average_list( input_list ):
  """
  This will calculate the average of all numbers in a List
  :param input_list: the List to average
  :return: the average of all values in the List
  """
  return sum( input_list ) / len( input_list )


def c_to_f( value ):
  return value * 1.8 + 32


def poll_sensors():
  global rssi
  temperature, relative_humidity = sht40.measurements
  add_value( sht_temp, temperature )
  add_value( sht_humidity, relative_humidity )
  if ip_address is not None:
    # noinspection PyUnresolvedReferences
    rssi = wifi.radio.ap_info.rssi


def change_pixels():
  """
    red: (255, 0, 0)
    orange: (255, 127, 0)
    yellow: (255, 255, 0)
    green: (0, 255, 0)
    blue: (0, 0, 255)
    indigo: (75, 0, 130)
    violet: (127, 0, 255)
    cyan: (0, 255, 255)
    purple: (255, 0, 255)
    white: (255, 255, 255)
    black (off): (0, 0, 0)
  """
  global pixel_modulus
  pixel_modulus += 1
  if pixel_modulus % 3 == 0:
    pixel.fill( (0, 255, 255) )
    print( "Neopixel changed to cyan" )
  elif pixel_modulus % 3 == 1:
    pixel.fill( (255, 0, 255) )
    print( "Neopixel changed to purple" )
  else:
    pixel.fill( (255, 255, 0) )
    print( "Neopixel changed to yellow" )


def infinite_loop():
  global rssi
  loop_count = 0
  last_sensor_poll = 0
  poll_sensors()
  poll_sensors()
  print( f"Polling the sensor every {sensor_interval} seconds." )
  while True:
    try:
      if (time.time() - last_sensor_poll) > sensor_interval:
        loop_count += 1
        poll_sensors()
        change_pixels()
        print()
        print( f"SHT40 temperature: {average_list( sht_temp ):.2f} C, {c_to_f( average_list( sht_temp ) ):.2f} F" )
        print( f"SHT40 humidity: {average_list( sht_humidity ):.1f} %" )
        print( f"Loop count: {loop_count}" )
        print( f"RSSI: {rssi}" )
        print( f"IP address: {ip_address}" )
        print( f"MAC address: {mac_address}" )
        print( f"Poll interval: {sensor_interval}" )
        print( f"Publishing to '{mqtt_client.broker}'" )
        mqtt_client.publish( celsiusTopic, average_list( sht_temp ) )
        mqtt_client.publish( FahrenheitTopic, c_to_f( average_list( sht_temp ) ) )
        mqtt_client.publish( humidityTopic, average_list( sht_humidity ) )
        mqtt_client.publish( rssi_topic, rssi )
        mqtt_client.publish( publish_count_topic, loop_count )
        mqtt_client.publish( mac_topic, mac_address )
        if ip_address is not None:
          mqtt_client.publish( ip_topic, ip_address )
        last_sensor_poll = time.time()
    except BrokenPipeError as pipe_error:
      print( f"BrokenPipeError: {pipe_error}" )
    except OSError as recovered_os_error:
      print( f"The infinite_loop caught an OS error: {recovered_os_error}" )
      pixel.fill( (255, 0, 0) )
      wifi_connect()


def get_mac_address():
  mac_string = ""
  subsequent = False
  i = 0
  # noinspection PyUnresolvedReferences
  for _ in wifi.radio.mac_address:
    if subsequent:
      mac_string += ":"
    # noinspection PyUnresolvedReferences
    mac_string += f"{wifi.radio.mac_address[i]:02X}"
    subsequent = True
    i += 1
  return mac_string


def wifi_scan( config ):
  # Scan for SSIDs and return the last one found that is in the configuration parameter.
  connection_to_use = None
  print( "Available WiFi networks:" )
  # noinspection PyUnresolvedReferences
  for network in wifi.radio.start_scanning_networks():
    print( "\t%s\t\tRSSI: %d\tChannel: %d" % (str( network.ssid, "utf-8" ), network.rssi, network.channel) )
    for connection in config['brokerConnections']:
      if connection['ssid'] == network.ssid:
        connection_to_use = connection
  return connection_to_use


# noinspection PyUnresolvedReferences
def wifi_connect():
  global mac_address, ip_address

  wifi_connection = wifi_scan( configuration )

  try:
    print( f"Connecting to '{wifi_connection['ssid']}'" )
    wifi.radio.connect( wifi_connection['ssid'], wifi_connection['password'] )
    print( f"Connected to {wifi_connection['ssid']}!" )
    mac_address = get_mac_address()
    ip_address = f"{wifi.radio.ipv4_address}"
    wifi.radio.hostname = configuration['clientId']
    print( f"  MAC address: {mac_address}" )
    print( f"  IP address: {ip_address}" )
    print( f"  Hostname: {configuration['clientId']}" )
    if ip_address is not None:
      print( f"  RSSI: {wifi.radio.ap_info.rssi}" )
  except (ConnectionError, AttributeError) as connection_error:
    print( f"{connection_error}" )
    pixel.fill( (255, 0, 0) )
  return wifi_connection


def configure_client():
  # Set up a MiniMQTT Client
  client = mqtt_class.MQTT(
    broker = broker_info['broker'],
    port = broker_info["port"],
    username = configuration["aio_username"],
    password = configuration["aio_key"],
    socket_pool = pool,
    client_id = configuration["clientId"],
    is_ssl = False,
  )
  # Connect callback handlers to mqtt_client
  client.on_connect = connect
  client.on_disconnect = disconnect
  client.on_subscribe = subscribe
  client.on_unsubscribe = unsubscribe
  client.on_publish = publish
  client.on_message = message

  set_topics( broker_info['topic_root'] )
  return client


if __name__ == "__main__":
  with open( "privateInfo.json", "r" ) as config_file:
    configuration = json.loads( config_file.read() )

  # i2c = board.I2C()  # uses board.SCL and board.SDA
  # noinspection PyUnresolvedReferences
  i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller
  sht40 = adafruit_sht4x.SHT4x( i2c )
  print( f"Found SHT4x with serial number {hex( sht40.serial_number )}" )
  # noinspection PyUnresolvedReferences
  sht40.mode = adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION
  # Can also set the mode to enable heater
  # sht40.mode = adafruit_sht4x.Mode.LOWHEAT_100MS
  # noinspection PyUnresolvedReferences
  print( f"Current mode is: {adafruit_sht4x.Mode.string[sht40.mode]}" )

  # noinspection PyUnresolvedReferences
  pixel = neopixel.NeoPixel( board.NEOPIXEL, 1 )
  pixel.fill( (0, 0, 255) )

  broker_info = wifi_connect()

  # noinspection PyUnresolvedReferences
  pool = socketpool.SocketPool( wifi.radio )

  mqtt_client = configure_client()

  try:
    print( f"Attempting to connect to {broker_info['broker']}:{broker_info['port']}" )
    mqtt_client.connect( host = broker_info['broker'], port = broker_info['port'], keep_alive = 60 )

    print( f"Subscribing to {command_topic}" )
    mqtt_client.subscribe( command_topic )

    infinite_loop()

  except KeyError as key_error:
    print( "\n--------------------------------------------------" )
    print( "There was a key error, likely in privateInfo.json!" )
    print( "--------------------------------------------------\n" )
    pixel.fill( (255, 0, 0) )
  except OSError as os_error:
    print( f"An OS error interrupted the process: {os_error}" )
    pixel.fill( (255, 0, 0) )
  finally:
    print( f"Unsubscribing from {command_topic}" )
    mqtt_client.unsubscribe( command_topic )

    print( f"Disconnecting from {mqtt_client.broker}" )
    mqtt_client.disconnect()
