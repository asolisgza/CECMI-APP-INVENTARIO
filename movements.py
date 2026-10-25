import json
import os
from datetime import datetime

import streamlit as st
from streamlit_gsheets import GSheetsConnection

MOVEMENTS_FILE = os.path.join(os.path.dirname(__file__), "movements.jsonl")
SPREADSHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "17AfEVk6-HmFNwNxpngwp-cttRaFaqpZFnmRBAzDRUXo/edit"
)
MOVEMENTS_WORKSHEET = "movements"
MOVEMENT_COLUMNS = ["timestamp", "action", "box", "location", "sample_id"]


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
    return movement


def load_movements():
    if not os.path.exists(MOVEMENTS_FILE):
        return []

    with open(MOVEMENTS_FILE, "r", encoding="utf-8") as movement_file:
        return [
            json.loads(line)
            for line in movement_file
            if line.strip()
        ]


@st.cache_data(ttl=30)
def load_movements_from_sheet():
    connection = st.connection("gsheets", type=GSheetsConnection)
    movements = connection.read(
        spreadsheet=SPREADSHEET_URL,
        worksheet=MOVEMENTS_WORKSHEET,
        ttl=0,
    )
    missing_columns = set(MOVEMENT_COLUMNS).difference(movements.columns)
    if missing_columns:
        raise ValueError(
            f"La pestaña {MOVEMENTS_WORKSHEET} no tiene las columnas requeridas: "
            f"{', '.join(sorted(missing_columns))}"
        )
    return movements.dropna(how="all")[MOVEMENT_COLUMNS].reset_index(drop=True)


def clear_movement_sheet_cache():
    load_movements_from_sheet.clear()


def clear_movements():
    try:
        os.remove(MOVEMENTS_FILE)
    except FileNotFoundError:
        pass