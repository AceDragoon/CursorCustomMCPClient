#llm.py
import os
import asyncio
import json
from openai import OpenAI
from mcp_experimental.servermanagers.manager import Manager
from dotenv import load_dotenv

load_dotenv()

client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

messages = [{
    "role": "system",
    "content": (
        "Du bist ein hilfreicher KI-Assistent. "
        "Wenn der Benutzer eine Aufgabe beschreibt, die mehrere Funktionen erfordert, "
        "führe sie automatisch nacheinander aus. "
        "Du darfst mehrere function_calls hintereinander tätigen, ohne den Benutzer vorher zu fragen."
    )
}]
async def chat():
    manager = Manager()
    available_tools, resources, available_prompts = await manager.add_session()
    resource_name_map = {}
    reverse_resource_map = {}


    for res in resources:
        gpt_name = str(res.uri).replace("://", "_").replace("/", "_")
        resource_name_map[gpt_name] = str(res.uri)
        reverse_resource_map[str(res.uri)] = gpt_name
    for name, uri in resource_name_map.items():
        print(next(res.description for res in resources if str(res.uri) == uri))

    while True:
        user_input = input("Du: ")
        if user_input.lower() in ["exit", "quit"]:
            break
    
        messages.append({
            "role": "user", 
            "content": [{"type": "text","text": user_input }]}) #,{"type": "image_url","image_url": {"url": "https://www.google.com"}}
        response = client_openai.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            temperature=0.7,
            functions=[
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
                for tool in available_tools
            ] + [
                    {
                    "name": name,
                    "description": next(res.description for res in resources if str(res.uri) == uri),
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
                for name, uri in resource_name_map.items()
            ] + [
                    {
                        "name": prompt.name,
                        "description": prompt.description,
                        "parameters": {
                            "type": "object",
                            "properties": {
                                arg.name: {
                                    "type": "string",  # du kannst auf "string" gehen, wenn du nichts anderes weißt
                                    "description": arg.description or f"{arg.name} (kein Beschreibungstext vorhanden)"
                                } for arg in prompt.arguments
                            },
                            "required": [arg.name for arg in prompt.arguments if arg.required]
                        }
                }
                for prompt in available_prompts
            ]
            ,
            function_call="auto",
        )

        reply = response.choices[0].message

        # Max. 5 Function-Calls hintereinander (sicheres Multi-Tool-Chaining)
        for _ in range(5):
            if reply.function_call:
                func_name = reply.function_call.name
                try:
                    func_args = json.loads(reply.function_call.arguments)
                except json.JSONDecodeError:
                    func_args = {}

                # Resource-Mapping prüfen
                if func_name in resource_name_map:
                    real_name = resource_name_map[func_name]
                else:
                    real_name = func_name
                print(f"Function name: {type(real_name)}")
                print(f"Arguments: {type(func_args)}")
                tool_result = await manager.make_request(real_name, func_args)

                # GPT-kompatiblen Namen rekonstruieren
                gpt_name = reverse_resource_map.get(real_name, real_name)

                messages.append({
                    "role": "assistant",
                    "content": None,
                    "function_call": {
                        "name": gpt_name,
                        "arguments": reply.function_call.arguments
                    }
                })
                messages.append({
                    "role": "function",
                    "name": gpt_name,
                    "content": str(tool_result)
                })

                # GPT erneut aufrufen
                followup_response = client_openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    temperature=0.7,
                    functions=[
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.inputSchema
                        }
                        for tool in available_tools
                    ] + [
                            {
                            "name": name,
                            "description": next(res.description for res in resources if str(res.uri) == uri),
                            "parameters": {
                                "type": "object",
                                "properties": {},
                                "required": []
                            }
                        }
                        for name, uri in resource_name_map.items()
                    ] + [
                            {
                                "name": prompt.name,
                                "description": prompt.description,
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        arg.name: {
                                            "type": "string",  # du kannst auf "string" gehen, wenn du nichts anderes weißt
                                            "description": arg.description or f"{arg.name} (kein Beschreibungstext vorhanden)"
                                        } for arg in prompt.arguments
                                    },
                                    "required": [arg.name for arg in prompt.arguments if arg.required]
                                }
                        }
                        for prompt in available_prompts
                    ]
                    ,
                    function_call="auto",
                )
                
                reply = followup_response.choices[0].message
            else:
                if reply.content:
                    print(f"GPT: {reply.content}")
                    messages.append({"role": "assistant", "content": reply.content})
                break


if __name__ == "__main__":
    asyncio.run(chat())
