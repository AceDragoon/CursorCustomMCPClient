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
---

## Neues MCP-Client System

Im Verlauf habe ich einen eigenen Client entwickelt, der mit dem MCP-Server über STDIO kommuniziert und automatisch die verfügbaren Tools lädt.

---

## Funktionen im Client

- **start_client()**  
  Baut die Verbindung zum Server auf, initialisiert die Session und lädt alle verfügbaren Tools.

- **call_tool(tool_name, args)**  
  Führt ein vom Server bereitgestelltes Tool mit den passenden Argumenten aus.

- **close_client()**  
  Beendet die Verbindung am Ende des Programms sauber.

---

## Technologischer Stand

- Tools werden geladen und beschrieben.
- GPT-3.5 erkennt automatisch, wann ein Tool aufgerufen werden soll.
- Nach dem Tool-Call wird die Antwort in den Chat eingebaut.

---

## Nächste Schritte

- [x] Ressourcen mit einbinden.
- [x] Prompts mit einbinden.
- [ ]  Unterstützung für mehrere Server gleichzeitig vorbereiten.
- [ ] Das Hinzufügen von Servern über eine server_config.json.
- [ ] Integration von Ollama.
