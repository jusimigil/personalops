import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from datetime import date

from tools.registry import (
    get_tool_function,
    get_gemini_tools,
    requires_approval,
)

from services.usage_tracker import (
    record_usage,
    budget_exceeded,
)
from services.approval import request_confirmation
from services.scheduling.service import SchedulingService
from tools.tasks import get_tasks


# --------------------------------------------------
# Environment
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"

load_dotenv(ENV_FILE)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError(
        f"GEMINI_API_KEY is not set. Expected .env at: {ENV_FILE}"
    )


# --------------------------------------------------
# Gemini client
# --------------------------------------------------

client = genai.Client(api_key=api_key)
scheduling_service = SchedulingService()

conversation_id = None

# --------------------------------------------------
# Tool definition
# --------------------------------------------------

get_tasks_tool = {
    "type": "function",
    "name": "get_tasks",
    "description": "Gets the user's current tasks.",
    "parameters": {
        "type": "object",
        "properties": {},
    },
}

create_task_tool = {
    "type": "function",
    "name": "create_task",
    "description": (
        "Creates a new task for the user. "
        "Use this directly when the user explicitly asks "
        "to add or create a task. "
        "Always provide a due_date. If the user gives a "
        "relative date such as 'tomorrow', convert it to "
        "YYYY-MM-DD before calling this function. "
        "Do not call get_tasks first unless the user asks "
        "about existing tasks or checking for duplicates."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "The title of the task."
            },
            "due_date": {
                "type": "string",
                "description": (
                    "The due date in YYYY-MM-DD format. "
                    "Convert relative dates such as 'tomorrow' "
                    "into an exact date."
                )       
            },
            "priority": {
                "type": "string",
                "enum": ["low", "medium", "high"],
                "description": "Task priority."
            }
        },
        "required": ["title", "due_date", "priority"]
    }
}

remember_memory_tool = {
    "type": "function",
    "name": "remember_memory",
    "description": (
        "Stores information as persistent user memory. "
        "Use this when the user explicitly asks PersonalOps "
        "to remember something for future conversations."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": (
                    "The information that should be remembered."
                )
            },
            "category": {
                "type": "string",
                "enum": [
                    "preference",
                    "personal",
                    "project",
                    "general"
                ],
                "description": "The category of the memory."
            }
        },
        "required": ["content", "category"]
    }
}

recall_memories_tool = {
    "type": "function",
    "name": "recall_memories",
    "description": (
        "Retrieves ALL of the user's persistent memories. "
        "Use this only when the user explicitly asks to see "
        "all memories or asks what PersonalOps remembers in general. "
        "For questions about a specific preference, fact, project, "
        "or topic, use search_memories instead."
    ),
    "parameters": {
        "type": "object",
        "properties": {}
    }
}

search_memories_tool = {
    "type": "function",
    "name": "search_memories",
    "description": (
        "Searches the user's persistent memories for information "
        "related to a specific topic, preference, fact, or project. "
        "Use this for specific questions about what the user "
        "has previously asked PersonalOps to remember. "
        "Prefer this tool over recall_memories unless the user "
        "explicitly asks for ALL saved memories."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "A concise set of keywords describing the "
                    "information being searched for."
                )
            }
        },
        "required": ["query"]
    }
}

forget_memory_tool = {
    "type": "function",
    "name": "forget_memory",
    "description": (
        "Deletes a specific persistent memory. "
        "Use this when the user explicitly asks "
        "PersonalOps to forget previously stored information."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "memory_id": {
                "type": "integer",
                "description": "The ID of the memory to delete."
            }
        },
        "required": ["memory_id"]
    }
}

update_memory_tool = {
    "type": "function",
    "name": "update_memory",
    "description": (
        "Updates an existing persistent memory. "
        "Use this when the user explicitly changes "
        "or corrects something they previously asked "
        "PersonalOps to remember."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "memory_id": {
                "type": "integer",
                "description": "The ID of the memory to update."
            },
            "content": {
                "type": "string",
                "description": "The updated information."
            },
            "category": {
                "type": "string",
                "enum": [
                    "preference",
                    "personal",
                    "project",
                    "general"
                ],
                "description": "The category of the memory."
            }
        },
        "required": [
            "memory_id",
            "content",
            "category"
        ]
    }
}

# --------------------------------------------------
# Agent
# --------------------------------------------------

