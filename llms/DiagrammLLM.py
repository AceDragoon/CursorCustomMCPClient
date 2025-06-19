#DiagrammLLM.py
import os
import asyncio
import json
import yaml
from openai import OpenAI
from mcp_experimental.servermanagers.manager import Manager
from mcp_experimental.llms.AbstractLLM import AbstractLLM
from dotenv import load_dotenv
from mcp_experimental.utils.paths import get_project_base
import traceback
import base64

load_dotenv()

client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class DiagramLLM(AbstractLLM):

    def __init__(self):
        self.manager = Manager()
    
    async def load_image(self, image_path="RAG_Diagram.png") -> dict:
        # 1. Bild einlesen & base64 encodieren
        with open(get_project_base() / image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()

        # 2. content als LISTE definieren!
        return {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Bewerte bitte die Logik dieses Diagramms anhand des Bildes."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img_b64}"
                    }
                }
            ]
        }

    async def load_config(self, config_path = "testconfig.yaml") -> dict:
        with open(get_project_base() / config_path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
        return config
    

    async def load_tools(self) -> list:
        tools, resources, prompts = await self.manager.add_session()

        structured_functions=[
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
            for tool in tools
        ] + [
                {
                "name": resource.name.replace("://", "_"),
                "description": resource.description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
            for resource in resources
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
            for prompt in prompts
        ]

        return structured_functions


    def user_message(self) -> str:
        user_input = input("Enter your message: ")
        return {
            "role": "user",
            "content": [
                {
                "type": "text",
                "text": user_input 
                }
                ]
            }


    async def system_message(self, messages: list, tools: list, model: str, temperature: float):

        response = client_openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            functions=tools,
            function_call="auto",
        )

        return response.choices[0].message
    

    async def tool_call(self, reply) -> str:
        func_name = reply.function_call.name

        try:
            func_args = json.loads(reply.function_call.arguments)
        except json.JSONDecodeError:
            print(traceback.format_exc())
            func_args = {}

        tool_result = await self.manager.make_request(func_name, func_args)


        return  {
                    "role": "assistant",
                    "content": None,
                    "function_call": {
                        "name": func_name,
                        "arguments": str(func_args)
                    }
                },{
                    "role": "function",
                    "name": func_name,
                    "content": str(tool_result)
                }
    

    async def workflow(self, prompt:list, systemprompt:str, memory) -> list:
        tools = await self.load_tools()

        memory.extend(prompt) # list
        memory.append({
            "role" : "system",
            "content" : systemprompt
        })
        
        reply = await self.system_message(memory, tools, "gpt-4.1-mini", 0.7)
        del memory[-len(prompt)-1:]

        if reply.function_call:
            resultat = await self.tool_call(reply)
            memory.extend(resultat)
        else:
            if reply.content:
                print(f"GPT: {reply.content}")
                memory.append({"role": "assistant", "content": reply.content})

        return memory
    

    async def rating(self, prompt, systemprompt:str, memory, ratings):
        rating_tool = [{
    "name": "rate_diagram",
    "description": "Bewertet ein Diagramm anhand seiner Logik. Gibt eine Bewertung (1-10) und eine Begründung zurück.",
    "parameters": {
        "type": "object",
        "properties": {
            "rating": {
                "type": "integer",
                "description": "Eine Zahl zwischen 1 (schlecht) und 10 (sehr gut), die die logische Schlüssigkeit des Diagramms bewertet."
            },
            "reason": {
                "type": "string",
                "description": "Eine kurze Begründung für die Bewertung."
            }
        },
        "required": ["rating", "reason"]
    }
}]
        
        memory.extend(ratings)
        memory.append({
            "role" : "system",
            "content" : systemprompt
        })
        memory.append(prompt)

        reply = await self.system_message(memory, rating_tool, "gpt-4.1-mini", 0.7)
        del memory[-len(prompt)-2:]
        if reply.function_call:
            arguments_str = reply.function_call.arguments
            
            arguments = json.loads(arguments_str)

            rating = arguments.get("rating")
            reason = arguments.get("reason")
            
            print(f"Bewertung: {rating}")
            print(f"Begründung: {reason}")
            return rating, reason
        else:
            print("Keine function_call in der Antwort!")
            return "Error"


    

    async def logic(self):
        config = await self.load_config()
        user_messages = []
        logic_memory = []
        logic_rating = 0
        max_attempts = 2
        ratings = []

        user_messages.append( self.user_message())

        print("Process Rückfrage: ")
        await self.workflow(user_messages, config["system_prompts"]["Rückfrage"], [])

        user_messages.append( self.user_message())

        print("Process Faktenzusammentragung: ")
        logic_memory.extend(await self.workflow(user_messages, config["system_prompts"]["Fakten"], logic_memory[-5:]))

        for attempt in range(max_attempts):
            if logic_rating > 8:
                break
            print("Process Skizierug: ")
            logic_memory.extend(await self.workflow(user_messages, config["system_prompts"]["Skizze"], logic_memory[-5:]))
            print("Process Kantenbearbeitung: ")
            logic_memory.extend(await self.workflow(user_messages, config["system_prompts"]["Kanten"], logic_memory[-5:]))
            print("Process Bewertung: ")
            logic_rating, reason = await self.rating(await self.load_image(), config["system_prompts"]["Logik_Bewertung"], user_messages, ratings)
            logic_memory.append({
                "role": "assistant",
                "content": f"Bewertung: {str(reason)}"
            })
            ratings.append({
                "role": "assistant",
                "content": f"Rating:{str(logic_rating)} Begründung: {str(reason)}"
            })
            
        return [logic_memory[-3]], user_messages[:2]
    
    async def layout(self, user_messages):
        config = await self.load_config()
        layout_memory = []
        max_attempts = 2
        layout_rating = 0
        ratings = []
        print("/n Layout ------------------------------------------------------------------------------------ /n")
        for attempt in range(max_attempts):
            if layout_rating > 8:
                break
            print("Process Knoten: ")
            layout_memory.extend(await self.workflow(user_messages, config["system_prompts"]["Layout_Nodes"], layout_memory[-5:]))
            print("Process Kanten: ")
            layout_memory.extend(await self.workflow(user_messages, config["system_prompts"]["Layout_Pfeile"], layout_memory[-5:]))
            print("Process Schrift: ")
            layout_memory.extend(await self.workflow(user_messages, config["system_prompts"]["Layout_Schrift"], layout_memory[-5:]))
            print("Process Bewertung: ")
            rating, reason = await self.rating(await self.load_image(), config["system_prompts"]["Layout_Bewertung"], user_messages, ratings)
            layout_memory.append({
                "role": "assistant",
                "content": f"Bewertung: {str(reason)}"
            })
            ratings.append({
                "role": "assistant",
                "content": f"Rating:{str(rating)} Begründung: {str(reason)}"
            })

    async def main(self):
        logic, user_messages = await self.logic()
        prompt = {
            "role": "user",
            "content": [{"type": "text","text": f"Code:  {logic[0]["function_call"]["arguments"]}" }]}
        user_messages.append(prompt)
        await self.layout(user_messages)

if __name__ == "__main__":
    llm = DiagramLLM()
    asyncio.run(llm.main())

    
