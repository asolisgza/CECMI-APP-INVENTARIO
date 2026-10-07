import json
import os
from datetime import datetime

MOVEMENTS_FILE = os.path.join(os.path.dirname(__file__), "movements.jsonl")


def record_movement(action, box_name, location, sample):
    movement = {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "action": action,
        "box": box_name,
        "location": f"{location[0]},{location[1]}",
        "sample_id": sample.get("id", ""),
    }
    with open(MOVEMENTS_FILE, "a", encoding="utf-8") as movement_file:
        movement_file.write(json.dumps(movement, ensure_ascii=False) + "\n")


def load_movements():
    if not os.path.exists(MOVEMENTS_FILE):
        return []

    with open(MOVEMENTS_FILE, "r", encoding="utf-8") as movement_file:
        return [
            json.loads(line)
            for line in movement_file
            if line.strip()
        ]


def clear_movements():
    try:
        os.remove(MOVEMENTS_FILE)
    except FileNotFoundError:
        pass