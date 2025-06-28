import json
import datetime as dt

def parse_json(file_path : str) -> dict:
    with open(file_path, "r") as f:
        data = json.load(f)
    if f:
        f.close()
    return data

def dt_date_range(start: dt.datetime, interval: int, periods: int):
    for i in range(periods):
        yield start +  dt.timedelta(seconds=i * interval)