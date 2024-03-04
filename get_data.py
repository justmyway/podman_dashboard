import schedule
import json
from datetime import datetime
import time
import urllib.request
from influxdb_client import InfluxDBClient, Point, WritePrecision
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

def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def write_to_influxdb(data):
    current_time = datetime.utcnow().isoformat()

    p = Point("temperatures") \
        .tag("host", "server01") \
        .tag("region", "eu") \
        .field("value", data) \
        .time(datetime.utcnow(), WritePrecision.NS)

    # Add a new field to the point
    p.field("pressure", 1013.25)

    nested_dict = {
        "location": {
            "lat": 51.0,
            "lon": 45.0
        }
    }

    flat_dict = flatten_dict(nested_dict)

    for k, v in flat_dict.items():
        p.field(k, v)
    
    write_api.write(bucket="home", record=p)


client = InfluxDBClient(url="http://localhost:8086", token="xxx", org="home")
write_api = client.write_api(write_options=SYNCHRONOUS)

schedule.every(every_minute).minutes.do(call_url, url=url)

call_url(url)

while True:
    schedule.run_pending()
    time.sleep(1)