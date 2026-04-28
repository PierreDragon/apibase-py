"""
Minimal example: OpenAI agent with persistent memory via APIBASE.

Setup:
    pip install apibase openai

APIBASE table required (e.g. table 30):
    id_memory | memory | value | agent
"""
import os
from openai import OpenAI
from apibase import ApibaseClient, Memory

AB_BASE  = os.environ['APIBASE_BASE']    # e.g. https://apibase.work
AB_TOKEN = os.environ['APIBASE_TOKEN']
AB_TABLE = int(os.environ['APIBASE_MEMORY_TABLE'])  # e.g. 3

client = ApibaseClient(AB_BASE, AB_TOKEN)
mem    = Memory(client, table_id=AB_TABLE, agent='assistant')
oai    = OpenAI()

SYSTEM = """You are a helpful assistant with persistent memory.
When the user tells you something to remember, call remember_fact().
When you need to recall something, call recall_fact().
Memory keys must be short, lowercase, no underscores (e.g. "username", "userlang").
"""

tools = [
    {
        'type': 'function',
        'function': {
            'name': 'remember_fact',
            'description': 'Store a fact in persistent memory.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'key':   {'type': 'string', 'description': 'Short identifier'},
                    'value': {'type': 'string', 'description': 'The fact to store'},
                },
                'required': ['key', 'value'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'recall_fact',
            'description': 'Retrieve a fact from persistent memory by key.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'key': {'type': 'string'},
                },
                'required': ['key'],
            },
        },
    },
]

messages = [{'role': 'system', 'content': SYSTEM}]

def run_turn(user_input: str) -> str:
    messages.append({'role': 'user', 'content': user_input})

    while True:
        response = oai.chat.completions.create(
            model='gpt-4o-mini',
            messages=messages,
            tools=tools,
        )
        msg = response.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            return msg.content

        for call in msg.tool_calls:
            import json
            args = json.loads(call.function.arguments)

            if call.function.name == 'remember_fact':
                mem.remember(args['key'], args['value'])
                result = f"Stored: {args['key']} = {args['value']}"
            elif call.function.name == 'recall_fact':
                value = mem.recall(args['key'])
                result = value if value is not None else 'Not found.'
            else:
                result = 'Unknown tool.'

            messages.append({
                'role': 'tool',
                'tool_call_id': call.id,
                'content': result,
            })


if __name__ == '__main__':
    print(run_turn("My name is Pierre and I prefer concise answers."))
    print(run_turn("What's my name?"))
