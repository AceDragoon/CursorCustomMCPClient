#llm.py
import traceback
import os
import asyncio
import json
from openai import OpenAI
from mcp_experimental.servermanagers.manager import Manager
from dotenv import load_dotenv

load_dotenv()

client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

messages = [{"role": "system", "content": "Du bist ein hilfreicher KI-Assistent."}]
async def chat():
    manager = Manager()
    available_tools, resources, available_prompts = await manager.add_session()
    resource_name_map = {}
    reverse_resource_map = {}

    for res in resources:
        gpt_name = str(res.uri).replace("://", "_").replace("/", "_")
        resource_name_map[gpt_name] = str(res.uri)
        reverse_resource_map[str(res.uri)] = gpt_name
    try:
        while True:
            user_input = input("Du: ")
            if user_input.lower() in ["exit", "quit"]:
                break

            messages.append({"role": "user", "content": user_input})

            response = client_openai.chat.completions.create(
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

            reply = response.choices[0].message
            print(f"Reply: {reply}" )
            if reply.function_call:
                func_name = reply.function_call.name
                try:
                    func_args = json.loads(reply.function_call.arguments)
                except json.JSONDecodeError:
                    func_args = {}
                
                

                if func_name in resource_name_map:
                    func_name = resource_name_map[func_name]
                    tool_result = await manager.make_request(func_name, func_args)
                else:
                    tool_result = await manager.make_request(func_name, func_args)
                
                print(f"[Tool aufgerufen: {func_name}]")
                print(f"[Tool aufgerufen: {tool_result}]") 

                gpt_func_name = reverse_resource_map.get(func_name, func_name)
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "function_call": {
                        "name": gpt_func_name,
                        "arguments": reply.function_call.arguments
                    }
                })
                
                messages.append({
                    "role": "function",
                    "name": gpt_func_name,
                    "content": tool_result
                })
                
                try:
                    followup_response = client_openai.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=messages,
                        temperature=0.7,
                    )
                except Exception as e:
                    print("FEHLER beim Follow-up-Request:")
                    print(e)
                    traceback.print_exc()
                    print("Letzte Nachricht war:")
                    print(json.dumps(messages[-1], indent=2))
                    return
                followup_reply = followup_response.choices[0].message
                print("!")
                print(f"GPT: {followup_reply.content}")
                messages.append({"role": "assistant", "content": followup_reply.content})
                print("!")
            else:
                print(f"GPT: {reply.content}")
                messages.append({"role": "assistant", "content": reply.content})

    except:
        print("Error!")

if __name__ == "__main__":
    asyncio.run(chat())
