from datetime import datetime as dt
import json
from pprint import pprint
from random import randint
try:
    from openai_init import *
except ImportError:
    from src.openai_init import *

class GPT:
    def __init__(self, 
                 model='gpt-4o', 
                 max_tokens=1000, 
                 temperature=0.3, 
                 system_message=None, 
                 injected_messages=None,
                 save_messages=False):
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.system_message = system_message
        self.injected_messages = injected_messages
        self.save_messages = save_messages

        self.message_history = []

    def compile_messages(self, prompt):
        messages = []
        if self.system_message:
            messages.append({"role": "system", "content": self.system_message})
        if self.injected_messages:
            messages.extend(self.injected_messages)
        if self.save_messages:
            messages.extend(self.message_history)
        messages.append({"role": "user", "content": prompt})
        return messages
    
    def prompt(self, prompt):
        messages = self.compile_messages(prompt)

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None,
        )

        answer = response.choices[0].message
        if self.save_messages:
            self.message_history.append({"role": "user", "content": prompt})
            self.message_history.append(answer)
        return answer.content


class stream_GPT:
    def __init__(self, 
                 model='gpt-3.5-turbo', 
                 max_tokens=1000, 
                 temperature=0.3, 
                 system_message=None, 
                 injected_messages=None,
                 save_messages=False,
                 output_heap=[]):
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.system_message = system_message
        self.injected_messages = injected_messages
        self.save_messages = save_messages
        self.output_heap=output_heap

        self.message_history = []

    def compile_messages(self, prompt):
        messages = []
        if self.system_message:
            messages.append({"role": "system", "content": self.system_message})
        if self.injected_messages:
            messages.extend(self.injected_messages)
        if self.save_messages:
            messages.extend(self.message_history)
        messages.append({"role": "user", "content": prompt})
        return messages
    
    def prompt(self, prompt):
        messages = self.compile_messages(prompt)

        stream = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None,
            stream=True,
        )

        out = []
        print("[GPT]")
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                print(chunk.choices[0].delta.content, end="")
                out.append(chunk.choices[0].delta.content)
                if len(chunk.choices[0].delta.content) > 1:
                    self.output_heap.append(chunk.choices[0].delta.content)
        print("\n[/GPT]")

        if self.save_messages:
            self.message_history.append({"role": "user", "content": prompt})
            self.message_history.append({"role": "assistant", "content": ''.join(out)})
        return None
    

def get_time():
    return dt.now().strftime("%Y-%m-%d %H:%M:%S")

def get_flooby_index(flibby, flubby):
    return str(randint(1, 127))

class handy_GPT:
    def __init__(self, 
                 model='gpt-4-0125-preview', #'gpt-3.5-turbo-0125', 
                 max_tokens=1000, 
                 temperature=0.3, 
                 system_message=None, 
                 injected_messages=None,
                 save_messages=False,
                 tool_choice="auto"):
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.system_message = system_message
        self.injected_messages = injected_messages
        self.save_messages = save_messages
        self.tool_choice=tool_choice

        self.message_history = []

        self.tools = [            
            {
                "type": "function",
                "function": {
                    "name": "get_time",
                    "description": "Get the datetime in user's current timezone."
                },
            }
        ]

        self.available_tools = {"get_time": get_time}

    def add_tool(self, tool_json, tool_function):
        self.tools.append(tool_json)
        self.available_tools[tool_json['function']['name']] = tool_function

    def print_example_tool(self):
        example_tool = {
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather in a given location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        },
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                    },
                    "required": ["location"],
                },
            },
        }
        pprint(example_tool)

    def compile_messages(self):
        messages = []
        if self.system_message:
            messages.append({"role": "system", "content": self.system_message})
        if self.injected_messages:
            messages.extend(self.injected_messages)
        messages.extend(self.message_history)
        return messages
    
    def prompt(self, prompt):
        self.message_history.append({"role": "user", "content": prompt})

        while True:
            response = client.chat.completions.create(
                model=self.model,
                messages=self.compile_messages(),
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
                tools=self.tools,
                tool_choice=self.tool_choice,
            )

            answer = response.choices[0].message
            tool_calls = answer.tool_calls

            self.message_history.append(answer)

            if tool_calls:
                
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_to_call = self.available_tools[function_name]
                    function_args = json.loads(tool_call.function.arguments)
                    function_response = function_to_call(**function_args)
                    self.message_history.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": function_response,
                        }
                    )
            else:
                break

        if not self.save_messages:
            self.message_history = []

        return answer.content
    

if __name__ == '__main__':
    m = GPT()
    print(m.prompt("What is the derivatieve of ln(x)?"))
    m = GPT(save_messages=True)
    while True:
        print(m.prompt(input(">>")))

    # m = stream_GPT(save_messages=True)

    # m.prompt("Outlines the steps for finding the derivative of e^(2x+4)?")

    # while True:
    #     m.prompt(input(">> "))
    #     m.prompt(input(">> "))

    # m = handy_GPT()
    # print(m.prompt("What time is it right now?"))

    # tool = {
    #     "type": "function",
    #     "function": {
    #         "name": "get_flooby_index",
    #         "description": "Get the current flooby index for the 2 provided integers",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "flibby": {
    #                     "type": "integer",
    #                     "description": "The flibby of the flooby index",
    #                 },
    #                 "flubby": {
    #                     "type": "integer", 
    #                     "enum": [1, 27, 69],
    #                     "description": "The flubby of the flooby index",
    #                 },
    #             },
    #             "required": ["flibby", "flooby"],
    #         },
    #     },
    # }

    # m.add_tool(tool, get_flooby_index)

    # print(m.prompt("whats the flooby index for flibby=the current hour and flubby=69?"))