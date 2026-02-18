# daily_log.py - runs in terminal
import json
from datetime import date

LOG_FILE = "log.json"

def load_log():
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_log(log):
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)

def main():
    log = load_log()
    today = str(date.today())
    
    print(f"\n📋 Daily Log - {today}\n")
    
    entry = {
        "sleep": input("Hours of sleep: "),
        "exercise": input("Exercise? (y/n): "),
        "mood": input("Mood (1-5): "),
        "notes": input("Notes: ")
    }
    
    log[today] = entry
    save_log(log)
    print("\n✅ Logged!")

if __name__ == "__main__":
    main()