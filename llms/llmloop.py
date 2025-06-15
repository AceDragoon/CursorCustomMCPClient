import os
import asyncio
import json
import logging
from typing import Dict, List, Optional
from openai import OpenAI
from mcp_experimental.servermanagers.manager import Manager
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class MCPClient:
    def __init__(self):
        self.client_openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.manager = None
        self.messages = [{
            "role": "system",
            "content": (
                "Du bist ein hilfreicher Assistent. Du bist in der Lage mehrere Aktionen hintereinander auszuführen. "
                "Wenn du die Aufgabe die dir der User gestellt hat abgeschlossen hast, integriere 'Mission Accomplished' am Ende deiner Antwort. "
                "Achtung: Solange du nicht 'Mission Accomplished' in deine Antwort integrierst, wird der User nicht antworten können. "
                "Gehe komplexe Aufgaben wie folgt; einen Schritt-für-Schritt Plan anzufertigen und anschließend einen Schritt pro Antwort zu bearbeiten."
            )
        }]
        self.resource_name_map = {}
        self.reverse_resource_map = {}
        self.available_tools = []
        self.resources = []
        self.available_prompts = []

    async def initialize(self):
        """Initialize the MCP manager and load available tools/resources."""
        try:
            self.manager = Manager()
            self.available_tools, self.resources, self.available_prompts = await self.manager.add_session()
            
            # Build resource mappings
            for res in self.resources:
                gpt_name = str(res.uri).replace("://", "_").replace("/", "_")
                self.resource_name_map[gpt_name] = str(res.uri)
                self.reverse_resource_map[str(res.uri)] = gpt_name
                
            logger.info(f"Initialized with {len(self.available_tools)} tools, {len(self.resources)} resources, {len(self.available_prompts)} prompts")
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP manager: {e}")
            raise

    def _build_functions_schema(self) -> List[Dict]:
        """Build the functions schema for OpenAI API."""
        functions = []
        
        # Add tools
        for tool in self.available_tools:
            functions.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            })
        
        # Add resources
        for name, uri in self.resource_name_map.items():
            resource = next((res for res in self.resources if str(res.uri) == uri), None)
            if resource:
                functions.append({
                    "name": name,
                    "description": resource.description,
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                })
        
        # Add prompts
        for prompt in self.available_prompts:
            functions.append({
                "name": prompt.name,
                "description": prompt.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        arg.name: {
                            "type": "string",
                            "description": arg.description or f"{arg.name} (keine Beschreibung verfügbar)"
                        } for arg in prompt.arguments
                    },
                    "required": [arg.name for arg in prompt.arguments if arg.required]
                }
            })
        
        return functions

    async def _execute_function_call(self, func_name: str, func_args: Dict) -> str:
        """Execute a function call and return the result."""
        try:
            # Map GPT function name to real name
            real_name = self.resource_name_map.get(func_name, func_name)
            
            # Make the request
            tool_result = await self.manager.make_request(real_name, func_args)
            
            return str(tool_result)
            
        except Exception as e:
            logger.error(f"Error executing function {func_name}: {e}")
            return f"Error: {str(e)}"

    async def _process_function_calls(self, reply) -> bool:
        """Process function calls from the assistant's response."""
        function_calls_made = False
        
        # Process up to 5 function calls in sequence
        for _ in range(5):
            if not reply.function_call:
                break
                
            function_calls_made = True
            func_name = reply.function_call.name
            
            try:
                func_args = json.loads(reply.function_call.arguments)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse function arguments: {e}")
                func_args = {}

            # Execute the function
            tool_result = await self._execute_function_call(func_name, func_args)

            # Add function call and result to message history
            self.messages.append({
                "role": "assistant",
                "content": None,
                "function_call": {
                    "name": func_name,
                    "arguments": reply.function_call.arguments
                }
            })
            
            self.messages.append({
                "role": "function",
                "name": func_name,
                "content": tool_result
            })

            # Get next response from GPT
            try:
                response = self.client_openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=self.messages,
                    temperature=0.7,
                    functions=self._build_functions_schema(),
                    function_call="auto",
                )
                reply = response.choices[0].message
                
                if reply.content:
                    print(f"GPT: {reply.content}")
                    self.messages.append({"role": "assistant", "content": reply.content})
                    
            except Exception as e:
                logger.error(f"Error in OpenAI API call: {e}")
                break
        
        return function_calls_made

    async def chat(self):
        """Main chat loop."""
        await self.initialize()
        
        print("MCP Client gestartet. Geben Sie 'exit' oder 'quit' ein, um zu beenden.")
        
        while True:
            try:
                user_input = input("\nDu: ")
                if user_input.lower() in ["exit", "quit"]:
                    print("Auf Wiedersehen!")
                    break

                self.messages.append({"role": "user", "content": user_input})
                finished = False
                
                while not finished:
                    # Get initial response from GPT
                    response = self.client_openai.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=self.messages,
                        temperature=0.7,
                        functions=self._build_functions_schema(),
                        function_call="auto",
                    )

                    reply = response.choices[0].message
                    
                    if reply.content:
                        print(f"GPT: {reply.content}")
                        self.messages.append({"role": "assistant", "content": reply.content})
                        
                        # Check if task is completed
                        if "Mission Accomplished" in reply.content:
                            finished = True

                    # Process any function calls
                    await self._process_function_calls(reply)
                    
                    # If no function calls were made and no content, something went wrong
                    if not reply.function_call and not reply.content:
                        logger.warning("Empty response from GPT")
                        finished = True

            except KeyboardInterrupt:
                print("\nUnterbrochen. Auf Wiedersehen!")
                break
            except Exception as e:
                logger.error(f"Unerwarteter Fehler: {e}")
                print(f"Ein Fehler ist aufgetreten: {e}")

async def main():
    """Main entry point."""
    client = MCPClient()
    await client.chat()

if __name__ == "__main__":
    asyncio.run(main())