def ask_agent(user_message: str) -> str:

    if budget_exceeded():
        return (
            "I've reached the configured API budget. "
            "Please check PersonalOps usage before continuing."
        )

    global conversation_id

    if conversation_id is None:
        interaction = client.interactions.create(
            model="gemini-3.7-flash",
            input=(
                f"Today's date is {date.today().isoformat()}.\n\n"
                f"User request: {user_message}"
            ),
            tools=get_gemini_tools(),
        )
    else:
        interaction = client.interactions.create(
            model="gemini-3.7-flash",
            previous_interaction_id=conversation_id,
            input=(
                f"User request: {user_message}"
            ),
            tools=get_gemini_tools(),
        )

    conversation_id = interaction.id

    # Track usage from this interaction
    if interaction.usage:

        usage = interaction.usage

        record_usage(
            input_tokens=usage.total_input_tokens,
            output_tokens=usage.total_output_tokens,
            thought_tokens=usage.total_thought_tokens,
            total_tokens=usage.total_tokens,
        )

    max_steps = 5

    for _ in range(max_steps):

        function_call = None

        for step in interaction.steps:

            if step.type == "function_call":
                function_call = step
                break

        # -----------------------------------------
        # No tool call = final answer
        # -----------------------------------------

        if function_call is None:
            return interaction.output_text

        function_name = function_call.name
        arguments = function_call.arguments or {}

        print(
            f"\n[Tool call] "
            f"{function_name}({arguments})"
        )

        function = get_tool_function(function_name)
        

        if function is None:
            raise ValueError(
                f"Unknown function requested: {function_name}"
            )

        # -----------------------------------------
        # Permission check
        # -----------------------------------------

        if requires_approval(function_name):

            if function_name == "create_task":

                title = arguments.get("title")
                due_date = arguments.get("due_date")
                priority = arguments.get(
                    "priority",
                    "medium"
                )

                description = (
                    f"Create task:\n"
                    f"  Title: {title}\n"
                    f"  Due: {due_date or 'No due date'}\n"
                    f"  Priority: {priority}"
                )

            elif function_name == "remember_memory":

                content = arguments.get("content")
                category = arguments.get(
                    "category",
                    "general"
                )

                description = (
                    f"Remember this information:\n"
                    f"  {content}\n"
                    f"Category: {category}"
                )

            elif function_name == "forget_memory":

                memory_id = arguments.get(
                    "memory_id"
                )

                description = (
                    f"Forget memory #{memory_id}."
                )

            elif function_name == "update_memory":

                memory_id = arguments.get(
                    "memory_id"
                )

                content = arguments.get(
                    "content"
                )

                category = arguments.get(
                    "category",
                    "general"
                )

                description = (
                    f"Update memory #{memory_id}:\n"
                    f"  New information: {content}\n"
                    f"  Category: {category}"
                )

            elif function_name == "schedule_plan":

                plan = arguments.get("plan", [])

                lines = [
                    "Schedule the following plan:"
                ]

                for item in plan:
                    task = item.get("task", {})
                    title = task.get(
                        "title",
                        "Untitled task"
                    )

                    lines.append(
                        f"  {title}: "
                        f"{item.get('start')} – "
                        f"{item.get('end')}"
                    )

                description = "\n".join(lines)

            elif function_name == "reschedule_event":

                event_id = arguments.get("event_id")
                new_start = arguments.get("new_start")
                new_end = arguments.get("new_end")

                event = None

                if event_id:
                    event = scheduling_service.calendar.get_event_by_id(
                        event_id=event_id,
                        calendar_name=arguments.get("calendar_name"),
                    )

                if event:
                    description = (
                        "Reschedule calendar event:\n\n"
                        f"  Title: {event['title']}\n"
                        f"  Current: {event['start']} – {event['end']}\n"
                        f"  New: {new_start} – {new_end}"
                    )
                else:
                    description = (
                        "Reschedule calendar event:\n\n"
                        f"  Event ID: {event_id}\n"
                        f"  New: {new_start} – {new_end}"
                    )

            elif function_name == "reschedule_task":

                task_id = arguments.get("task_id")
                new_start = arguments.get("new_start")
                new_end = arguments.get("new_end")

                task = next(
                    (
                        task
                        for task in get_tasks()
                        if task["id"] == task_id
                    ),
                    None,
                )

                if task:
                    description = (
                        "Reschedule task:\n\n"
                        f"  Task: {task['title']}\n"
                        f"  Current event: "
                        f"{task.get('calendar_event_id')}\n"
                        f"  New time: {new_start} – {new_end}"
                    )
                else:
                    description = (
                        f"Reschedule task {task_id} "
                        f"to {new_start} – {new_end}"
                    )

            elif function_name == "complete_task":

                task_id = arguments.get("task_id")

                task = next(
                    (
                        task
                        for task in get_tasks()
                        if task["id"] == task_id
                    ),
                    None,
                )

                if task:
                    description = (
                        "Complete task:\n\n"
                        f"  Task: {task['title']}\n"
                        f"  Task ID: {task_id}"
                    )
                else:
                    description = (
                        f"Complete task {task_id}"
                    )      

            else:
                description = (
                f"Execute tool: {function_name}"
            )

            approved = request_confirmation(
            description
            )

            if not approved:
                return (
                    f"The action '{function_name}' "
                    "was cancelled."
                )

        # -----------------------------------------
        # Execute tool
        # -----------------------------------------

        result = function(**arguments)

        print(f"[Tool result] {result}")

        # -----------------------------------------
        # Send result back to Gemini
        # -----------------------------------------

        interaction = client.interactions.create(
            model="gemini-3.7-flash",
            previous_interaction_id=interaction.id,
            input=[
                {
                    "type": "function_result",
                    "name": function_name,
                    "call_id": function_call.id,
                    "result": [
                        {
                            "type": "text",
                            "text": json.dumps(result),
                        }
                    ],
                }
            ],
            tools=get_gemini_tools()
        )

        conversation_id = interaction.id  

        # Track usage from subsequent interaction
        if interaction.usage:

            usage = interaction.usage

            record_usage(
                input_tokens=usage.total_input_tokens,
                output_tokens=usage.total_output_tokens,
                thought_tokens=usage.total_thought_tokens,
                total_tokens=usage.total_tokens,
            )

    return (
        "I stopped because the agent reached "
        "the maximum number of steps."
    )