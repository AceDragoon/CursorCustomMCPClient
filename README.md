# MCP-Experimental

Dieses Repository dient zur Visualisierung meines Fortschritts im Bereich Model Context Protocol (MCP) – bis jetzt wurde Claude Desktop in Verbindung mit lokalen Tools und Ressourcen getestet.

---

- Das Ziel dieses Repository ist es meinen Lernablauf fortfahrend zu dokumentieren 

---

## Aktueller Standpunkt
Für dieses Projekt habe ich uv verwendet hier die verwendeten Commands:
```bash
uv init mcp-server-demo
cd mcp-server-demo
uv add "mcp[cli]"
uv run main.py
```
### Configuration des MCP-Servers 
In Cursor habe ich anschließend in der Struktur des "mcp[cli]" habe ich dann die main.py Datei mit folgenden Codes verändert. In Claude Desktop wurden die Tools, Ressources und Prompts von mir getestet.

## Beispiele

### Tools
```python
@mcp.tool()
def create_note(title: str, content: str) -> str:
    """Erstellt eine neue Notiz."""
    notes.append({"title": title, "content": content})
    return f"Notiz '{title}' gespeichert."
```

### Resources
```python
@mcp.resource("notes")
def all_notes() -> str:
    """Stellt alle gespeicherten Notizen als lesbare Ressource bereit."""
    notes = load_notes()
    if not notes:
        return "Es sind keine Notizen vorhanden."
```
