from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import gradio as gr

load_dotenv(override=True)

# Initialize OpenAI client
openai_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"), 
    base_url=os.getenv("DEEPSEEK_OPEN_API_ENDPOINT")
)

# Global lists for todos
todos = []
completed = []

def get_todo_report() -> str:
    """Returns a formatted string of the current todo list."""
    result = ""
    for index, todo in enumerate(todos):
        if completed[index]:
            result += f"Todo #{index + 1}: <span style=\"color: green;\">~~{todo}~~</span>\n"
        else:
            result += f"Todo #{index + 1}: {todo}\n"
    return result

def create_todos(descriptions: list[str]) -> str:
    """Add new todos from a list of descriptions and return the full list."""
    global todos, completed
    todos.extend(descriptions)
    completed.extend([False] * len(descriptions))
    return get_todo_report()

def mark_complete(index: int, completion_notes: str) -> str:
    """Mark complete the todo at the given position (starting from 1) and return the full list."""
    global todos, completed
    if 1 <= index <= len(todos):
        completed[index - 1] = True
    else:
        return "No todo at this index."
    return get_todo_report()

# JSON schemas for the tools
create_todos_json = {
    "name": "create_todos",
    "description": "Add new todos from a list of descriptions and return the full list",
    "parameters": {
        "type": "object",
        "properties": {
            "descriptions": {
                'type': 'array',
                'items': {'type': 'string'},
                'title': 'Descriptions'
                }
            },
        "required": ["descriptions"],
        "additionalProperties": False
    }
}

mark_complete_json = {
    "name": "mark_complete",
    "description": "Mark complete the todo at the given position (starting from 1) and return the full list",
    "parameters": {
        'properties': {
            'index': {
                'description': 'The 1-based index of the todo to mark as complete',
                'title': 'Index',
                'type': 'integer'
                },
            'completion_notes': {
                'description': 'Notes about how you completed the todo in rich console markup',
                'title': 'Completion Notes',
                'type': 'string'
                }
            },
        'required': ['index', 'completion_notes'],
        'type': 'object',
        'additionalProperties': False
    }
}

tools = [
    {"type": "function", "function": create_todos_json},
    {"type": "function", "function": mark_complete_json}
]

def chat(message, history):
    """Handles chat interactions, using an LLM with tool-use capabilities to manage a todo list."""
    system_message_content = """
You are given a problem to solve, by using your todo tools to plan a list of steps, then carrying out each step in turn.
Now use the todo list tools, create a plan, carry out the steps, and reply with the solution.
If any quantity isn't provided in the question, then include a step to come up with a reasonable estimate.
Provide your solution in Rich console markup without code blocks.
Do not ask the user questions or clarification; respond only with the answer after using your tools.
"""

    messages = [
        {"role": "system", "content": system_message_content}
    ]

    for human_message, ai_message in history:
        messages.append({"role": "user", "content": human_message})
        messages.append({"role": "assistant", "content": ai_message})
    
    messages.append({"role": "user", "content": message})

    # Yield an initial message to show activity
    yield "Thinking..."

    done = False
    while not done:
        response = openai_client.chat.completions.create(
            model="deepseek-v4-flash", 
            messages=messages, 
            tools=tools,
        )
        finish_reason = response.choices[0].finish_reason
        
        if finish_reason == "tool_calls":
            llm_message = response.choices[0].message
            # Display agent's reasoning before tool calls
            if llm_message.content:
                yield f"🤔 Agent's reasoning: {llm_message.content}"

            tool_calls = llm_message.tool_calls
            
            # Display tool calls to the user
            tool_call_messages_for_display = []
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                tool_call_message = f"⚙️ Calling tool: **{tool_name}** with arguments: ```json\n{json.dumps(arguments, indent=2)}\n```"
                tool_call_messages_for_display.append(tool_call_message)
            yield "\n".join(tool_call_messages_for_display) # Yield intermediate tool call message

            results = []
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                tool = globals().get(tool_name)
                result = tool(**arguments) if tool else {}
                results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
                
                # Display tool result to the user
                if tool_name in ["create_todos", "mark_complete"]:
                    yield f"✅ Tool **{tool_name}** returned:\n{result}"
                else:
                    yield f"✅ Tool **{tool_name}** returned: ```json\n{json.dumps(result, indent=2)}\n```"

            messages.append(llm_message)
            messages.extend(results)
        else:
            done = True
            final_response = response.choices[0].message.content
            yield final_response  # Yield the final response
            todos.clear()  # Reset todos for the next task
            completed.clear()  # Reset completed status for the next task

if __name__ == "__main__":
    print("Starting Gradio ChatInterface...")
    gr.ChatInterface(chat).launch()
