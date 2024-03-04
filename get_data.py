import schedule
import json
from datetime import datetime
import time
import urllib.request
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS


every_minute = 1
city = "Tilburg"
url = f"http://api.weatherapi.com/v1/current.json?key=xxx&q={city}"
    
def call_url(url):
    with urllib.request.urlopen(url) as response:
        data = response.read().decode("utf-8")
        data = json.loads(data)
        temperature = data["current"]["temp_c"]
        write_to_influxdb(temperature)
        print(f"Temperature: {temperature}")

def write_to_influxdb(data):
    current_time = datetime.utcnow().isoformat()

    p = Point("temperatures") \
        .tag("host", "server01") \
        .tag("region", "eu") \
        .field("value", data) \
        .field("time", current_time)
    
    write_api.write(bucket="home", record=p)


client = InfluxDBClient(url="http://localhost:8086", token="xxx", org="home")
write_api = client.write_api(write_options=SYNCHRONOUS)

schedule.every(every_minute).minutes.do(call_url, url=url)

call_url(url)

while True:
    schedule.run_pending()
    time.sleep(1)