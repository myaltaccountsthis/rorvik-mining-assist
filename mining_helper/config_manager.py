import os
import json
from constants import DEFAULT_SETTINGS

SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "settings.json")

def load_settings():
    if not os.path.exists(SETTINGS_PATH):
        return DEFAULT_SETTINGS.copy()
    try:
        with open(SETTINGS_PATH, "r") as f:
            user_settings = json.load(f)
        # Merge with defaults in case of missing keys
        return {**DEFAULT_SETTINGS, **user_settings}
    except Exception:
        return DEFAULT_SETTINGS.copy()

def save_settings(new_settings):
    with open(SETTINGS_PATH, "w") as f:
        json.dump(new_settings, f, indent=4)

def reset_settings():
    save_settings(DEFAULT_SETTINGS.copy())
