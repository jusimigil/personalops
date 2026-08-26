import json
from pathlib import Path


# --------------------------------------------------
# Storage
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

MEMORY_FILE = BASE_DIR / "data" / "memory.json"


# --------------------------------------------------
# Storage helpers
# --------------------------------------------------

def load_memories():
    """Load persistent memories from disk."""

    if not MEMORY_FILE.exists():
        return []

    with open(MEMORY_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_memories(memories):
    """Save persistent memories to disk."""

    MEMORY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        MEMORY_FILE,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            memories,
            file,
            indent=2
        )


# --------------------------------------------------
# Memory operations
# --------------------------------------------------

def remember_memory(content, category="general"):
    """
    Store a new persistent memory.

    Args:
        content: Information to remember.
        category: Category of the memory.

    Returns:
        The newly created memory.
    """

    memories = load_memories()

    if memories:
        new_id = max(
            memory["id"]
            for memory in memories
        ) + 1
    else:
        new_id = 1

    memory = {
        "id": new_id,
        "content": content,
        "category": category,
    }

    memories.append(memory)

    save_memories(memories)

    return memory


def recall_memories():
    """
    Retrieve all persistent memories.

    Returns:
        A list of stored memories.
    """

    return load_memories()

def search_memories(query):
    """
    Search persistent memories using keyword matching
    with basic synonym expansion.
    """

    memories = load_memories()

    if not memories:
        return []

    # Basic synonym groups
    synonym_groups = {
        "study": {
            "study",
            "studying",
            "schoolwork",
            "school",
            "academic",
            "academics",
            "learning",
        },
        "work": {
            "work",
            "working",
            "schoolwork",
            "task",
            "tasks",
        },
        "time": {
            "time",
            "when",
            "schedule",
            "schedule",
            "period",
        },
        "preference": {
            "preference",
            "prefer",
            "preferred",
            "like",
            "likes",
        },
    }

    query_words = set(
        query.lower().split()
    )

    expanded_words = set(query_words)

    for word in query_words:
        for group in synonym_groups.values():
            if word in group:
                expanded_words.update(group)

    results = []

    for memory in memories:

        content = memory["content"].lower()

        score = 0

        for word in expanded_words:
            if word in content:
                score += 1

        if score > 0:
            results.append(
                {
                    **memory,
                    "relevance_score": score
                }
            )

    results.sort(
        key=lambda memory: memory["relevance_score"],
        reverse=True
    )

    return results

def forget_memory(memory_id):
    """
    Delete a persistent memory.

    Args:
        memory_id: ID of the memory to delete.

    Returns:
        The deleted memory.
    """

    memories = load_memories()

    for memory in memories:
        if memory["id"] == memory_id:

            memories.remove(memory)

            save_memories(memories)

            return memory

    return None

def update_memory(memory_id, content, category="general"):
    """
    Update an existing persistent memory.

    Args:
        memory_id: ID of the memory to update.
        content: New memory content.
        category: New memory category.

    Returns:
        The updated memory.
    """

    memories = load_memories()

    for memory in memories:

        if memory["id"] == memory_id:

            memory["content"] = content
            memory["category"] = category

            save_memories(memories)

            return memory

    return None