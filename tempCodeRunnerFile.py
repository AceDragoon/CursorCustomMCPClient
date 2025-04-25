import os
import asyncio
import json
from openai import OpenAI
from client import MCPClient  # <<< Nur MCPClient importieren
from dotenv import load_dotenv

load_dotenv()

client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

messages = [
    {"role": "system", "content": "Du bist ein hilfreicher, kreativer und freundlicher KI-Assistent."}
]

async def chat():
    client = MCPClient()  # <<< MCPClient-Objekt erzeugen
    available_tools = await client.start_client()

    try:
        while True:
            user_input = input("Du: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Beende das Gespräch. Auf Wiedersehen!")
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
                ],
                function_call="auto",
            )

            reply = response.choices[0].message

            if reply.function_call:
                func_name = reply.function_call.name
                func_args_json = reply.function_call.arguments

                try:
                    func_args = json.loads(func_args_json)
                except json.JSONDecodeError:
                    func_args = {}

                print(f"🛠️ GPT möchte Funktion '{func_name}' aufrufen mit {func_args}")

                # 🔥 Jetzt dein Client-Objekt benutzen!
                tool_result = await client.call_tool(func_name, func_args)

                messages.append({
                    "role": "assistant",
                    "content": None,
                    "function_call": {
                        "name": func_name,
                        "arguments": func_args_json
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

                print(f"\nGPT: {followup_reply.content}")
                messages.append({"role": "assistant", "content": followup_reply.content})

            else:
                print(f"GPT: {reply.content}")
                messages.append({"role": "assistant", "content": reply.content})
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(chat())
