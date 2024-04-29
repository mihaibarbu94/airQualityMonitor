"""example for using the SGP30 with CircuitPython and the Adafruit library"""

import time
import board
import busio
import adafruit_sgp30
import Adafruit_DHT as dht
from math import e
from prometheus_client import start_http_server, Gauge


def get_absolute_humidity(temperature, relative_humidity):
    absolute_humidity_in_grams_per_m3 = (6.112 * (e**((17.67 * temperature) / (temperature + 243.5))) * relative_humidity * 2.1674) / (273.15 + temperature)
    return absolute_humidity_in_grams_per_m3

def print_and_set_in_prometheus(current_time, co2, tvoc, temperature, humidity, abs_hum):
    print("%s   eCO2 = %d ppm   TVOC = %d ppb   T = %.1f*C   H = %.1f%%   Abs.H = %.2fg/m3" % (
         current_time, co2, tvoc, temperature, humidity, abs_hum))
    temp_gauge.set(temperature)
    hum_gauge.set(humidity)
    co2_gauge.set(co2)
    tvoc_gauge.set(tvoc)
    abs_hum_gauge.set(abs_hum)

def clean_dht_temp(temp):
    # if diff between old and new is more than 15% use old (bad reading)
    if ( abs(old_temperature - temp) / old_temperature ) > 0.15:
        return old_temperature
    else:
        return temp

def clean_dht_humidity(humidity):
    # if diff between old and new is more than 15% use old (bad reading)
    if ( abs(old_humidity - humidity) / old_humidity ) > 0.15:
        return old_humidity
    else:
        return humidity

def adjust_dht_humidity(humidity):
    linear_offset_factor = 20 #observed from testing with other devices
    if ( humidity < linear_offset_factor ):
        return humidity
    else:
        return humidity - linear_offset_factor

i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)

# Create library object on our I2C port
sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c)

print("SGP30 serial #", [hex(i) for i in sgp30.serial])


# 17/01/2021 15:42:40      eCO2 = 400 ppm          TVOC = 12 ppb
# **** Baseline values: eCO2 = 0x9e95, TVOC = 0x9cd5, Baseline= [40597, 40149]
# **** Baseline values: eCO2 = 0x9a0e, TVOC = 0x9c4d, Baseline= [39438, 40013]  01/03/2021 17:03:43

# **** Baseline values: eCO2 = 0x95eb, TVOC = 0x8fcc, Baseline= [38379, 36812]
# 10/07/2023 22:54:34   eCO2 = 400 ppm   TVOC = 24 ppb   T = 24.7*C   H = 56.2%   Abs.H = 12.72g/m3

sgp30.iaq_init()
sgp30.set_iaq_baseline(0x95eb, 0x8fcc)
humidity, temperature = dht.read_retry(dht.DHT22, 24)
humidity = adjust_dht_humidity(humidity)
sgp30.set_iaq_humidity(get_absolute_humidity(temperature, humidity))

elapsed_sec = 0
baseline_eCO2 = sgp30.baseline_eCO2
baseline_TVOC = sgp30.baseline_TVOC

#monitoring stuff
temp_gauge = Gauge('temperature', 'Temperature')
hum_gauge = Gauge('humidity', 'Relative Humidity')
co2_gauge = Gauge('co2', 'CO2')
tvoc_gauge = Gauge('tvoc', 'Total Volatile Organic Compounds')
abs_hum_gauge = Gauge ('abs_hum', 'Absolute Humiditity')
start_http_server(9222)

old_humidity, old_temperature = dht.read_retry(dht.DHT22, 24)
old_humidity = adjust_dht_humidity(old_humidity)
current_date_time = time.strftime("%Y%m%d-%H:%M:%S", time.localtime())

while True:
    t = time.localtime()
    current_time = time.strftime("%d/%m/%Y %H:%M:%S", t)

    #get dirty humidity and temp values
    humidity, temperature = dht.read_retry(dht.DHT22, 24)

    #adjust values using offset (observed through testing)
    humidity = adjust_dht_humidity(humidity)

    #clean
    temperature = clean_dht_temp(temperature)
    humidity = clean_dht_humidity(humidity)
    old_temperature = temperature
    old_humidity = humidity

    abs_hum = get_absolute_humidity(temperature, humidity)
    co2 = sgp30.eCO2
    tvoc = sgp30.TVOC

    print_and_set_in_prometheus(current_time, co2, tvoc, temperature, humidity, abs_hum)

    file_name ="valuesSgp" + current_date_time + ".txt"
    f = open(file_name ,"a+")
    f.write("%s   eCO2 = %d ppm   TVOC = %d ppb   T = %.1f*C   H = %.1f%%   Abs.H = %.2fg/m3 \n" % (
          current_time, co2, tvoc, temperature, humidity, abs_hum))
    f.close()

    sleep_time_in_seconds = 10
    time.sleep(sleep_time_in_seconds)
    elapsed_sec += sleep_time_in_seconds

    if elapsed_sec > sleep_time_in_seconds * 30:
        elapsed_sec = 0
        sgp30.set_iaq_humidity(get_absolute_humidity(temperature, humidity))

        print("**** Baseline values: eCO2 = 0x%x, TVOC = 0x%x, Baseline= %s"
            % (sgp30.baseline_eCO2, sgp30.baseline_TVOC, sgp30.get_iaq_baseline()))

        f = open(file_name, "a+")
        f.write("**** Baseline values: eCO2 = 0x%x, TVOC = 0x%x, Baseline= %s \n"
            % (sgp30.baseline_eCO2, sgp30.baseline_TVOC, sgp30.get_iaq_baseline()))
        f.close()
