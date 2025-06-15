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

load_dotenv()

client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class DiagramLLM(AbstractLLM):
    def __init__(self):
        self.manager = Manager()
        pass


    async def retrieve_config(self, config_path) -> dict:
        with open(get_project_base() / config_path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
        return config
    
    async def retrieve_tools(self) -> list:
        available_tools, available_resources, available_prompts = await self.manager.add_session()
        resources = self.build_resource_maps(available_resources)
        print(resources)
        return available_tools, available_resources, available_prompts

    def build_resource_maps(self, resources):
        resource_name_map = {}
        reverse_resource_map = {}
        for res in resources:
            gpt_name = str(res.uri).replace("://", "_").replace("/", "_")
            resource_name_map[gpt_name] = str(res.uri)
            reverse_resource_map[str(res.uri)] = gpt_name
        return resource_name_map

    async def message_from_user(self) -> str:
        user_input = input("Enter your message: ")
        return {"role": "user", "content": [{"type": "text","text": user_input }]}
    
    
    async def create_functions(self, tools, resources, prompts) -> str:
        structured_functions=[
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                    for tool in tools
                ] + [
                        {
                        "name": resources[0].name.replace("://", "_"),
                        "description": resources[0].description,
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

    async def generate_response(self, messages, tools: list, model: str, temperature: float):
        response = client_openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            functions=tools,
            function_call="auto",
        )
        return response
    
    async def function_call(self, function_call) -> str:
        func_name = function_call.name
        try:
            func_args = json.loads(function_call.arguments or "{}")
        except json.JSONDecodeError:
            func_args = {}
        try:
            uri = function_call[0].name.replace("://", "_"),
        except:
            uri = function_call
        tool_result = await self.manager.make_request(uri, func_args)
        return  {
                    "role": "assistant",
                    "content": None,
                    "function_call": {
                        "name": func_name,
                        "arguments": function_call.function_call.arguments
                    }
                },{
                    "role": "function",
                    "name": func_name,
                    "content": str(tool_result)
                }
    
    async def main_loop(self) -> None:
        config = await self.retrieve_config("config.yaml")
        messages = []
        tools, resources, prompts = await self.retrieve_tools()
        structured_funcions = await self.create_functions(tools, resources, prompts)
        messages.append( await self.message_from_user())
        for name, system_prompt in config["system_prompts"].items():
            messages.extend(system_prompt)
            response = await self.generate_response(messages, structured_funcions, "gpt-4.1-mini", 0.7)
            reply = response.choices[0].message
            del messages[-1]
            if reply.function_call:
                await self.function_call(reply.function_call)
            elif reply.content:
                print(f"GPT: {reply.content}")
                messages.append({"role": "assistant", "content": reply.content})
        return
    
    async def close(self) -> None:
        pass

if __name__ == "__main__":
    llm = DiagramLLM()
    asyncio.run(llm.main_loop())

    
