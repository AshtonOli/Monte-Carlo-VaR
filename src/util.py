import json

def parse_json(file_path : str) -> dict:
    with open(file_path, "r") as f:
        data = json.load(f)
    if f:
        f.close()
    return data