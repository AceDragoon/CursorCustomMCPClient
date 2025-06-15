from mcp.server.fastmcp import FastMCP
import json
from datetime import datetime, timedelta
from pathlib import Path
import re
import anyio

DATA_PATH = Path(__file__).parent / "memory_data.json"

mcp = FastMCP(name="MemoryMCP", host="0.0.0.0", port=8051)

def load_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def parse_time_string(time_str: str) -> str:
    """Erlaubte Eingaben: 'in 5 Minuten', 'in 2 Stunden', 'um 17:30', 'morgen um 8', '2025-05-10T14:00'"""
    time_str = time_str.lower().strip()
    now = datetime.now()

    # ISO direkt übernehmen
    try:
        return datetime.fromisoformat(time_str).replace(microsecond=0).isoformat()
    except:
        pass

    # Automatisch "um HH:MM" interpretieren, wenn nur Uhrzeit kommt
    if re.fullmatch(r"\d{1,2}:\d{2}", time_str):
        time_str = "um " + time_str

    if not any(time_str.startswith(pref) for pref in ("in ", "morgen", "übermorgen", "um")):
        time_str = "in " + time_str

    if m := re.match(r"in (\d+)\s*(minute|minuten|min|mins|minutes)", time_str):
        return (now + timedelta(minutes=int(m.group(1)))).replace(microsecond=0).isoformat()
    if m := re.match(r"in (\d+)\s*(stunde|stunden|h|hour|hours)", time_str):
        return (now + timedelta(hours=int(m.group(1)))).replace(microsecond=0).isoformat()
    if m := re.match(r"(in )?um (\d{1,2})(?::(\d{2}))?", time_str):
        h, mi = int(m.group(2)), int(m.group(3) or 0)
        fut = now.replace(hour=h, minute=mi, second=0, microsecond=0)
        if fut < now: fut += timedelta(days=1)
        return fut.isoformat()
    if m := re.match(r"(in )?morgen um (\d{1,2})(?::(\d{2}))?", time_str):
        h, mi = int(m.group(2)), int(m.group(3) or 0)
        return (now + timedelta(days=1)).replace(hour=h, minute=mi, second=0, microsecond=0).isoformat()
    if m := re.match(r"(in )?übermorgen um (\d{1,2})(?::(\d{2}))?", time_str):
        h, mi = int(m.group(2)), int(m.group(3) or 0)
        return (now + timedelta(days=2)).replace(hour=h, minute=mi, second=0, microsecond=0).isoformat()

    raise ValueError(f"Zeitangabe nicht erkannt: '{time_str}'")

@mcp.tool(description="Speichert eine neue Erinnerung. Das Zeitformat muss sein: 'in X Minuten', 'in X Stunden', 'um HH:MM', 'morgen um HH', oder ein ISO-Zeitstempel wie '2025-05-10T14:00'.")
def add_reminder(title: str, time: str) -> str:
    try:
        pt = parse_time_string(time)
    except ValueError as e:
        return f"Fehler bei Zeitangabe: {e}"
    data = load_data()
    data["reminders"].append({"title": title, "time": pt, "status": "pending"})
    save_data(data)
    return f"Erinnerung '{title}' für {pt} gespeichert."

@mcp.tool()
def get_upcoming_reminders() -> list[str]:
    data = load_data()
    now = datetime.now().replace(microsecond=0).isoformat()
    return [f"{r['title']} um {r['time']}" for r in data["reminders"] if r["time"] > now and r.get("status") == "pending"]

@mcp.tool()
def remind_contact(name: str) -> str:
    data = load_data()
    today = datetime.now().date().isoformat()
    last = data["contacts"].get(name, {}).get("last_reminded")
    data["contacts"][name] = {"last_reminded": today}
    save_data(data)
    if last:
        return f"Du hast {name} zuletzt am {last} kontaktiert. Heute wäre ein guter Tag, mal wieder Hallo zu sagen!"
    return f"Du hast {name} bisher noch nicht kontaktiert. Schreib ihm doch heute mal!"

async def reminder_watcher():
    while True:
        now = datetime.now().replace(microsecond=0).isoformat()
        data = load_data()
        dirty = False
        for r in data["reminders"]:
            if r.get("status") == "pending" and r["time"] <= now:
                print(f"🔔 Erinnerung: {r['title']} ist jetzt fällig!")
                r["status"] = "notified"
                dirty = True
        if dirty:
            save_data(data)
        await anyio.sleep(30)

async def run_with_reminder():
    async with anyio.create_task_group() as tg:
        tg.start_soon(reminder_watcher)
        await mcp.run_stdio_async()

if __name__ == "__main__":
    anyio.run(run_with_reminder)
