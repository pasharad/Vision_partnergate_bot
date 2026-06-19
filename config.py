import os
import json
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
EXCEL_FILE_PATH = os.getenv("EXCEL_FILE_PATH", "data/boards.xlsx")
RELOAD_INTERVAL_HOURS = int(os.getenv("RELOAD_INTERVAL_HOURS", "4"))
WHITELIST_PATH = os.getenv("WHITELIST_PATH", "whitelist.json")
STATION_CONFIG_PATH = os.getenv("STATION_CONFIG_PATH", "data/station_config.json")

DIRECTION_LABELS = {
    1: "شمال",
    2: "جنوب",
    3: "شرق",
    4: "غرب",
    5: "مرکز",
    6: "خارج از تهران",
}


def load_station_config() -> dict:
    try:
        with open(STATION_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"stations": {}}
