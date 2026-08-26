from tools.tasks import (
    get_tasks,
    create_task,
    update_task,
)

from tools.memory import (
    remember_memory,
    recall_memories,
    search_memories,
    forget_memory,
    update_memory,
)

from tools.calendar import (
    get_calendars,
    create_calendar_event,
    get_calendar_events,
    find_free_time,
    recommend_task_time,
    schedule_task,
)


# ==================================================
# Python implementations
# ==================================================

TOOL_FUNCTIONS = {
    "get_tasks": get_tasks,
    "create_task": create_task,

    "remember_memory": remember_memory,
    "recall_memories": recall_memories,
    "search_memories": search_memories,
    "forget_memory": forget_memory,
    "update_memory": update_memory,

    "get_calendars": get_calendars,
    "create_calendar_event": create_calendar_event,
    "get_calendar_events": get_calendar_events,
    "find_free_time": find_free_time,
    "recommend_task_time": recommend_task_time,
    "schedule_task": schedule_task,
    "update_task": update_task,
}


# ==================================================
# Gemini tool definitions
# ==================================================

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "name": "get_tasks",
        "description": (
            "Returns the user's current task list."
        ),
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },

    {
        "type": "function",
        "name": "create_task",
        "description": (
            "Creates a new task for the user. "
            "Use this when the user explicitly asks "
            "to add or create a task. "
            "Always provide a due_date when one is known. "
            "Convert relative dates such as tomorrow "
            "into YYYY-MM-DD."
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
                        "Convert relative dates such as tomorrow "
                        "into an exact date."
                    )
                },
                "priority": {
                    "type": "string",
                    "enum": [
                        "low",
                        "medium",
                        "high"
                    ],
                    "description": "Task priority."
                },
                "estimated_minutes": {
                    "type": "integer",
                    "description": (
                        "Optional estimated amount of time needed "
                        "to complete the task, in minutes."
                    )
                }
            },
            "required": [
                "title"
            ]
        }
    },

    {
        "type": "function",
        "name": "remember_memory",
        "description": (
            "Stores information as persistent user memory. "
            "Use this when the user explicitly asks "
            "PersonalOps to remember something."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string"
                },
                "category": {
                    "type": "string",
                    "enum": [
                        "preference",
                        "personal",
                        "project",
                        "general"
                    ]
                }
            },
            "required": [
                "content",
                "category"
            ]
        }
    },

    {
        "type": "function",
        "name": "recall_memories",
        "description": (
            "Retrieves ALL persistent memories. "
            "Use this only when the user explicitly asks "
            "to see all saved memories or asks what "
            "PersonalOps remembers in general. "
            "For specific topics, use search_memories."
        ),
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },

    {
        "type": "function",
        "name": "search_memories",
        "description": (
            "Searches persistent memories for information "
            "related to a specific topic, preference, fact, "
            "or project. Prefer this over recall_memories "
            "for specific questions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string"
                }
            },
            "required": [
                "query"
            ]
        }
    },

    {
        "type": "function",
        "name": "forget_memory",
        "description": (
            "Deletes a specific persistent memory when "
            "the user explicitly asks PersonalOps to "
            "forget it."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "memory_id": {
                    "type": "integer"
                }
            },
            "required": [
                "memory_id"
            ]
        }
    },

    {
        "type": "function",
        "name": "update_memory",
        "description": (
            "Updates an existing persistent memory when "
            "the user changes or corrects previously "
            "stored information."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "memory_id": {
                    "type": "integer"
                },
                "content": {
                    "type": "string"
                },
                "category": {
                    "type": "string",
                    "enum": [
                        "preference",
                        "personal",
                        "project",
                        "general"
                    ]
                }
            },
            "required": [
                "memory_id",
                "content",
                "category"
            ]
        }
    },

    {
        "type": "function",
        "name": "get_calendars",
        "description": (
            "Returns the user's available Apple Calendar "
            "calendar names."
        ),
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },

    {
        "type": "function",
        "name": "create_calendar_event",
        "description": (
            "Creates an event in the user's Apple Calendar. "
            "Use this when the user explicitly asks to "
            "schedule something. "
            "Use exact YYYY-MM-DD HH:MM:SS times."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string"
                },
                "start_time": {
                    "type": "string"
                },
                "end_time": {
                    "type": "string"
                },
                "calendar_name": {
                    "type": "string"
                },
                "location": {
                    "type": "string"
                },
                "description": {
                    "type": "string"
                }
            },
            "required": [
                "title",
                "start_time",
                "end_time"
            ]
        }
    },

    {
        "type": "function",
        "name": "get_calendar_events",
        "description": (
            "Returns events from the user's Apple Calendar "
            "within a specified time range. "
            "Use this when the user asks what is on their "
            "calendar or when checking their availability."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "start_time": {
                    "type": "string",
                    "description": (
                        "Start of the range in "
                        "YYYY-MM-DD HH:MM:SS format."
                    )
                },
                "end_time": {
                    "type": "string",
                    "description": (
                        "End of the range in "
                        "YYYY-MM-DD HH:MM:SS format."
                    )
                },
                "calendar_name": {
                    "type": "string",
                    "description": (
                        "Optional Apple Calendar name."
                    )
                }
            },
            "required": [
                "start_time",
                "end_time"
            ]
        }
    },

    {
        "type": "function",
        "name": "find_free_time",
        "description": (
            "Finds available time blocks in the user's "
            "Apple Calendar. Use this when the user asks "
            "when they are free, when they can study, "
            "or when they want to find a suitable time "
            "for an activity. The availability calculation "
            "is deterministic and accounts for calendar "
            "events, including recurring events."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "start_time": {
                    "type": "string",
                    "description": (
                        "Beginning of the search range in "
                        "YYYY-MM-DD HH:MM:SS format."
                    ),
                },
                "end_time": {
                    "type": "string",
                    "description": (
                        "End of the search range in "
                        "YYYY-MM-DD HH:MM:SS format."
                    ),
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": (
                        "Minimum continuous free time "
                        "required, in minutes."
                    ),
                },
                "calendar_name": {
                    "type": "string",
                    "description": (
                        "Optional Apple Calendar name. "
                        "If omitted, search all calendars."
                    ),
                },
                "earliest_hour": {
                    "type": "integer",
                    "description": (
                        "Earliest hour to consider, from 0 to 23. "
                        "Defaults to 7."
                    ),
                },
                "latest_hour": {
                    "type": "integer",
                    "description": (
                        "Latest hour to consider, from 0 to 23. "
                        "Defaults to 23."
                    ),
                },
            },
            "required": [
                "start_time",
                "end_time",
                "duration_minutes",
            ],
        },
    },

    {
        "type": "function",
        "name": "recommend_task_time",
        "description": (
            "Find the best available time to work on a task "
            "using the user's Apple Calendar and saved study "
            "preferences. Use this when the user asks when "
            "they should work on a task or study."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "task_title": {
                    "type": "string",
                    "description": (
                        "The title or identifying name of the task."
                    ),
                },
                "start_time": {
                    "type": "string",
                    "description": (
                        "Beginning of the search range in "
                        "YYYY-MM-DD HH:MM:SS format."
                    ),
                },
                "end_time": {
                    "type": "string",
                    "description": (
                        "End of the search range in "
                        "YYYY-MM-DD HH:MM:SS format."
                    ),
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": (
                        "Desired work/study session duration "
                        "in minutes."
                    ),
                },
                "calendar_name": {
                    "type": "string",
                    "description": (
                        "Optional Apple Calendar name. "
                        "If omitted, search all calendars."
                    ),
                },
                "earliest_hour": {
                    "type": "integer",
                    "description": (
                        "Earliest hour to consider, 0-23. "
                        "Defaults to 7."
                    ),
                },
                "latest_hour": {
                    "type": "integer",
                    "description": (
                        "Latest hour to consider, 0-23. "
                        "Defaults to 23."
                    ),
                },
            },
            "required": [
                "task_title",
                "start_time",
                "end_time",
            ],
        },
    },

    {
        "type": "function",
        "name": "schedule_task",
        "description": (
            "Create a calendar event for a task at a specific "
            "recommended time. Use this only when the user has "
            "explicitly approved scheduling the task."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "task_title": {
                    "type": "string",
                    "description": "Title of the task.",
                },
                "start_time": {
                    "type": "string",
                    "description": (
                        "Start time in YYYY-MM-DD HH:MM:SS format."
                    ),
                },
                "end_time": {
                    "type": "string",
                    "description": (
                        "End time in YYYY-MM-DD HH:MM:SS format."
                    ),
                },
                "calendar_name": {
                    "type": "string",
                    "description": (
                        "Optional Apple Calendar name."
                    ),
                },
                "location": {
                    "type": "string",
                    "description": "Optional event location.",
                },
                "description": {
                    "type": "string",
                    "description": "Optional event description.",
                },
            },
            "required": [
                "task_title",
                "start_time",
                "end_time",
            ],
        },
    },

    {
        "type": "function",
        "name": "update_task",
        "description": (
            "Update an existing task. Use this when the user "
            "provides new information about a task such as "
            "its duration, due date, priority, status, or title."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "integer",
                    "description": "ID of the task to update.",
                },
                "title": {
                    "type": "string",
                    "description": "New task title.",
                },
                "due_date": {
                    "type": "string",
                    "description": "New due date in YYYY-MM-DD format.",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "New task priority.",
                },
                "status": {
                    "type": "string",
                    "description": "New task status.",
                },
                "estimated_minutes": {
                    "type": "integer",
                    "description": (
                        "Estimated time required to complete "
                        "the task, in minutes."
                    ),
                },
            },
            "required": ["task_id"],
        },
    },
]


# ==================================================
# Permission policy
# ==================================================

TOOLS_REQUIRING_APPROVAL = {
    "create_task",
    "remember_memory",
    "forget_memory",
    "update_memory",
    "create_calendar_event",
}


# ==================================================
# Registry API
# ==================================================

def get_tool_function(name):
    """Return the Python implementation for a tool."""

    return TOOL_FUNCTIONS.get(name)


def get_gemini_tools():
    """Return all tool definitions for Gemini."""

    return TOOL_DEFINITIONS


def requires_approval(name):
    """Return whether a tool requires user approval."""

    return name in TOOLS_REQUIRING_APPROVAL