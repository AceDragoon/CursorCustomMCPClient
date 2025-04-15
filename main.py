import json
import os
import time
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("NotizenAssistent")

NOTES_FILE = os.path.expanduser("C:/Users/User/Desktop/AI Code/MCP/CursorCustomMCP/notes.json")

def load_notes():
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_notes(notes):
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, indent=2, ensure_ascii=False)


@mcp.tool()
def create_note(title: str, content: str) -> str:
    """Erstellt eine neue Notiz."""
    notes = load_notes()
    notes.append({"title": title, "content": content})
    save_notes(notes)
    return f"Notiz '{title}' wurde gespeichert."

@mcp.tool()
def list_notes() -> str:
    """Zeigt alle gespeicherten Notizen an."""
    notes = load_notes()
    if not notes:
        return "Es sind keine Notizen vorhanden."
    return "\n\n".join(f"{i+1}. {n['title']}: {n['content']}" for i, n in enumerate(notes))

@mcp.tool()
def edit_note(title: str, new_content: str) -> str:
    """Ändert den Inhalt einer bestehenden Notiz."""
    notes = load_notes()
    for note in notes:
        if note["title"].lower() == title.lower():
            note["content"] = new_content
            save_notes(notes)
            return f"Inhalt von '{title}' wurde aktualisiert."
    return f"Keine Notiz mit dem Titel '{title}' gefunden."

@mcp.tool()
def delete_note(title: str) -> str:
    """Löscht eine Notiz nach Titel."""
    notes = load_notes()
    filtered = [n for n in notes if n["title"].lower() != title.lower()]
    if len(filtered) == len(notes):
        return f"Keine Notiz mit dem Titel '{title}' gefunden."
    save_notes(filtered)
    return f"Notiz '{title}' wurde gelöscht."

@mcp.tool()
def create_note_with_reminder(title: str, content: str, remind_in_minutes: int) -> str:
    """Erstellt eine Notiz und erinnert in x Minuten daran."""
    create_note(title, content)
    remind_time = time.time() + remind_in_minutes * 60
    with open("reminders.json", "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "title": title,
            "remind_at": remind_time
        }) + "\n")
    return f"Notiz '{title}' erstellt. Ich erinnere dich in {remind_in_minutes} Minuten daran."

if __name__ == "__main__":
    mcp.run(transport="stdio")
