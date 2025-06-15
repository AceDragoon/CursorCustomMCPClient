# Function Calling LLM mit Ollama (manuelles Tool-Parsing)
from ollama import Client
import sys
import json
import asyncio
import re
from mcp_experimental.servermanagers.manager import Manager
from dotenv import load_dotenv

# Konfiguration
load_dotenv()


# Modell-Einstellung
MODEL_NAME = "llama3"  # Oder ein anderes Modell wie "mistral" oder "qwen2:7b"

# Nachrichtenspeicher für den Kontext
messages = [
    {
        'role': 'system',
        'content': (
                    """
                    Du bist eine hilfsbereite Pflegekraft aus Oberbayern. Du beantwortest Fragen freundlich und klar. Wenn es notwendig ist, darfst du Tools (Funktionen) verwenden, um Aufgaben zu erledigen – aber nur dann.

                    ### Wichtige Regeln für Funktionsaufrufe:

                    1. Verwende nur dann eine Funktion, wenn du sie **wirklich brauchst**.
                    2. Verwende dieses exakte Format, wenn du eine Funktion aufrufst:

                    ```function
                    {{
                    "name": "funktionsname",
                    "arguments": {{
                        "param1": "wert1",
                        "param2": "wert2"
                    }}
                    }}
                    Schreibe nichts vor oder nach dem Funktionsblock. Kein Text, keine Erklärungen, keine Überschriften.

                    Du darfst nur eine Funktion pro Antwort aufrufen.

                    Warte auf das Ergebnis, bevor du weitermachst. Verwende dieses Ergebnis in der nächsten Antwort.

                    Niemals simulieren oder raten. Beispiel: Nicht sagen „Es ist 18:47 Uhr“, bevor du das Tool time_now aufgerufen und das echte Ergebnis bekommen hast.

                    Beispiel für korrektes Verhalten:
                    Du: Wie spät ist es?

                    LLM:

                    function
                    Kopieren
                    Bearbeiten
                    {{
                    "name": "time_now",
                    "arguments": {{}}
                    }}
                    (Warte auf Tool-Ergebnis, dann antworten)

                    LLM: Es ist aktuell 22:04 Uhr. Zeit, langsam zur Ruhe zu kommen.

                    Wenn du keine Funktion brauchst, antworte ganz normal.
                    ⚠️ Niemals simulieren!

                    Beispiel für FALSCHES Verhalten (so darfst du NICHT antworten):

                    LLM: 
                    ```function
                    {{
                    "name": "time_now",
                    "arguments": {{}}
                    }}
                    Es ist jetzt 18:47 Uhr.

                    → ❌ Das ist falsch! Du darfst erst antworten, wenn du das Ergebnis erhalten hast.
                    """

        )
    }
]

# Ollama Client erstellen
client = Client()

# Funktion zum Extrahieren von Funktionsaufrufen aus LLM-Antworten
def extract_function_call(text):
    pattern = r"```function\s*({[\s\S]*?})\s*```"
    match = re.search(pattern, text)
    if match:
        try:
            function_json = json.loads(match.group(1))
            return function_json
        except json.JSONDecodeError:
            return None
    return None

async def chat():
    manager = Manager()
    available_tools, resources, available_prompts = await manager.add_session()
    resource_name_map = {}
    reverse_resource_map = {}
    
    # Erstelle eine Beschreibung aller verfügbaren Tools für das System-Prompt
    tool_descriptions = "Verfügbare Funktionen:\n\n"
    
    for res in resources:
        gpt_name = str(res.uri).replace("://", "_").replace("/", "_")
        resource_name_map[gpt_name] = str(res.uri)
        reverse_resource_map[str(res.uri)] = gpt_name
        
        tool_descriptions += f"- {gpt_name}: {next(r.description for r in resources if str(r.uri) == str(res.uri))}\n"
    
    for tool in available_tools:
        tool_descriptions += f"- {tool.name}: {tool.description}\nParameter: {json.dumps(tool.inputSchema, indent=2)}\n\n"
    
    for prompt in available_prompts:
        params = {arg.name: arg.description or f"{arg.name}" for arg in prompt.arguments}
        required = [arg.name for arg in prompt.arguments if arg.required]
        tool_descriptions += f"- {prompt.name}: {prompt.description}\nParameter: {json.dumps(params, indent=2)}\nErforderlich: {required}\n\n"
    
    # Aktualisiere das System-Prompt mit den Tool-Beschreibungen
    messages[0]['content'] += "\n\n" + tool_descriptions

    try:
        while True:
            user_input = input("Du: ")
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("Auf Wiedersehen!")
                break

            messages.append({'role': 'user', 'content': user_input})
            
            # Bis zu 5 Funktionsaufrufe erlauben (für Multi-Tool-Chaining)
            for _ in range(5):
                try:
                    # Anfrage an Ollama senden
                    response = client.chat(
                        model=MODEL_NAME,
                        messages=messages,
                        stream=False,
                        options={
                            "temperature": 0.7,
                        }
                    )
                    
                    content = response['message']['content']
                    
                    # Nach Funktionsaufrufen im Text suchen
                    function_call = extract_function_call(content)
                    
                    if function_call and 'name' in function_call and 'arguments' in function_call:
                        func_name = function_call['name']
                        func_args = function_call['arguments']
                        
                        # Entferne den Funktionsaufruf aus der Antwort
                        clean_content = re.sub(r"```function\s*{[\s\S]*?}\s*```", "", content).strip()
                        if clean_content:
                            print(f"LLM: {clean_content}")
                        
                        print(f"[Rufe Funktion auf: {func_name}]")
                        
                        # Resource-Mapping prüfen
                        if func_name in resource_name_map:
                            real_name = resource_name_map[func_name]
                        else:
                            real_name = func_name

                        # Tool ausführen
                        tool_result = await manager.make_request(real_name, func_args)
                        
                        # GPT-kompatiblen Namen rekonstruieren
                        gpt_name = reverse_resource_map.get(real_name, real_name)
                        
                        # Füge Funktionsaufruf und Ergebnis zum Kontext hinzu
                        messages.append({
                            'role': 'assistant',
                            'content': content
                        })
                        
                        messages.append({
                            'role': 'user',
                            'content': f"Ergebnis des Funktionsaufrufs {gpt_name}:\n\n{str(tool_result)}\n\nNutze es, um ggf. weiterzumachen."
                        })
                    else:
                        # Keine Funktionsaufrufe gefunden, gib Antwort aus
                        if content:
                            print(f"LLM: {content}")
                            messages.append({
                                'role': 'assistant', 
                                'content': content
                            })
                        break
                        
                except Exception as e:
                    print(f"\nFehler bei Anfrage: {str(e)}")
                    break
                    
    except Exception as e:
        print(f"\nFehler: {str(e)}")

if __name__ == "__main__":
    asyncio.run(chat())