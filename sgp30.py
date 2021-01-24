"""example for using the SGP30 with CircuitPython and the Adafruit library"""
 
import time
import board
import busio
import adafruit_sgp30
import Adafruit_DHT as dht
from math import e
 
def get_absolute_humidity(temperature, relative_humidity):
    absolute_humidity_in_grams_per_m3 = (6.112 * (e**((17.67 * temperature) / (temperature + 243.5))) * relative_humidity * 2.1674) / (273.15 + temperature)
    return absolute_humidity_in_grams_per_m3


i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)
 
# Create library object on our I2C port
sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c)
 
print("SGP30 serial #", [hex(i) for i in sgp30.serial])


#17/01/2021 15:42:40      eCO2 = 400 ppm          TVOC = 12 ppb
#**** Baseline values: eCO2 = 0x9e95, TVOC = 0x9cd5, Baseline= [40597, 40149]

 
sgp30.iaq_init()
sgp30.set_iaq_baseline(0x9e95, 0x9cd5)
humidity, temperature = dht.read_retry(dht.DHT22, 24)
sgp30.set_iaq_humidity(get_absolute_humidity(temperature, humidity))
 
elapsed_sec = 0
baseline_eCO2 = sgp30.baseline_eCO2
baseline_TVOC = sgp30.baseline_TVOC
 
while True:
    t = time.localtime()
    current_time = time.strftime("%d/%m/%Y %H:%M:%S", t)
    humidity, temperature = dht.read_retry(dht.DHT22, 24)
    abs_hum = get_absolute_humidity(temperature, humidity)
    co2 = sgp30.eCO2
    tvoc = sgp30.TVOC
     
    print("%s   eCO2 = %d ppm   TVOC = %d ppb   T = %.1f*C   H = %.1f%%   Abs.H = %.2fg/m3" % (
          current_time, co2, tvoc, temperature, humidity, abs_hum))
    
    f = open("valuesSgp.txt", "a+")
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
        
        f = open("valuesSgp.txt", "a+")
        f.write("**** Baseline values: eCO2 = 0x%x, TVOC = 0x%x, Baseline= %s \n"
            % (sgp30.baseline_eCO2, sgp30.baseline_TVOC, sgp30.get_iaq_baseline()))
        f.close()
