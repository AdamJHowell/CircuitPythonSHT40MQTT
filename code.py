#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This is what privateInfo.py should look like:
secrets = {
  'ssid': 'FairCom',
  'password': '6faircom3global0operations0',
  "broker": "adamh-dt-2019.west.faircom.com",
  "port": 1883,
  'homeSsid': 'Red5',
  'homePassword': '8012254722',
  "homeBroker": "192.168.55.200",
  'location': 'Utah, US',
  "clientId": "QPTyESP32S2",
  "aio_username": "",
  "aio_key": "",
}
"""
import time

import adafruit_minimqtt.adafruit_minimqtt as mqtt_class
import adafruit_sht4x
import board
import socketpool
import wifi as wifi


# Add a privateInfo.py to your filesystem that has a dictionary called secrets with your WiFi credentials.
try:
  from privateInfo import secrets
except ImportError:
  print( "WiFi credentials are kept in privateInfo.py, please add them there!" )
  raise

"""
pip install adafruit-circuitpython-sht4x
pip install adafruit-circuitpython-minimqtt
"""

sht_temp = [21.12, 21.12, 21.12]
sht_humidity = [21.12, 21.12, 21.12]
topic_root = "AdamsDesk/QTPy"
command_topic = topic_root + "/commands"
rssi_topic = topic_root + "/rssi"
ip_topic = topic_root + "/ip"
mac_topic = topic_root + "/mac"
publish_count_topic = topic_root + "/publishCount"
celsiusTopic = topic_root + "/SHT40/tempC"
FahrenheitTopic = topic_root + "/SHT40/tempF"
humidityTopic = topic_root + "/SHT40/humidity"
sensor_interval = 15
mac_address = "00:11:22:AA:BB:CC"
ip_address = "127.0.0.1"
rssi = -21


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
  print( "New message on topic {0}: {1}".format( topic, inbound_message ) )
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
    rssi = wifi.radio.ap_info.rssi


def infinite_loop():
  global rssi
  loop_count = 0
  last_sensor_poll = 0
  poll_sensors()
  poll_sensors()
  print( f"Polling the sensor every {sensor_interval} seconds." )
  while True:
    if (time.time() - last_sensor_poll) > sensor_interval:
      loop_count += 1
      poll_sensors()
      print()
      print( f"SHT40 temperature: {average_list( sht_temp ):.2f} C, {c_to_f( average_list( sht_temp ) ):.2f} F" )
      print( f"SHT40 humidity: {average_list( sht_humidity ):.1f} %" )
      print( f"Loop count: {loop_count}" )
      print( f"RSSI: {rssi}" )
      print( f"IP address: {ip_address}" )
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


def get_mac_address():
  mac_string = ""
  subsequent = False
  i = 0
  for _ in wifi.radio.mac_address:
    if subsequent:
      mac_string += ":"
    mac_string += f"{wifi.radio.mac_address[i]:02x}"
    subsequent = True
    i += 1
  return mac_string


def wifi_scan():
  # Scan for SSIDs and return the ones we are interested in.
  ssid_found = ""
  print( "Available WiFi networks:" )
  for network in wifi.radio.start_scanning_networks():
    print( "\t%s\t\tRSSI: %d\tChannel: %d" % (str( network.ssid, "utf-8" ), network.rssi, network.channel) )
    if network.ssid == "Red5":
      ssid_found = "Red5"
    if network.ssid == "FairCom":
      ssid_found = "FairCom"
  wifi.radio.stop_scanning_networks()
  return ssid_found


def wifi_connect():
  global mac_address, ip_address
  wifi_found = wifi_scan()

  print( "Connecting to %s" % wifi_found )
  password = secrets['homePassword']
  if wifi_found == "FairCom":
    password = secrets['password']
  wifi.radio.connect( wifi_found, password )
  print( f"Connected to {wifi_found}!" )
  mac_address = get_mac_address()
  ip_address = f"{wifi.radio.ipv4_address}"
  wifi.radio.hostname = secrets['clientId']
  print( f"  MAC address: {mac_address}" )
  print( f"  IP address: {ip_address}" )
  if ip_address is not None:
    print( f"  AP info: {wifi.radio.ap_info.rssi}" )


if __name__ == "__main__":
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
  print( "Current mode is: ", adafruit_sht4x.Mode.string[sht40.mode] )

  wifi_connect()

  broker_to_use = secrets['homeBroker']
  if ip_address.startswith( "10." ):
    broker_to_use = secrets['broker']

  # noinspection PyUnresolvedReferences
  pool = socketpool.SocketPool( wifi.radio )

  # Set up a MiniMQTT Client
  mqtt_client = mqtt_class.MQTT(
    broker = secrets["broker"],
    port = secrets["port"],
    username = secrets["aio_username"],
    password = secrets["aio_key"],
    socket_pool = pool,
    client_id = secrets["clientId"],
    is_ssl = False,
  )

  # Connect callback handlers to mqtt_client
  mqtt_client.on_connect = connect
  mqtt_client.on_disconnect = disconnect
  mqtt_client.on_subscribe = subscribe
  mqtt_client.on_unsubscribe = unsubscribe
  mqtt_client.on_publish = publish
  mqtt_client.on_message = message

  try:
    print( "Attempting to connect to %s" % mqtt_client.broker )
    mqtt_client.connect( host = mqtt_client.broker, port = 1883, keep_alive = 60 )

    print( "Subscribing to %s" % command_topic )
    mqtt_client.subscribe( command_topic )

    infinite_loop()

  except KeyError as key_error:
    print( "\n------------------------------------------------" )
    print( "There was a key error, likely in privateInfo.py!" )
    print( "------------------------------------------------\n" )

  finally:
    print( "Unsubscribing from %s" % command_topic )
    mqtt_client.unsubscribe( command_topic )

    print( "Disconnecting from %s" % mqtt_client.broker )
    mqtt_client.disconnect()
