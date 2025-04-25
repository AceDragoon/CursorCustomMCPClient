import os
import asyncio
from openai import OpenAI
from client import start_client
from dotenv import load_dotenv

load_dotenv()

# Setze deinen OpenAI-API-Schlüssel
client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

messages = [
    {"role": "system", "content": "Du bist ein hilfreicher, kreativer und freundlicher KI-Assistent."}
]

async def chat():
    available_tools = await start_client()

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
            stream=True,
        )

        print("GPT:", end=" ", flush=True)
        full_response = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_response += content
        print()

        messages.append({"role": "assistant", "content": full_response})

if __name__ == "__main__":
    asyncio.run(chat())
