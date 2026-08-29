from tools.tasks import (
    get_tasks,
    create_task,
    update_task,
    complete_task,
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
    plan_tasks,
    schedule_plan,
    recommend_reschedule,
    reschedule_event,
    find_calendar_event,
    reschedule_task,
    plan_day,
)

from tools.courses import (
    get_courses,
    create_course,
    update_course,
    delete_course,
    get_course_tasks,
    get_course_overview,
)

from tools.assignments import (
    get_assignments,
    create_assignment,
    update_assignment,
    get_assignment_tasks,
    get_assignment_progress,
    create_assignment_task,
    get_upcoming_assignments,
    get_academic_workload,
)


# ==================================================
# Python implementations
# ==================================================

TOOL_FUNCTIONS = {
    "get_tasks": get_tasks,
    "create_task": create_task,
    "complete_task": complete_task,

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
    "plan_tasks": plan_tasks,
    "schedule_plan": schedule_plan,
    "recommend_reschedule": recommend_reschedule,
    "reschedule_event": reschedule_event,
    "find_calendar_event": find_calendar_event,
    "reschedule_task": reschedule_task,
    "plan_day": plan_day,

    "get_courses": get_courses,
    "create_course": create_course,
    "update_course": update_course,
    "delete_course": delete_course,
    "get_course_tasks": get_course_tasks,
    "get_course_overview": get_course_overview,

    "get_assignments": get_assignments,
    "create_assignment": create_assignment,
    "update_assignment": update_assignment,
    "get_assignment_tasks": get_assignment_tasks,
    "get_assignment_progress": get_assignment_progress,
    "create_assignment_task": create_assignment_task,
    "get_upcoming_assignments": get_upcoming_assignments,
    "get_academic_workload": get_academic_workload,
    
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
            "Create a calendar event for a PersonalOps task. "
            "Prefer task_id when the task has already been identified. "
            "Use task_title only when a task ID is unavailable."
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
                "task_id": {
                    "type": "integer",
                    "description": (
                        "ID of the PersonalOps task to schedule. "
                        "Prefer this over task_title when available."
                    ),
                },
            },
            "required": [
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

    {
        "type": "function",
        "name": "plan_tasks",
        "description": (
            "Build a proposed schedule for the user's eligible "
            "tasks within a specified time range. The planner "
            "uses task urgency, estimated duration, calendar "
            "availability, user preferences, and breaks. "
            "Use this when the user asks to plan their day, "
            "evening, or a period of time."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "start_time": {
                    "type": "string",
                    "description": (
                        "Beginning of the planning range in "
                        "YYYY-MM-DD HH:MM:SS format."
                    ),
                },
                "end_time": {
                    "type": "string",
                    "description": (
                        "End of the planning range in "
                        "YYYY-MM-DD HH:MM:SS format."
                    ),
                },
                "calendar_name": {
                    "type": "string",
                    "description": (
                        "Optional Apple Calendar name. "
                        "If omitted, use all calendars."
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
                "break_minutes": {
                    "type": "integer",
                    "description": (
                        "Break between scheduled tasks, "
                        "in minutes. Defaults to 30."
                    ),
                },
            },
            "required": [
                "start_time",
                "end_time",
            ],
        },
    },

    {
        "type": "function",
        "name": "schedule_plan",
        "description": (
            "Create calendar events for the recommended tasks in an "
            "approved daily plan. Each plan item's task object MUST "
            "include the original PersonalOps task ID from plan_day. "
            "Preserve task IDs exactly; do not replace them with "
            "title-only task objects. Do not include already-scheduled "
            "tasks from scheduled_existing."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "plan": {
                    "type": "array",
                    "description": (
                        "The exact proposed schedule to add."
                    ),
                    "items": {
                        "type": "object",
                        "properties": {
                            "task": {
                                "type": "object",
                                "properties": {
                                    "id": {
                                        "type": "integer",
                                        "description": (
                                            "Original PersonalOps task ID returned by "
                                            "plan_day. Preserve this ID exactly."
                                        ),
                                    },
                                    "title": {
                                        "type": "string",
                                        "description": "Original PersonalOps task title.",
                                    },
                                },
                                "required": [
                                    "id",
                                    "title",
                                ],
                            },
                            "start": {
                                "type": "string",
                                "description": (
                                    "Start time in "
                                    "YYYY-MM-DD HH:MM:SS format."
                                ),
                            },
                            "end": {
                                "type": "string",
                                "description": (
                                    "End time in "
                                    "YYYY-MM-DD HH:MM:SS format."
                                ),
                            },
                        },
                        "required": [
                            "task",
                            "start",
                            "end",
                        ],
                    },
                },
                "calendar_name": {
                    "type": "string",
                    "description": (
                        "Calendar used by the plan. When the plan came from "
                        "plan_day, preserve the calendar_name returned by plan_day."
                    ),
                },
            },
            "required": ["plan"],
        },
    },

    {
        "type": "function",
        "name": "recommend_reschedule",
        "description": (
            "Find a better available time for an existing calendar "
            "event. Use this when the user wants to move or "
            "reschedule an event but has not yet specified the "
            "exact replacement time."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": (
                        "The Apple Calendar event UID."
                    ),
                },
                "search_start": {
                    "type": "string",
                    "description": (
                        "Beginning of the search range in "
                        "YYYY-MM-DD HH:MM:SS format."
                    ),
                },
                "search_end": {
                    "type": "string",
                    "description": (
                        "End of the search range in "
                        "YYYY-MM-DD HH:MM:SS format."
                    ),
                },
                "calendar_name": {
                    "type": "string",
                    "description": (
                        "Optional Apple Calendar name."
                    ),
                },
                "preference": {
                    "type": "string",
                    "description": (
                        "Optional scheduling preference to "
                        "use when evaluating replacement times."
                    ),
                },
            },
            "required": [
                "event_id",
                "search_start",
                "search_end",
            ],
        },
    },

    {
        "type": "function",
        "name": "reschedule_event",
        "description": (
            "Move an existing non-recurring calendar event "
            "to a new start and end time. Use only after the "
            "user has explicitly approved the new time."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": (
                        "The Apple Calendar event UID."
                    ),
                },
                "new_start": {
                    "type": "string",
                    "description": (
                        "New start time in "
                        "YYYY-MM-DD HH:MM:SS format."
                    ),
                },
                "new_end": {
                    "type": "string",
                    "description": (
                        "New end time in "
                        "YYYY-MM-DD HH:MM:SS format."
                    ),
                },
                "calendar_name": {
                    "type": "string",
                    "description": (
                        "Optional Apple Calendar name."
                    ),
                },
            },
            "required": [
                "event_id",
                "new_start",
                "new_end",
            ],
        },
    },

    {
        "type": "function",
        "name": "find_calendar_event",
        "description": (
            "Find calendar events by title. Search all calendars "
            "when calendar_name is not specified. Use this when "
            "the user refers to an existing event by its name."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "The event title to find.",
                },
                "start_time": {
                    "type": "string",
                    "description": (
                        "Optional start of the search range in "
                        "YYYY-MM-DD HH:MM:SS format."
                    ),
                },
                "end_time": {
                    "type": "string",
                    "description": (
                        "Optional end of the search range in "
                        "YYYY-MM-DD HH:MM:SS format."
                    ),
                },
                "calendar_name": {
                    "type": "string",
                    "description": "Optional calendar name.",
                },
            },
            "required": ["title"],
        },
    },

    {
        "type": "function",
        "name": "reschedule_task",
        "description": (
            "Move the calendar event linked to a PersonalOps task "
            "to a new time. Use this for task-related rescheduling "
            "when the task has a calendar event linked to it."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "integer",
                    "description": (
                        "ID of the PersonalOps task."
                    ),
                },
                "new_start": {
                    "type": "string",
                    "description": (
                        "New start time in "
                        "YYYY-MM-DD HH:MM:SS format."
                    ),
                },
                "new_end": {
                    "type": "string",
                    "description": (
                        "New end time in "
                        "YYYY-MM-DD HH:MM:SS format."
                    ),
                },
            },
            "required": [
                "task_id",
                "new_start",
                "new_end",
            ],
        },
    },

    {
        "type": "function",
        "name": "complete_task",
        "description": (
            "Mark a PersonalOps task as complete. "
            "Use this when the user explicitly says they "
            "finished or completed a task."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "integer",
                    "description": "ID of the task to complete.",
                },
            },
            "required": [
                "task_id",
            ],
        },
    },

    {
        "type": "function",
        "name": "plan_day",
        "description": (
            "Build a realistic plan for a specific day using tasks, "
            "deadlines, estimated durations, calendar availability, "
            "existing calendar events, scheduling preferences, "
            "breaks, and a daily workload limit. Use this for broad "
            "day-planning requests."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": (
                        "Date to plan in YYYY-MM-DD format."
                    ),
                },
                "earliest_hour": {
                    "type": "integer",
                    "description": (
                        "Earliest hour at which planned work may begin."
                    ),
                },
                "latest_hour": {
                    "type": "integer",
                    "description": (
                        "Latest hour at which planned work may end."
                    ),
                },
                "break_minutes": {
                    "type": "integer",
                    "description": (
                        "Preferred break duration between scheduled tasks."
                    ),
                },
                "calendar_name": {
                    "type": "string",
                    "description": (
                        "Optional calendar to use for availability."
                    ),
                },
                "max_work_minutes": {
                    "type": "integer",
                    "description": (
                        "Maximum amount of task work to schedule that day, "
                        "in minutes. Use this when the user specifies or "
                        "implies a daily workload limit."
                    ),
                },
            },
            "required": [
                "date",
            ],
        },
    },

    {
        "type": "function",
        "name": "get_courses",
        "description": (
            "Return the user's courses. Use this when the user asks "
            "about their courses, classes, or academic subjects."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },

    {
        "type": "function",
        "name": "create_course",
        "description": (
            "Create a new academic course for the user."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Course code.",
                },
                "name": {
                    "type": "string",
                    "description": "Course name.",
                },
                "term": {
                    "type": "string",
                    "description": "Academic term for the course.",
                },
            },
            "required": [
                "code",
                "name",
                "term",
            ],
        },
    },

    {
        "type": "function",
        "name": "get_course_tasks",
        "description": (
            "Return all tasks associated with a specific course."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "course_id": {
                    "type": "integer",
                    "description": "ID of the course.",
                },
            },
            "required": [
                "course_id",
            ],
        },
    },

    {
        "type": "function",
        "name": "get_assignments",
        "description": (
            "Return the user's academic assignments."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },

    {
        "type": "function",
        "name": "create_assignment",
        "description": (
            "Create a new academic assignment for an existing course."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "course_id": {
                    "type": "integer",
                    "description": "ID of the existing course.",
                },
                "title": {
                    "type": "string",
                    "description": "Assignment title.",
                },
                "due_date": {
                    "type": "string",
                    "description": (
                        "Optional due date in YYYY-MM-DD format."
                    ),
                },
                "estimated_minutes": {
                    "type": "integer",
                    "description": (
                        "Estimated time required to complete the assignment."
                    ),
                },
                "status": {
                    "type": "string",
                    "description": (
                        "Assignment status, such as incomplete "
                        "or complete."
                    ),
                },
            },
            "required": [
                "course_id",
                "title",
            ],
        },
    },

    {
        "type": "function",
        "name": "update_assignment",
        "description": (
            "Update an existing academic assignment."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "assignment_id": {
                    "type": "integer",
                    "description": "ID of the assignment.",
                },
                "course_id": {
                    "type": "integer",
                    "description": "ID of the existing course.",
                },
                "title": {
                    "type": "string",
                    "description": "Updated assignment title.",
                },
                "due_date": {
                    "type": "string",
                    "description": (
                        "Updated due date in YYYY-MM-DD format."
                    ),
                },
                "estimated_minutes": {
                    "type": "integer",
                    "description": (
                        "Updated estimated completion time."
                    ),
                },
                "status": {
                    "type": "string",
                    "description": "Updated assignment status.",
                },
            },
            "required": [
                "assignment_id",
            ],
        },
    },

    {
        "type": "function",
        "name": "get_assignment_tasks",
        "description": (
            "Return all tasks associated with a specific academic assignment."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "assignment_id": {
                    "type": "integer",
                    "description": "ID of the assignment.",
                },
            },
            "required": [
                "assignment_id",
            ],
        },
    },

    {
        "type": "function",
        "name": "get_assignment_progress",
        "description": (
            "Return progress and estimated remaining work for an "
            "academic assignment."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "assignment_id": {
                    "type": "integer",
                    "description": "ID of the assignment.",
                },
            },
            "required": [
                "assignment_id",
            ],
        },
    },

    {
        "type": "function",
        "name": "create_assignment_task",
        "description": (
            "Create an actionable task associated with an existing "
            "academic assignment. The task inherits the assignment's "
            "course and, by default, its due date."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "assignment_id": {
                    "type": "integer",
                    "description": "ID of the existing assignment.",
                },
                "title": {
                    "type": "string",
                    "description": (
                        "Title of the actionable task. "
                        "Defaults to the assignment title."
                    ),
                },
                "priority": {
                    "type": "string",
                    "description": (
                        "Priority of the work task: low, medium, or high."
                    ),
                },
                "estimated_minutes": {
                    "type": "integer",
                    "description": (
                        "Estimated time required for this specific task."
                    ),
                },
                "due_date": {
                    "type": "string",
                    "description": (
                        "Optional task-specific due date in YYYY-MM-DD format. "
                        "Defaults to the assignment due date."
                    ),
                },
            },
            "required": [
                "assignment_id",
            ],
        },
    },

    {
        "type": "function",
        "name": "get_upcoming_assignments",
        "description": (
            "Return academic assignments whose due dates fall within "
            "a specified date range, along with their associated tasks."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format.",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format.",
                },
            },
            "required": [
                "start_date",
                "end_date",
            ],
        },
    },

    {
        "type": "function",
        "name": "get_academic_workload",
        "description": (
            "Calculate academic workload for assignments due "
            "within a specified date range, including totals "
            "by assignment and course."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format.",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format.",
                },
            },
            "required": [
                "start_date",
                "end_date",
            ],
        },
    },

    {
        "type": "function",
        "name": "get_course_overview",
        "description": (
            "Return a complete overview of a course, including "
            "its assignments and associated tasks."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "course_id": {
                    "type": "integer",
                    "description": "ID of the course.",
                },
            },
            "required": [
                "course_id",
            ],
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
    "schedule_plan",
    "reschedule_event",
    "reschedule_task",
    "complete_task",
    "create_course",
    "create_assignment",
    "update_assignment",
    "create_assignment_task",
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