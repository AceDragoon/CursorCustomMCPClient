import os
import asyncio
import json
from openai import OpenAI
from client import MCPClient
from dotenv import load_dotenv

load_dotenv()

client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

messages = [{"role": "system", "content": "Du bist ein hilfreicher KI-Assistent."}]
async def chat():
    client = MCPClient()
    available_tools, resources = await client.start_client()
    resource_name_map = {}

    for res in resources:
        gpt_name = str(res.uri).replace("://", "_").replace("/", "_")
        resource_name_map[gpt_name] = str(res.uri)
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
                ],
                function_call="auto",
            )

            reply = response.choices[0].message

            if reply.function_call:
                func_name = reply.function_call.name
                try:
                    func_args = json.loads(reply.function_call.arguments)
                except json.JSONDecodeError:
                    func_args = {}
                
                if func_name in [tool.name for tool in available_tools]:
                    tool_result = await client.call_tool(func_name, func_args)

                elif func_name in resource_name_map:
                    resource_uri = resource_name_map[func_name]
                    resource_contents = await client.read_resource(resource_uri)
                    tool_result = resource_contents[0].text if resource_contents else "Keine Inhalte gefunden."

                else:
                    tool_result = f"Unbekannte Funktion: {func_name}"
                print(f"[Tool aufgerufen: {func_name}]")
                print(f"[Tool aufgerufen: {tool_result}]") 


                messages.append({
                    "role": "assistant",
                    "content": None,
                    "function_call": {
                        "name": func_name,
                        "arguments": reply.function_call.arguments
                    }
                })
                messages.append({
                    "role": "function",
                    "name": func_name,
                    "content": tool_result
                })

                followup_response = client_openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    temperature=0.7,
                )
                followup_reply = followup_response.choices[0].message

                print(f"GPT: {followup_reply.content}")
                messages.append({"role": "assistant", "content": followup_reply.content})

            else:
                print(f"GPT: {reply.content}")
                messages.append({"role": "assistant", "content": reply.content})

    finally:
        await client.close()

if __name__ == "__main__":
    print("!")
    asyncio.run(chat())
